from django import forms
from .models import Flight, Airline, Gate, Terminal, Aircraft

class FlightSearchForm(forms.Form):
    source = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'From'})
    )
    destination = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'To'})
    )
    departure_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    airline = forms.ModelChoiceField(
        queryset=Airline.objects.all(),
        required=False,
        empty_label="All Airlines",
        widget=forms.Select(attrs={'class': 'form-select'})
    )

class FlightForm(forms.ModelForm):
    class Meta:
        model = Flight
        fields = [
            'flight_number', 'airline', 'aircraft', 'source', 'destination',
            'source_code', 'destination_code', 'scheduled_departure', 'scheduled_arrival', 
            'departure_terminal', 'gate', 'duration', 'distance', 'economy_price', 
            'business_price', 'first_class_price', 'status'
        ]
        widgets = {
            'flight_number': forms.TextInput(attrs={'class': 'form-control'}),
            'airline': forms.Select(attrs={'class': 'form-select'}),
            'aircraft': forms.Select(attrs={'class': 'form-select'}),
            'source': forms.TextInput(attrs={'class': 'form-control'}),
            'destination': forms.TextInput(attrs={'class': 'form-control'}),
            'source_code': forms.TextInput(attrs={'class': 'form-control', 'maxlength': '5'}),
            'destination_code': forms.TextInput(attrs={'class': 'form-control', 'maxlength': '5'}),
            'scheduled_departure': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'scheduled_arrival': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'departure_terminal': forms.Select(attrs={'class': 'form-select'}),
            'gate': forms.Select(attrs={'class': 'form-select'}),
            'duration': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'HH:MM:SS'}),
            'distance': forms.NumberInput(attrs={'class': 'form-control'}),
            'economy_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'business_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'first_class_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        scheduled_departure = cleaned_data.get('scheduled_departure')
        scheduled_arrival = cleaned_data.get('scheduled_arrival')
        
        if scheduled_departure and scheduled_arrival:
            if scheduled_arrival <= scheduled_departure:
                raise forms.ValidationError("Arrival time must be after departure time.")
        
        return cleaned_data

class AirlineForm(forms.ModelForm):
    class Meta:
        model = Airline
        fields = ['name', 'code', 'description', 'contact_email', 'contact_phone', 'website', 'logo']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'code': forms.TextInput(attrs={'class': 'form-control', 'maxlength': '10'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'contact_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'contact_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'website': forms.URLInput(attrs={'class': 'form-control'}),
            'logo': forms.FileInput(attrs={'class': 'form-control'}),
        }

class GateForm(forms.ModelForm):
    class Meta:
        model = Gate
        fields = ['gate_number', 'terminal', 'gate_type', 'capacity', 'status', 'is_active']
        widgets = {
            'gate_number': forms.TextInput(attrs={'class': 'form-control'}),
            'terminal': forms.Select(attrs={'class': 'form-select'}),
            'gate_type': forms.Select(attrs={'class': 'form-select'}),
            'capacity': forms.NumberInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class AircraftForm(forms.ModelForm):
    class Meta:
        model = Aircraft
        fields = ['registration_number', 'aircraft_type', 'airline', 'capacity', 'economy_seats', 'business_seats', 'first_class_seats', 'manufacturing_year', 'is_active']
        widgets = {
            'registration_number': forms.TextInput(attrs={'class': 'form-control'}),
            'aircraft_type': forms.TextInput(attrs={'class': 'form-control'}),
            'airline': forms.Select(attrs={'class': 'form-select'}),
            'capacity': forms.NumberInput(attrs={'class': 'form-control'}),
            'economy_seats': forms.NumberInput(attrs={'class': 'form-control'}),
            'business_seats': forms.NumberInput(attrs={'class': 'form-control'}),
            'first_class_seats': forms.NumberInput(attrs={'class': 'form-control'}),
            'manufacturing_year': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }