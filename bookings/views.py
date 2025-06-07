from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, View
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.db import transaction
from django.core.exceptions import ValidationError
import qrcode
from io import BytesIO
import base64
from .models import Booking, BoardingPass, Seat, Baggage, FlightStaff
from .forms import BookingForm, SeatSelectionForm, BaggageForm
from flights.models import Flight
from notifications.models import Notification

class BookingListView(LoginRequiredMixin, ListView):
    model = Booking
    template_name = 'bookings/booking_list.html'
    context_object_name = 'bookings'
    paginate_by = 10
    
    def get_queryset(self):
        if self.request.user.is_passenger:
            return Booking.objects.filter(user=self.request.user).order_by('-created_at')
        elif self.request.user.is_staff_member or self.request.user.is_admin:
            return Booking.objects.all().order_by('-created_at')
        elif self.request.user.is_airline_staff:
            # Filter by airline - this would need airline assignment in User model
            return Booking.objects.all().order_by('-created_at')
        return Booking.objects.none()

class BookingDetailView(LoginRequiredMixin, DetailView):
    model = Booking
    template_name = 'bookings/booking_detail.html'
    context_object_name = 'booking'
    
    def get_queryset(self):
        if self.request.user.is_passenger:
            return Booking.objects.filter(user=self.request.user)
        elif self.request.user.is_staff_member or self.request.user.is_admin:
            return Booking.objects.all()
        elif self.request.user.is_airline_staff:
            return Booking.objects.all()
        return Booking.objects.none()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        booking = self.get_object()
        context['boarding_pass'] = BoardingPass.objects.filter(booking=booking).first()
        context['baggage'] = Baggage.objects.filter(booking=booking)
        return context

class BookingCreateView(LoginRequiredMixin, View):
    template_name = 'bookings/booking_form.html'
    
    def get(self, request, flight_id=None):
        if flight_id:
            flight = get_object_or_404(Flight, id=flight_id, is_active=True)
        else:
            flight = None
        
        form = BookingForm(initial={'flight': flight} if flight else None)
        return render(request, self.template_name, {
            'form': form,
            'flight': flight
        })
    
    def post(self, request, flight_id=None):
        form = BookingForm(request.POST)
        flight = None
        
        if flight_id:
            flight = get_object_or_404(Flight, id=flight_id, is_active=True)
        
        if form.is_valid():
            try:
                with transaction.atomic():
                    booking = form.save(commit=False)
                    booking.user = request.user
                    booking.booking_reference = booking.generate_booking_reference()
                    booking.total_amount = booking.calculate_total_amount()
                    booking.save()
                    
                    # Create notification
                    Notification.objects.create(
                        user=request.user,
                        title='Booking Confirmation',
                        message=f'Your booking {booking.booking_reference} has been confirmed.',
                        notification_type='booking_confirmation',
                        booking=booking
                    )
                    
                    messages.success(request, f'Booking created successfully! Reference: {booking.booking_reference}')
                    return redirect('bookings:seat_selection', booking_id=booking.id)
                    
            except ValidationError as e:
                messages.error(request, str(e))
        
        return render(request, self.template_name, {
            'form': form,
            'flight': flight
        })

