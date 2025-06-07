from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.utils import timezone
from .models import Flight, Airline, Gate, Terminal, Aircraft
from .forms import FlightForm, AirlineForm, GateForm, FlightSearchForm, AircraftForm
from datetime import datetime, timedelta

def flight_list_view(request):
    search_form = FlightSearchForm(request.GET or None)
    flights = Flight.objects.select_related('airline', 'aircraft', 'gate', 'departure_terminal', 'arrival_terminal').all()
    
    if search_form.is_valid():
        if search_form.cleaned_data['source']:
            flights = flights.filter(source__icontains=search_form.cleaned_data['source'])
        if search_form.cleaned_data['destination']:
            flights = flights.filter(destination__icontains=search_form.cleaned_data['destination'])
        if search_form.cleaned_data['departure_date']:
            flights = flights.filter(scheduled_departure__date=search_form.cleaned_data['departure_date'])
        if search_form.cleaned_data['airline']:
            flights = flights.filter(airline=search_form.cleaned_data['airline'])
    
    flights = flights.order_by('scheduled_departure')
    
    paginator = Paginator(flights, 10)
    page_number = request.GET.get('page')
    flights_page = paginator.get_page(page_number)
    
    context = {
        'flights': flights_page,
        'search_form': search_form,
        'title': 'Available Flights'
    }
    
    return render(request, 'flights/flight_list.html', context)

def flight_detail_view(request, flight_id):
    flight = get_object_or_404(Flight, id=flight_id)
    
    # Get available seats for this flight
    total_seats = flight.aircraft.seats.count() if flight.aircraft else 0
    booked_seats = flight.bookings.filter(status='confirmed').count()
    available_seats = total_seats - booked_seats
    
    context = {
        'flight': flight,
        'total_seats': total_seats,
        'booked_seats': booked_seats,
        'available_seats': available_seats,
        'can_book': available_seats > 0 and flight.status == 'scheduled',
    }
    
    return render(request, 'flights/flight_detail.html', context)

def flight_status_view(request):
    search_query = request.GET.get('search', '')
    
    flights = Flight.objects.select_related('airline', 'gate', 'departure_terminal', 'arrival_terminal').all()
    
    if search_query:
        flights = flights.filter(
            Q(flight_number__icontains=search_query) |
            Q(source__icontains=search_query) |
            Q(destination__icontains=search_query) |
            Q(airline__name__icontains=search_query)
        )
    
    # Group flights by status
    today = timezone.now().date()
    flights_today = flights.filter(scheduled_departure__date=today).order_by('scheduled_departure')
    
    context = {
        'flights': flights_today,
        'search_query': search_query,
        'current_time': timezone.now(),
    }
    
    return render(request, 'flights/flight_status.html', context)

@login_required
def flight_management_view(request):
    if request.user.role not in ['admin', 'staff', 'airline_staff']:
        messages.error(request, 'Access denied.')
        return redirect('dashboard:home')
    
    flights = Flight.objects.select_related('airline', 'aircraft', 'gate', 'departure_terminal', 'arrival_terminal').all()
    
    if request.user.role == 'airline_staff':
        # Airline staff can only see their airline's flights
        flights = flights.filter(airline__name=request.user.airline)
    
    flights = flights.order_by('-scheduled_departure')
    
    paginator = Paginator(flights, 15)
    page_number = request.GET.get('page')
    flights_page = paginator.get_page(page_number)
    
    context = {
        'flights': flights_page,
        'title': 'Flight Management'
    }
    
    return render(request, 'flights/flight_management.html', context)

@login_required
def flight_create_view(request):
    if request.user.role not in ['admin', 'staff', 'airline_staff']:
        messages.error(request, 'Access denied.')
        return redirect('dashboard:home')
    
    if request.method == 'POST':
        form = FlightForm(request.POST)
        if form.is_valid():
            flight = form.save()
            messages.success(request, f'Flight {flight.flight_number} created successfully!')
            return redirect('flights:flight_management')
    else:
        form = FlightForm()
        if request.user.role == 'airline_staff':
            # Limit airline choices for airline staff
            form.fields['airline'].queryset = Airline.objects.filter(name=request.user.airline)
    
    return render(request, 'flights/flight_form.html', {'form': form, 'title': 'Create Flight'})

