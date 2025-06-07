from django.contrib import admin
from .models import Airline, Terminal, Gate, Aircraft, Flight, FlightSchedule

@admin.register(Airline)
class AirlineAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'contact_email', 'contact_phone', 'created_at')
    search_fields = ('name', 'code', 'contact_email')
    list_filter = ('created_at',)
    readonly_fields = ('created_at', 'updated_at')

@admin.register(Terminal)
class TerminalAdmin(admin.ModelAdmin):
    list_display = ('name', 'capacity', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)

@admin.register(Gate)
class GateAdmin(admin.ModelAdmin):
    list_display = ('gate_number', 'terminal', 'gate_type', 'capacity', 'status', 'is_active')
    list_filter = ('terminal', 'gate_type', 'status', 'is_active')
    search_fields = ('gate_number',)

@admin.register(Aircraft)
class AircraftAdmin(admin.ModelAdmin):
    list_display = ('registration_number', 'airline', 'aircraft_type', 'capacity', 'manufacturing_year', 'is_active')
    list_filter = ('airline', 'aircraft_type', 'manufacturing_year', 'is_active')
    search_fields = ('registration_number', 'aircraft_type')

@admin.register(Flight)
class FlightAdmin(admin.ModelAdmin):
    list_display = ('flight_number', 'airline', 'source', 'destination', 'scheduled_departure', 'status')
    list_filter = ('airline', 'status', 'scheduled_departure', 'departure_terminal')
    search_fields = ('flight_number', 'source', 'destination')
    date_hierarchy = 'scheduled_departure'

# FlightSchedule admin temporarily disabled - need to check model fields