class SeatSelectionView(LoginRequiredMixin, View):
    template_name = 'bookings/seat_selection.html'
    
    def get(self, request, booking_id):
        booking = get_object_or_404(Booking, id=booking_id, user=request.user)
        
        if booking.status != 'confirmed':
            messages.error(request, 'Seat selection is only available for confirmed bookings.')
            return redirect('bookings:booking_detail', pk=booking.id)
        
        # Get available seats
        aircraft = booking.flight.aircraft
        occupied_seats = Seat.objects.filter(
            booking__flight=booking.flight,
            booking__status='confirmed'
        ).values_list('seat_number', flat=True)
        
        # Generate seat map
        seat_map = self.generate_seat_map(aircraft, occupied_seats)
        
        return render(request, self.template_name, {
            'booking': booking,
            'seat_map': seat_map,
            'aircraft': aircraft
        })
    
    def post(self, request, booking_id):
        booking = get_object_or_404(Booking, id=booking_id, user=request.user)
        seat_numbers = request.POST.getlist('seats')
        
        if len(seat_numbers) != booking.number_of_passengers:
            return JsonResponse({
                'success': False,
                'error': f'Please select {booking.number_of_passengers} seat(s)'
            })
        
        try:
            with transaction.atomic():
                # Clear existing seats
                Seat.objects.filter(booking=booking).delete()
                
                # Create new seat assignments
                for seat_number in seat_numbers:
                    Seat.objects.create(
                        booking=booking,
                        seat_number=seat_number,
                        seat_class=booking.seat_class
                    )
                
                return JsonResponse({'success': True})
                
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    def generate_seat_map(self, aircraft, occupied_seats):
        """Generate seat map for the aircraft"""
        seat_map = {
            'economy': [],
            'business': [],
            'first_class': []
        }
        
        # Economy seats (rows 1-30, seats A-F)
        for row in range(1, 31):
            for seat_letter in ['A', 'B', 'C', 'D', 'E', 'F']:
                seat_number = f"{row}{seat_letter}"
                seat_map['economy'].append({
                    'number': seat_number,
                    'available': seat_number not in occupied_seats,
                    'row': row,
                    'letter': seat_letter
                })
        
        # Business seats (rows 1-5, seats A-D)
        for row in range(1, 6):
            for seat_letter in ['A', 'B', 'C', 'D']:
                seat_number = f"B{row}{seat_letter}"
                seat_map['business'].append({
                    'number': seat_number,
                    'available': seat_number not in occupied_seats,
                    'row': row,
                    'letter': seat_letter
                })
        
        return seat_map

class CheckInView(LoginRequiredMixin, View):
    def post(self, request, booking_id):
        booking = get_object_or_404(Booking, id=booking_id, user=request.user)
        
        if booking.status != 'confirmed':
            return JsonResponse({'success': False, 'error': 'Only confirmed bookings can be checked in'})
        
        # Check if already checked in
        if BoardingPass.objects.filter(booking=booking).exists():
            return JsonResponse({'success': False, 'error': 'Already checked in'})
        
        # Check if seats are assigned
        if not Seat.objects.filter(booking=booking).exists():
            return JsonResponse({'success': False, 'error': 'Please select seats first'})
        
        try:
            with transaction.atomic():
                # Create boarding pass
                boarding_pass = BoardingPass.objects.create(
                    booking=booking,
                    seat_numbers=', '.join(
                        Seat.objects.filter(booking=booking).values_list('seat_number', flat=True)
                    ),
                    gate=booking.flight.gate.gate_number if booking.flight.gate else 'TBA',
                    boarding_time=booking.flight.scheduled_departure - timezone.timedelta(minutes=30)
                )
                
                # Generate QR code
                boarding_pass.generate_qr_code()
                
                # Create notification
                Notification.objects.create(
                    user=request.user,
                    title='Check-in Successful',
                    message=f'Check-in completed for flight {booking.flight.flight_number}',
                    notification_type='check_in_reminder',
                    booking=booking
                )
                
                return JsonResponse({
                    'success': True,
                    'boarding_pass_id': boarding_pass.id
                })
                
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

class BoardingPassView(LoginRequiredMixin, DetailView):
    model = BoardingPass
    template_name = 'bookings/boarding_pass.html'
    context_object_name = 'boarding_pass'
    
    def get_queryset(self):
        return BoardingPass.objects.filter(booking__user=self.request.user)