@login_required
def flight_edit_view(request, flight_id):
    if request.user.role not in ['admin', 'staff', 'airline_staff']:
        messages.error(request, 'Access denied.')
        return redirect('dashboard:home')
    
    flight = get_object_or_404(Flight, id=flight_id)
    
    if request.user.role == 'airline_staff' and flight.airline.name != request.user.airline:
        messages.error(request, 'You can only edit flights for your airline.')
        return redirect('flights:flight_management')
    
    if request.method == 'POST':
        form = FlightForm(request.POST, instance=flight)
        if form.is_valid():
            form.save()
            messages.success(request, f'Flight {flight.flight_number} updated successfully!')
            return redirect('flights:flight_management')
    else:
        form = FlightForm(instance=flight)
    
    return render(request, 'flights/flight_form.html', {'form': form, 'flight': flight, 'title': 'Edit Flight'})

@login_required
def flight_delete_view(request, flight_id):
    if request.user.role not in ['admin', 'staff']:
        return JsonResponse({'success': False, 'message': 'Access denied'})
    
    flight = get_object_or_404(Flight, id=flight_id)
    
    if request.method == 'POST':
        flight_number = flight.flight_number
        flight.delete()
        return JsonResponse({'success': True, 'message': f'Flight {flight_number} deleted successfully'})
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})

def airline_list_view(request):
    airlines = Airline.objects.annotate(
        flight_count=Count('flights'),
        active_flights=Count('flights', filter=Q(flights__status='scheduled'))
    ).order_by('name')
    
    context = {
        'airlines': airlines,
        'title': 'Airlines'
    }
    
    return render(request, 'flights/airline_list.html', context)

def airline_detail_view(request, airline_id):
    airline = get_object_or_404(Airline, id=airline_id)
    flights = airline.flights.all().order_by('-scheduled_departure')[:10]
    
    context = {
        'airline': airline,
        'flights': flights,
    }
    
    return render(request, 'flights/airline_detail.html', context)

@login_required
def gate_list_view(request):
    if request.user.role not in ['admin', 'staff']:
        messages.error(request, 'Access denied.')
        return redirect('dashboard:home')
    
    gates = Gate.objects.select_related('terminal').annotate(
        current_flight=Count('flights', filter=Q(
            flights__scheduled_departure__lte=timezone.now(),
            flights__scheduled_arrival__gte=timezone.now()
        ))
    ).order_by('terminal', 'gate_number')
    
    context = {
        'gates': gates,
        'title': 'Gate Management'
    }
    
    return render(request, 'flights/gate_list.html', context)

@login_required
def update_flight_status(request, flight_id):
    if request.user.role not in ['admin', 'staff', 'airline_staff']:
        return JsonResponse({'success': False, 'message': 'Access denied'})
    
    flight = get_object_or_404(Flight, id=flight_id)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(Flight.STATUS_CHOICES):
            flight.status = new_status
            
            # Update actual times based on status
            if new_status == 'boarding':
                flight.actual_departure = timezone.now() + timedelta(minutes=30)
            elif new_status == 'landed':
                flight.actual_arrival = timezone.now()
            
            flight.save()
            
            return JsonResponse({
                'success': True, 
                'message': f'Flight status updated to {flight.get_status_display()}'
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})

def get_flight_status_api(request):
    """API endpoint for real-time flight status updates"""
    flights = Flight.objects.filter(
        scheduled_departure__date=timezone.now().date()
    ).values(
        'id', 'flight_number', 'status', 'scheduled_departure', 
        'actual_departure', 'gate__gate_number'
    )
    
    flight_data = []
    for flight in flights:
        flight_data.append({
            'id': flight['id'],
            'flight_number': flight['flight_number'],
            'status': flight['status'],
            'scheduled_departure': flight['scheduled_departure'].isoformat() if flight['scheduled_departure'] else None,
            'actual_departure': flight['actual_departure'].isoformat() if flight['actual_departure'] else None,
            'gate': flight['gate__gate_number'],
        })
    
    return JsonResponse({'flights': flight_data})

# Missing views that are referenced in URLs

def flight_search_view(request):
    """Search flights with advanced filters"""
    search_form = FlightSearchForm(request.GET or None)
    flights = Flight.objects.select_related('airline', 'aircraft', 'gate', 'departure_terminal').all()
    
    if search_form.is_valid():
        if search_form.cleaned_data['source']:
            flights = flights.filter(source__icontains=search_form.cleaned_data['source'])
        if search_form.cleaned_data['destination']:
            flights = flights.filter(destination__icontains=search_form.cleaned_data['destination'])
        if search_form.cleaned_data['departure_date']:
            flights = flights.filter(scheduled_departure__date=search_form.cleaned_data['departure_date'])
        if search_form.cleaned_data['airline']:
            flights = flights.filter(airline=search_form.cleaned_data['airline'])
    
    flights = flights.order_by('scheduled_departure')
    
    context = {
        'flights': flights,
        'search_form': search_form,
        'title': 'Search Flights'
    }
    
    return render(request, 'flights/flight_search.html', context)

