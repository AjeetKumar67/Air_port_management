from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator

class Airline(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, unique=True)  # IATA code like "AI", "6E"
    logo = models.ImageField(upload_to='airline_logos/', null=True, blank=True)
    description = models.TextField(blank=True)
    contact_email = models.EmailField()
    contact_phone = models.CharField(max_length=15)
    website = models.URLField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.code})"
    
    class Meta:
        ordering = ['name']

class Terminal(models.Model):
    name = models.CharField(max_length=50)  # Terminal 1, Terminal 2, etc.
    code = models.CharField(max_length=5, unique=True)  # T1, T2, etc.
    description = models.TextField(blank=True)
    capacity = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.code})"
    
    class Meta:
        ordering = ['code']

class Gate(models.Model):
    GATE_STATUS_CHOICES = [
        ('available', 'Available'),
        ('occupied', 'Occupied'),
        ('maintenance', 'Under Maintenance'),
        ('closed', 'Closed'),
    ]
    
    terminal = models.ForeignKey(Terminal, on_delete=models.CASCADE, related_name='gates')
    gate_number = models.CharField(max_length=10)  # A1, B2, C3, etc.
    gate_type = models.CharField(max_length=20, choices=[
        ('domestic', 'Domestic'),
        ('international', 'International'),
    ], default='domestic')
    capacity = models.PositiveIntegerField(default=200)
    status = models.CharField(max_length=20, choices=GATE_STATUS_CHOICES, default='available')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Gate {self.gate_number} - {self.terminal.name}"
    
    class Meta:
        unique_together = ['terminal', 'gate_number']
        ordering = ['terminal', 'gate_number']

class Aircraft(models.Model):
    airline = models.ForeignKey(Airline, on_delete=models.CASCADE, related_name='aircrafts')
    aircraft_type = models.CharField(max_length=50)  # Boeing 737, Airbus A320, etc.
    registration_number = models.CharField(max_length=20, unique=True)
    capacity = models.PositiveIntegerField()
    economy_seats = models.PositiveIntegerField()
    business_seats = models.PositiveIntegerField(default=0)
    first_class_seats = models.PositiveIntegerField(default=0)
    manufacturing_year = models.PositiveIntegerField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.aircraft_type} ({self.registration_number})"
    
    class Meta:
        ordering = ['airline', 'aircraft_type']

class Flight(models.Model):
    FLIGHT_STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('boarding', 'Boarding'),
        ('departed', 'Departed'),
        ('in_air', 'In Air'),
        ('landed', 'Landed'),
        ('delayed', 'Delayed'),
        ('cancelled', 'Cancelled'),
    ]
    
    flight_number = models.CharField(max_length=10)  # AI101, 6E234, etc.
    airline = models.ForeignKey(Airline, on_delete=models.CASCADE, related_name='flights')
    aircraft = models.ForeignKey(Aircraft, on_delete=models.SET_NULL, null=True, related_name='flights')
    
    # Route Information
    source = models.CharField(max_length=100)
    destination = models.CharField(max_length=100)
    source_code = models.CharField(max_length=5)  # DEL, BOM, etc.
    destination_code = models.CharField(max_length=5)
    
    # Time Information
    scheduled_departure = models.DateTimeField()
    scheduled_arrival = models.DateTimeField()
    actual_departure = models.DateTimeField(null=True, blank=True)
    actual_arrival = models.DateTimeField(null=True, blank=True)
    
    # Gate and Terminal Information
    departure_terminal = models.ForeignKey(Terminal, on_delete=models.SET_NULL, null=True, related_name='departure_flights')
    arrival_terminal = models.ForeignKey(Terminal, on_delete=models.SET_NULL, null=True, blank=True, related_name='arrival_flights')
    gate = models.ForeignKey(Gate, on_delete=models.SET_NULL, null=True, blank=True, related_name='flights')
    
    # Flight Details
    duration = models.DurationField()
    distance = models.PositiveIntegerField(help_text="Distance in kilometers")
    status = models.CharField(max_length=20, choices=FLIGHT_STATUS_CHOICES, default='scheduled')
    
    # Pricing
    economy_price = models.DecimalField(max_digits=10, decimal_places=2)
    business_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    first_class_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Admin fields
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.airline.code}{self.flight_number} ({self.source} → {self.destination})"
    
    @property
    def is_delayed(self):
        if self.actual_departure and self.scheduled_departure:
            return self.actual_departure > self.scheduled_departure
        return False
    
    @property
    def delay_duration(self):
        if self.is_delayed:
            return self.actual_departure - self.scheduled_departure
        return None
    
    @property
    def available_economy_seats(self):
        if self.aircraft:
            booked_economy = self.bookings.filter(seat_class='economy', status='confirmed').count()
            return self.aircraft.economy_seats - booked_economy
        return 0
    
    @property
    def available_business_seats(self):
        if self.aircraft:
            booked_business = self.bookings.filter(seat_class='business', status='confirmed').count()
            return self.aircraft.business_seats - booked_business
        return 0
    
    class Meta:
        ordering = ['scheduled_departure']
        unique_together = ['flight_number', 'airline', 'scheduled_departure']

class FlightSchedule(models.Model):
    DAYS_OF_WEEK = [
        ('monday', 'Monday'),
        ('tuesday', 'Tuesday'),
        ('wednesday', 'Wednesday'),
        ('thursday', 'Thursday'),
        ('friday', 'Friday'),
        ('saturday', 'Saturday'),
        ('sunday', 'Sunday'),
    ]
    
    flight = models.ForeignKey(Flight, on_delete=models.CASCADE, related_name='schedules')
    day_of_week = models.CharField(max_length=10, choices=DAYS_OF_WEEK)
    is_active = models.BooleanField(default=True)
    effective_from = models.DateField()
    effective_to = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.flight} - {self.get_day_of_week_display()}"
    
    class Meta:
        unique_together = ['flight', 'day_of_week']