class BoardingPassDownloadView(LoginRequiredMixin, View):
    def get(self, request, boarding_pass_id):
        boarding_pass = get_object_or_404(
            BoardingPass, 
            id=boarding_pass_id, 
            booking__user=request.user
        )
        
        # Generate PDF or return the boarding pass template
        # For now, just redirect to the view
        return redirect('bookings:boarding_pass_detail', pk=boarding_pass.id)

class BaggageManagementView(LoginRequiredMixin, View):
    template_name = 'bookings/baggage_management.html'
    
    def get(self, request, booking_id):
        booking = get_object_or_404(Booking, id=booking_id, user=request.user)
        baggage = Baggage.objects.filter(booking=booking)
        form = BaggageForm()
        
        return render(request, self.template_name, {
            'booking': booking,
            'baggage': baggage,
            'form': form
        })
    
    def post(self, request, booking_id):
        booking = get_object_or_404(Booking, id=booking_id, user=request.user)
        form = BaggageForm(request.POST)
        
        if form.is_valid():
            baggage = form.save(commit=False)
            baggage.booking = booking
            baggage.tracking_number = baggage.generate_tracking_number()
            baggage.save()
            
            messages.success(request, f'Baggage added successfully. Tracking: {baggage.tracking_number}')
            return redirect('bookings:baggage_management', booking_id=booking.id)
        
        baggage = Baggage.objects.filter(booking=booking)
        return render(request, self.template_name, {
            'booking': booking,
            'baggage': baggage,
            'form': form
        })

class CancelBookingView(LoginRequiredMixin, View):
    def post(self, request, booking_id):
        booking = get_object_or_404(Booking, id=booking_id, user=request.user)
        
        if booking.status == 'cancelled':
            return JsonResponse({'success': False, 'error': 'Booking is already cancelled'})
        
        # Check if cancellation is allowed (e.g., not within 24 hours of departure)
        time_to_departure = booking.flight.scheduled_departure - timezone.now()
        if time_to_departure < timezone.timedelta(hours=24):
            return JsonResponse({
                'success': False, 
                'error': 'Cannot cancel booking within 24 hours of departure'
            })
        
        try:
            with transaction.atomic():
                booking.status = 'cancelled'
                booking.cancelled_at = timezone.now()
                booking.save()
                
                # Create notification
                Notification.objects.create(
                    user=request.user,
                    title='Booking Cancelled',
                    message=f'Your booking {booking.booking_reference} has been cancelled.',
                    notification_type='booking_confirmation',
                    booking=booking
                )
                
                return JsonResponse({'success': True})
                
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

# API Views for AJAX requests
class AvailableSeatsAPIView(LoginRequiredMixin, View):
    def get(self, request, flight_id):
        flight = get_object_or_404(Flight, id=flight_id)
        
        occupied_seats = list(Seat.objects.filter(
            booking__flight=flight,
            booking__status='confirmed'
        ).values_list('seat_number', flat=True))
        
        return JsonResponse({
            'occupied_seats': occupied_seats,
            'total_seats': flight.aircraft.capacity if flight.aircraft else 0
        })

class FlightSearchAPIView(View):
    def get(self, request):
        origin = request.GET.get('origin')
        destination = request.GET.get('destination')
        departure_date = request.GET.get('departure_date')
        
        flights = Flight.objects.filter(
            source__icontains=origin,
            destination__icontains=destination,
            scheduled_departure__date=departure_date,
            is_active=True
        ).select_related('airline', 'aircraft')
        
        data = []
        for flight in flights:
            data.append({
                'id': flight.id,
                'flight_number': flight.flight_number,
                'airline': flight.airline.name,
                'departure_time': flight.scheduled_departure.strftime('%H:%M'),
                'arrival_time': flight.scheduled_arrival.strftime('%H:%M'),
                'duration': str(flight.duration),
                'economy_price': float(flight.economy_price),
                'business_price': float(flight.business_price),
                'available_economy': flight.available_economy_seats,
                'available_business': flight.available_business_seats,
            })
        
        return JsonResponse({'flights': data})