@login_required
def create_flight_view(request):
    """Create a new flight (admin only)"""
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to create flights.')
        return redirect('flights:flight_list')
    
    if request.method == 'POST':
        form = FlightForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Flight created successfully.')
            return redirect('flights:flight_list')
    else:
        form = FlightForm()
    
    context = {
        'form': form,
        'title': 'Create Flight'
    }
    
    return render(request, 'flights/flight_form.html', context)

@login_required
def edit_flight_view(request, flight_id):
    """Edit an existing flight (admin only)"""
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to edit flights.')
        return redirect('flights:flight_list')
    
    flight = get_object_or_404(Flight, id=flight_id)
    
    if request.method == 'POST':
        form = FlightForm(request.POST, instance=flight)
        if form.is_valid():
            form.save()
            messages.success(request, 'Flight updated successfully.')
            return redirect('flights:flight_detail', flight_id=flight.id)
    else:
        form = FlightForm(instance=flight)
    
    context = {
        'form': form,
        'flight': flight,
        'title': 'Edit Flight'
    }
    
    return render(request, 'flights/flight_form.html', context)

@login_required
def delete_flight_view(request, flight_id):
    """Delete a flight (admin only)"""
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to delete flights.')
        return redirect('flights:flight_list')
    
    flight = get_object_or_404(Flight, id=flight_id)
    
    if request.method == 'POST':
        flight.delete()
        messages.success(request, 'Flight deleted successfully.')
        return redirect('flights:flight_list')
    
    context = {
        'flight': flight,
        'title': 'Delete Flight'
    }
    
    return render(request, 'flights/flight_confirm_delete.html', context)

def create_airline_view(request):
    """Create a new airline"""
    if request.method == 'POST':
        form = AirlineForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Airline created successfully.')
            return redirect('flights:airline_list')
    else:
        form = AirlineForm()
    
    context = {
        'form': form,
        'title': 'Create Airline'
    }
    
    return render(request, 'flights/airline_form.html', context)

def edit_airline_view(request, airline_id):
    """Edit an existing airline"""
    airline = get_object_or_404(Airline, id=airline_id)
    
    if request.method == 'POST':
        form = AirlineForm(request.POST, request.FILES, instance=airline)
        if form.is_valid():
            form.save()
            messages.success(request, 'Airline updated successfully.')
            return redirect('flights:airline_detail', airline_id=airline.id)
    else:
        form = AirlineForm(instance=airline)
    
    context = {
        'form': form,
        'airline': airline,
        'title': 'Edit Airline'
    }
    
    return render(request, 'flights/airline_form.html', context)

def terminal_list_view(request):
    """List all terminals"""
    terminals = Terminal.objects.prefetch_related('gates').all()
    
    context = {
        'terminals': terminals,
        'title': 'Airport Terminals'
    }
    
    return render(request, 'flights/terminal_list.html', context)

def terminal_detail_view(request, terminal_id):
    """Terminal detail view"""
    terminal = get_object_or_404(Terminal, id=terminal_id)
    gates = terminal.gates.all()
    
    context = {
        'terminal': terminal,
        'gates': gates,
        'title': f'Terminal {terminal.name}'
    }
    
    return render(request, 'flights/terminal_detail.html', context)

def gate_detail_view(request, gate_id):
    """Gate detail view"""
    gate = get_object_or_404(Gate, id=gate_id)
    flights = gate.flights.filter(scheduled_departure__date=timezone.now().date())
    
    context = {
        'gate': gate,
        'flights': flights,
        'title': f'Gate {gate.gate_number}'
    }
    
    return render(request, 'flights/gate_detail.html', context)

def aircraft_list_view(request):
    """List all aircraft"""
    aircraft = Aircraft.objects.select_related('airline').all()
    
    context = {
        'aircraft': aircraft,
        'title': 'Aircraft Fleet'
    }
    
    return render(request, 'flights/aircraft_list.html', context)

def aircraft_detail_view(request, aircraft_id):
    """Aircraft detail view"""
    aircraft = get_object_or_404(Aircraft, id=aircraft_id)
    flights = aircraft.flights.all().order_by('-scheduled_departure')[:10]
    
    context = {
        'aircraft': aircraft,
        'flights': flights,
        'title': f'Aircraft {aircraft.registration_number}'
    }
    
    return render(request, 'flights/aircraft_detail.html', context)

def create_aircraft_view(request):
    """Create a new aircraft"""
    if request.method == 'POST':
        form = AircraftForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Aircraft created successfully.')
            return redirect('flights:aircraft_list')
    else:
        form = AircraftForm()
    
    context = {
        'form': form,
        'title': 'Add Aircraft'
    }
    
    return render(request, 'flights/aircraft_form.html', context)
