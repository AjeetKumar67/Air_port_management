from django.contrib import admin
from .models import Booking, BoardingPass, Baggage, Seat, FlightStaff

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ['booking_reference', 'passenger_name', 'flight', 'status', 'total_amount', 'booking_date']
    list_filter = ['status', 'seat_class', 'payment_status', 'is_checked_in', 'booking_date']
    search_fields = ['booking_reference', 'passenger_name', 'passenger_email', 'passport_number']
    readonly_fields = ['booking_reference', 'created_at', 'updated_at']
    ordering = ['-booking_date']
    
    fieldsets = (
        ('Booking Information', {
            'fields': ('booking_reference', 'user', 'flight', 'status')
        }),
        ('Passenger Details', {
            'fields': ('passenger_name', 'passenger_email', 'passenger_phone', 'passport_number')
        }),
        ('Booking Details', {
            'fields': ('seat_class', 'seat_number', 'number_of_passengers', 'total_amount')
        }),
        ('Payment & Check-in', {
            'fields': ('payment_status', 'payment_date', 'is_checked_in', 'check_in_time', 'boarding_pass_issued')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

@admin.register(BoardingPass)
class BoardingPassAdmin(admin.ModelAdmin):
    list_display = ['boarding_pass_number', 'booking', 'seat_number', 'gate_number', 'boarding_time', 'is_used']
    list_filter = ['is_used', 'boarding_time', 'issued_at']
    search_fields = ['boarding_pass_number', 'booking__booking_reference', 'booking__passenger_name']
    readonly_fields = ['boarding_pass_number', 'qr_code', 'created_at', 'updated_at']
    ordering = ['-issued_at']

@admin.register(Baggage)
class BaggageAdmin(admin.ModelAdmin):
    list_display = ['baggage_tag', 'booking', 'baggage_type', 'weight', 'status', 'last_location']
    list_filter = ['baggage_type', 'status', 'created_at']
    search_fields = ['baggage_tag', 'booking__booking_reference', 'booking__passenger_name']
    readonly_fields = ['baggage_tag', 'created_at', 'updated_at']
    ordering = ['-created_at']

@admin.register(Seat)
class SeatAdmin(admin.ModelAdmin):
    list_display = ['aircraft', 'seat_number', 'seat_class', 'seat_type', 'is_available', 'price_modifier']
    list_filter = ['seat_class', 'seat_type', 'is_available', 'extra_legroom', 'exit_row']
    search_fields = ['seat_number', 'aircraft__registration_number']
    ordering = ['aircraft', 'row_number', 'seat_number']

@admin.register(FlightStaff)
class FlightStaffAdmin(admin.ModelAdmin):
    list_display = ['user', 'flight', 'role', 'shift_start', 'shift_end', 'is_active']
    list_filter = ['role', 'is_active', 'shift_start']
    search_fields = ['user__username', 'user__email', 'flight__flight_number']
    ordering = ['shift_start']
