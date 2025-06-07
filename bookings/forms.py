from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Booking, Baggage, Seat
from flights.models import Flight

class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = [
            'flight', 'seat_class', 'number_of_passengers', 
            'passenger_name', 'passenger_email', 'passenger_phone',
            'passport_number'
        ]
        widgets = {
            'flight': forms.Select(attrs={
                'class': 'form-control',
                'required': True
            }),
            'seat_class': forms.Select(attrs={
                'class': 'form-control',
                'required': True
            }),
            'number_of_passengers': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '9',
                'required': True
            }),
            'passenger_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Full Name',
                'required': True
            }),
            'passenger_email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Email Address',
                'required': True
            }),
            'passenger_phone': forms.TextInput(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter passenger phone numbers (one per line)'
            }),
            'special_requests': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Any special requests or dietary requirements...'
            }),
        }
        labels = {
            'flight': 'Select Flight',
            'seat_class': 'Class',
            'passenger_count': 'Number of Passengers',
            'passenger_names': 'Passenger Names',
            'passenger_emails': 'Passenger Emails',
            'passenger_phones': 'Passenger Phone Numbers',
            'special_requests': 'Special Requests',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter flights to only show future, active flights
        self.fields['flight'].queryset = Flight.objects.filter(
            scheduled_departure__gte=timezone.now(),
            is_active=True
        ).select_related('airline').order_by('scheduled_departure')
        
        # Make special requests optional
        self.fields['special_requests'].required = False
    
    def clean_passenger_count(self):
        count = self.cleaned_data.get('passenger_count')
        if count and (count < 1 or count > 9):
            raise ValidationError("Passenger count must be between 1 and 9.")
        return count
    
    def clean_passenger_names(self):
        names = self.cleaned_data.get('passenger_names', '').strip()
        passenger_count = self.cleaned_data.get('passenger_count', 0)
        
        if names:
            name_list = [name.strip() for name in names.split('\n') if name.strip()]
            if len(name_list) != passenger_count:
                raise ValidationError(f"Please provide exactly {passenger_count} passenger name(s).")
            
            # Validate each name
            for name in name_list:
                if len(name) < 2:
                    raise ValidationError("Each passenger name must be at least 2 characters long.")
        
        return names
    
    def clean_passenger_emails(self):
        emails = self.cleaned_data.get('passenger_emails', '').strip()
        passenger_count = self.cleaned_data.get('passenger_count', 0)
        
        if emails:
            email_list = [email.strip() for email in emails.split('\n') if email.strip()]
            if len(email_list) != passenger_count:
                raise ValidationError(f"Please provide exactly {passenger_count} email address(es).")
            
            # Validate each email
            for email in email_list:
                try:
                    forms.EmailField().clean(email)
                except ValidationError:
                    raise ValidationError(f"'{email}' is not a valid email address.")
        
        return emails
    
    def clean_passenger_phones(self):
        phones = self.cleaned_data.get('passenger_phones', '').strip()
        passenger_count = self.cleaned_data.get('passenger_count', 0)
        
        if phones:
            phone_list = [phone.strip() for phone in phones.split('\n') if phone.strip()]
            if len(phone_list) != passenger_count:
                raise ValidationError(f"Please provide exactly {passenger_count} phone number(s).")
        
        return phones
    
    def clean(self):
        cleaned_data = super().clean()
        flight = cleaned_data.get('flight')
        seat_class = cleaned_data.get('seat_class')
        passenger_count = cleaned_data.get('passenger_count', 0)
        
        if flight and seat_class and passenger_count:
            # Check seat availability
            if seat_class == 'economy':
                available = flight.available_economy_seats
            elif seat_class == 'business':
                available = flight.available_business_seats
            else:  # first_class
                available = getattr(flight, 'available_first_class_seats', 0)
            
            if available < passenger_count:
                raise ValidationError(f"Only {available} {seat_class} seats available on this flight.")
        
        return cleaned_data

class SeatSelectionForm(forms.Form):
    seats = forms.CharField(
        widget=forms.HiddenInput(),
        help_text="Selected seat numbers (comma-separated)"
    )
    
    def __init__(self, *args, **kwargs):
        self.booking = kwargs.pop('booking', None)
        super().__init__(*args, **kwargs)
    
    def clean_seats(self):
        seats_data = self.cleaned_data.get('seats', '')
        if not seats_data:
            raise ValidationError("Please select seats.")
        
        seat_list = [seat.strip() for seat in seats_data.split(',') if seat.strip()]
        
        if self.booking and len(seat_list) != self.booking.passenger_count:
            raise ValidationError(f"Please select exactly {self.booking.passenger_count} seat(s).")
        
        # Check if seats are available
        if self.booking:
            occupied_seats = Seat.objects.filter(
                booking__flight=self.booking.flight,
                booking__status='confirmed'
            ).exclude(booking=self.booking).values_list('seat_number', flat=True)
            
            for seat in seat_list:
                if seat in occupied_seats:
                    raise ValidationError(f"Seat {seat} is no longer available.")
        
        return seat_list

class BaggageForm(forms.ModelForm):
    class Meta:
        model = Baggage
        fields = ['baggage_type', 'weight', 'description', 'special_handling']
        widgets = {
            'baggage_type': forms.Select(attrs={
                'class': 'form-control',
                'required': True
            }),
            'weight': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.1',
                'min': '0',
                'placeholder': 'Weight in kg'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Baggage description (optional)'
            }),
            'special_handling': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Special handling instructions (optional)'
            }),
        }
        labels = {
            'baggage_type': 'Baggage Type',
            'weight': 'Weight (kg)',
            'description': 'Description',
            'special_handling': 'Special Handling',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['description'].required = False
        self.fields['special_handling'].required = False
    
    def clean_weight(self):
        weight = self.cleaned_data.get('weight')
        if weight is not None:
            if weight <= 0:
                raise ValidationError("Weight must be greater than 0.")
            if weight > 50:  # Maximum weight limit
                raise ValidationError("Maximum weight allowed is 50kg per bag.")
        return weight

class FlightSearchForm(forms.Form):
    origin = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Departure city or airport code',
            'required': True
        })
    )
    destination = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Arrival city or airport code',
            'required': True
        })
    )
    departure_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
            'required': True
        })
    )
    return_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    passengers = forms.IntegerField(
        initial=1,
        min_value=1,
        max_value=9,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '1',
            'max': '9'
        })
    )
    seat_class = forms.ChoiceField(
        choices=[
            ('economy', 'Economy'),
            ('business', 'Business'),
            ('first_class', 'First Class'),
        ],
        initial='economy',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    def clean_departure_date(self):
        date = self.cleaned_data.get('departure_date')
        if date and date < timezone.now().date():
            raise ValidationError("Departure date cannot be in the past.")
        return date
    
    def clean_return_date(self):
        return_date = self.cleaned_data.get('return_date')
        departure_date = self.cleaned_data.get('departure_date')
        
        if return_date and departure_date and return_date <= departure_date:
            raise ValidationError("Return date must be after departure date.")
        
        return return_date

class PassengerDetailsForm(forms.Form):
    """Dynamic form for passenger details"""
    def __init__(self, *args, **kwargs):
        passenger_count = kwargs.pop('passenger_count', 1)
        super().__init__(*args, **kwargs)
        
        for i in range(passenger_count):
            self.fields[f'passenger_{i}_name'] = forms.CharField(
                label=f'Passenger {i+1} Name',
                max_length=100,
                widget=forms.TextInput(attrs={
                    'class': 'form-control',
                    'placeholder': 'Full name as on ID'
                })
            )
            self.fields[f'passenger_{i}_email'] = forms.EmailField(
                label=f'Passenger {i+1} Email',
                widget=forms.EmailInput(attrs={
                    'class': 'form-control',
                    'placeholder': 'email@example.com'
                })
            )
            self.fields[f'passenger_{i}_phone'] = forms.CharField(
                label=f'Passenger {i+1} Phone',
                max_length=15,
                widget=forms.TextInput(attrs={
                    'class': 'form-control',
                    'placeholder': '+1234567890'
                })
            )