from django.db import models
from django.conf import settings
from django.utils import timezone
import uuid
import qrcode
from io import BytesIO
from django.core.files import File
from PIL import Image

class Booking(models.Model):
    BOOKING_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    ]
    
    SEAT_CLASS_CHOICES = [
        ('economy', 'Economy'),
        ('business', 'Business'),
        ('first', 'First Class'),
    ]
    
    booking_reference = models.CharField(max_length=10, unique=True, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bookings')
    flight = models.ForeignKey('flights.Flight', on_delete=models.CASCADE, related_name='bookings')
    
    # Passenger Information
    passenger_name = models.CharField(max_length=100)
    passenger_email = models.EmailField()
    passenger_phone = models.CharField(max_length=15)
    passport_number = models.CharField(max_length=20, blank=True)
    
    # Booking Details
    seat_class = models.CharField(max_length=10, choices=SEAT_CLASS_CHOICES, default='economy')
    seat_number = models.CharField(max_length=5, blank=True)  # 12A, 15F, etc.
    number_of_passengers = models.PositiveIntegerField(default=1)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Status and Timestamps
    status = models.CharField(max_length=20, choices=BOOKING_STATUS_CHOICES, default='pending')
    booking_date = models.DateTimeField(auto_now_add=True)
    payment_status = models.BooleanField(default=False)
    payment_date = models.DateTimeField(null=True, blank=True)
    
    # Check-in Information
    is_checked_in = models.BooleanField(default=False)
    check_in_time = models.DateTimeField(null=True, blank=True)
    boarding_pass_issued = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        if not self.booking_reference:
            self.booking_reference = self.generate_booking_reference()
        super().save(*args, **kwargs)
    
    def generate_booking_reference(self):
        import random
        import string
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    
    def can_check_in(self):
        """Check if passenger can check in (2 hours before departure)"""
        if self.status != 'confirmed' or self.is_checked_in:
            return False
        
        time_until_departure = self.flight.scheduled_departure - timezone.now()
        return time_until_departure.total_seconds() <= 7200  # 2 hours in seconds
    
    def __str__(self):
        return f"{self.booking_reference} - {self.passenger_name} ({self.flight})"
    
    class Meta:
        ordering = ['-booking_date']

class BoardingPass(models.Model):
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='boarding_pass')
    boarding_pass_number = models.CharField(max_length=20, unique=True, editable=False)
    qr_code = models.ImageField(upload_to='boarding_passes/', blank=True)
    gate_number = models.CharField(max_length=10, blank=True)
    boarding_time = models.DateTimeField()
    seat_number = models.CharField(max_length=5)
    sequence_number = models.PositiveIntegerField()
    issued_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        if not self.boarding_pass_number:
            self.boarding_pass_number = self.generate_boarding_pass_number()
        
        if not self.qr_code:
            self.generate_qr_code()
        
        super().save(*args, **kwargs)
    
    def generate_boarding_pass_number(self):
        import random
        import string
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
    
    def generate_qr_code(self):
        qr_data = f"{self.booking.booking_reference}|{self.booking.passenger_name}|{self.booking.flight.flight_number}|{self.seat_number}"
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        canvas = Image.new('RGB', (300, 300), 'white')
        canvas.paste(img)
        
        fname = f'boarding_pass_{self.booking.booking_reference}.png'
        buffer = BytesIO()
        canvas.save(buffer, 'PNG')
        self.qr_code.save(fname, File(buffer), save=False)
        canvas.close()
    
    def __str__(self):
        return f"Boarding Pass {self.boarding_pass_number} - {self.booking.passenger_name}"
    
    class Meta:
        ordering = ['-issued_at']

class Baggage(models.Model):
    BAGGAGE_STATUS_CHOICES = [
        ('checked_in', 'Checked In'),
        ('in_transit', 'In Transit'),
        ('loaded', 'Loaded on Aircraft'),
        ('in_flight', 'In Flight'),
        ('arrived', 'Arrived'),
        ('delivered', 'Delivered'),
        ('lost', 'Lost'),
        ('damaged', 'Damaged'),
    ]
    
    BAGGAGE_TYPE_CHOICES = [
        ('carry_on', 'Carry On'),
        ('checked', 'Checked'),
        ('special', 'Special'),
    ]
    
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='baggages')
    baggage_tag = models.CharField(max_length=20, unique=True, editable=False)
    baggage_type = models.CharField(max_length=10, choices=BAGGAGE_TYPE_CHOICES, default='checked')
    weight = models.DecimalField(max_digits=5, decimal_places=2)  # in kg
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=BAGGAGE_STATUS_CHOICES, default='checked_in')
    last_location = models.CharField(max_length=100, blank=True)
    special_handling = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        if not self.baggage_tag:
            self.baggage_tag = self.generate_baggage_tag()
        super().save(*args, **kwargs)
    
    def generate_baggage_tag(self):
        import random
        import string
        return 'BAG' + ''.join(random.choices(string.digits, k=7))
    
    def __str__(self):
        return f"{self.baggage_tag} - {self.booking.passenger_name} ({self.weight}kg)"
    
    class Meta:
        ordering = ['-created_at']

class Seat(models.Model):
    SEAT_TYPE_CHOICES = [
        ('window', 'Window'),
        ('middle', 'Middle'),
        ('aisle', 'Aisle'),
    ]
    
    SEAT_CLASS_CHOICES = [
        ('economy', 'Economy'),
        ('business', 'Business'),
        ('first', 'First Class'),
    ]
    
    aircraft = models.ForeignKey('flights.Aircraft', on_delete=models.CASCADE, related_name='seats')
    seat_number = models.CharField(max_length=5)  # 12A, 15F, etc.
    seat_class = models.CharField(max_length=10, choices=SEAT_CLASS_CHOICES, default='economy')
    seat_type = models.CharField(max_length=10, choices=SEAT_TYPE_CHOICES, default='middle')
    row_number = models.PositiveIntegerField()
    is_available = models.BooleanField(default=True)
    extra_legroom = models.BooleanField(default=False)
    exit_row = models.BooleanField(default=False)
    price_modifier = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)  # Additional cost
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.aircraft} - Seat {self.seat_number} ({self.get_seat_class_display()})"
    
    class Meta:
        unique_together = ['aircraft', 'seat_number']
        ordering = ['aircraft', 'row_number', 'seat_number']

class FlightStaff(models.Model):
    STAFF_ROLE_CHOICES = [
        ('pilot', 'Pilot'),
        ('co_pilot', 'Co-Pilot'),
        ('flight_attendant', 'Flight Attendant'),
        ('ground_crew', 'Ground Crew'),
        ('check_in_staff', 'Check-in Staff'),
        ('security', 'Security'),
        ('maintenance', 'Maintenance'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='flight_assignments')
    flight = models.ForeignKey('flights.Flight', on_delete=models.CASCADE, related_name='staff_assignments')
    role = models.CharField(max_length=20, choices=STAFF_ROLE_CHOICES)
    shift_start = models.DateTimeField()
    shift_end = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.get_role_display()} ({self.flight})"
    
    class Meta:
        ordering = ['shift_start']
        unique_together = ['user', 'flight', 'role']
