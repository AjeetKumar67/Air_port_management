from django.shortcuts import render, redirect
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView, View
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Count, Sum, Q, Avg
from datetime import datetime, timedelta
from users.models import User
from flights.models import Flight, Airline, Gate, Terminal
from bookings.models import Booking, BoardingPass, Baggage
from notifications.models import Announcement, Notification
from .models import DashboardStats, UserActivity, SystemAlert, QuickAction

class DashboardHomeView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/home.html'
    
    def dispatch(self, request, *args, **kwargs):
        # Redirect users to their role-specific dashboard
        if request.user.is_authenticated:
            if request.user.is_admin:
                return redirect('dashboard:admin_dashboard')
            elif request.user.is_staff_member:
                return redirect('dashboard:staff_dashboard')
            elif request.user.is_airline_staff:
                return redirect('dashboard:airline_staff_dashboard')
            elif request.user.is_passenger:
                return redirect('dashboard:passenger_dashboard')
        return super().dispatch(request, *args, **kwargs)

class AdminDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'dashboard/admin_dashboard.html'
    
    def test_func(self):
        return self.request.user.is_admin
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.now().date()
        
        # Basic Statistics
        context.update({
            'total_users': User.objects.count(),
            'total_flights': Flight.objects.count(),
            'total_bookings': Booking.objects.count(),
            'active_airlines': Airline.objects.filter(is_active=True).count(),
            
            # Today's Statistics
            'todays_flights': Flight.objects.filter(scheduled_departure__date=today).count(),
            'todays_bookings': Booking.objects.filter(created_at__date=today).count(),
            'todays_revenue': Booking.objects.filter(
                created_at__date=today,
                status='confirmed'
            ).aggregate(total=Sum('total_amount'))['total'] or 0,
            
            # Flight Status Distribution
            'scheduled_flights': Flight.objects.filter(status='scheduled').count(),
            'delayed_flights': Flight.objects.filter(status='delayed').count(),
            'cancelled_flights': Flight.objects.filter(status='cancelled').count(),
            'departed_flights': Flight.objects.filter(status='departed').count(),
            
            # Recent Activities
            'recent_activities': UserActivity.objects.select_related('user').order_by('-timestamp')[:10],
            
            # System Alerts
            'unresolved_alerts': SystemAlert.objects.filter(is_resolved=False).order_by('-created_at')[:5],
            
            # Quick Actions
            'quick_actions': QuickAction.objects.filter(
                available_for_admin=True,
                is_active=True
            ).order_by('order'),
            
            # Recent Announcements
            'recent_announcements': Announcement.objects.filter(is_active=True).order_by('-created_at')[:5],
        })
        
        return context

class StaffDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'dashboard/staff_dashboard.html'
    
    def test_func(self):
        return self.request.user.is_staff_member or self.request.user.is_admin
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.now().date()
        now = timezone.now()
        
        # Today's flight operations
        todays_flights = Flight.objects.filter(scheduled_departure__date=today)
        
        context.update({
            # Flight Operations
            'todays_flights_count': todays_flights.count(),
            'boarding_flights': todays_flights.filter(status='boarding').count(),
            'delayed_flights': todays_flights.filter(status='delayed').count(),
            'departed_flights': todays_flights.filter(status='departed').count(),
            
            # Gate Information
            'total_gates': Gate.objects.filter(is_active=True).count(),
            'occupied_gates': Gate.objects.filter(
                flights__scheduled_departure__date=today,
                flights__status__in=['boarding', 'scheduled']
            ).distinct().count(),
            'available_gates': Gate.objects.filter(
                is_active=True,
                status='available'
            ).count(),
            
            # Passenger Information
            'todays_passengers': Booking.objects.filter(
                flight__scheduled_departure__date=today,
                status='confirmed'
            ).aggregate(total=Sum('number_of_passengers'))['total'] or 0,
            
            'checked_in_passengers': BoardingPass.objects.filter(
                booking__flight__scheduled_departure__date=today,
                is_used=False
            ).count(),
            
            # Next departures
            'next_departures': Flight.objects.filter(
                scheduled_departure__gte=now,
                scheduled_departure__date=today,
                status__in=['scheduled', 'boarding']
            ).order_by('scheduled_departure')[:5],
            
            # Recent baggage
            'recent_baggage': Baggage.objects.filter(
                created_at__date=today
            ).order_by('-created_at')[:5],
            
            # Quick Actions
            'quick_actions': QuickAction.objects.filter(
                available_for_staff=True,
                is_active=True
            ).order_by('order'),
        })
        
        return context

class AirlineStaffDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'dashboard/airline_staff_dashboard.html'
    
    def test_func(self):
        return self.request.user.is_airline_staff or self.request.user.is_admin
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.now().date()
        
        # Get user's airline (this would need to be implemented in User model)
        # For now, we'll show all flights - in real implementation, filter by airline
        
        context.update({
            # Flight Statistics
            'total_flights': Flight.objects.count(),
            'todays_flights': Flight.objects.filter(scheduled_departure__date=today).count(),
            'active_bookings': Booking.objects.filter(status='confirmed').count(),
            'revenue_today': Booking.objects.filter(
                created_at__date=today,
                status='confirmed'
            ).aggregate(total=Sum('total_amount'))['total'] or 0,
            
            # Flight Status
            'scheduled_flights': Flight.objects.filter(
                scheduled_departure__date=today,
                status='scheduled'
            ).count(),
            'boarding_flights': Flight.objects.filter(
                scheduled_departure__date=today,
                status='boarding'
            ).count(),
            'delayed_flights': Flight.objects.filter(
                scheduled_departure__date=today,
                status='delayed'
            ).count(),
            
            # Recent flights
            'recent_flights': Flight.objects.filter(
                scheduled_departure__date=today
            ).order_by('scheduled_departure')[:5],
            
            # Quick Actions
            'quick_actions': QuickAction.objects.filter(
                available_for_airline_staff=True,
                is_active=True
            ).order_by('order'),
        })
        
        return context

class PassengerDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/passenger_dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # User's bookings
        user_bookings = Booking.objects.filter(user=user)
        upcoming_bookings = user_bookings.filter(
            flight__scheduled_departure__gte=timezone.now(),
            status='confirmed'
        ).order_by('flight__scheduled_departure')
        
        context.update({
            # Booking Statistics
            'total_bookings': user_bookings.count(),
            'upcoming_flights': upcoming_bookings.count(),
            'completed_flights': user_bookings.filter(
                flight__scheduled_departure__lt=timezone.now(),
                status='confirmed'
            ).count(),
            
            # Next Flight
            'next_flight': upcoming_bookings.first(),
            
            # Recent Bookings
            'recent_bookings': user_bookings.order_by('-created_at')[:5],
            
            # Boarding Passes
            'boarding_passes': BoardingPass.objects.filter(
                booking__user=user,
                booking__flight__scheduled_departure__gte=timezone.now()
            ).order_by('booking__flight__scheduled_departure')[:3],
            
            # Notifications
            'unread_notifications': Notification.objects.filter(
                user=user,
                is_read=False
            ).count(),
            
            # Quick Actions
            'quick_actions': QuickAction.objects.filter(
                available_for_passenger=True,
                is_active=True
            ).order_by('order'),
        })
        
        return context

class ReportsView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'dashboard/reports.html'
    
    def test_func(self):
        return self.request.user.is_admin or self.request.user.is_staff_member

class BookingReportsView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'dashboard/booking_reports.html'
    
    def test_func(self):
        return self.request.user.is_admin or self.request.user.is_staff_member
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Last 30 days booking trends
        thirty_days_ago = timezone.now().date() - timedelta(days=30)
        booking_trends = []
        
        for i in range(30):
            date = thirty_days_ago + timedelta(days=i)
            bookings_count = Booking.objects.filter(created_at__date=date).count()
            revenue = Booking.objects.filter(
                created_at__date=date,
                status='confirmed'
            ).aggregate(total=Sum('total_amount'))['total'] or 0
            
            booking_trends.append({
                'date': date,
                'bookings': bookings_count,
                'revenue': revenue
            })
        
        context['booking_trends'] = booking_trends
        return context

class FlightReportsView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'dashboard/flight_reports.html'
    
    def test_func(self):
        return self.request.user.is_admin or self.request.user.is_staff_member

class AirlineReportsView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'dashboard/airline_reports.html'
    
    def test_func(self):
        return self.request.user.is_admin or self.request.user.is_staff_member

class QuickFlightStatusView(LoginRequiredMixin, View):
    def get(self, request):
        flight_number = request.GET.get('flight_number', '')
        if flight_number:
            try:
                flight = Flight.objects.get(flight_number__icontains=flight_number)
                data = {
                    'found': True,
                    'flight_number': flight.flight_number,
                    'airline': flight.airline.name,
                    'status': flight.get_status_display(),
                    'departure': flight.scheduled_departure.strftime('%Y-%m-%d %H:%M'),
                    'arrival': flight.scheduled_arrival.strftime('%Y-%m-%d %H:%M'),
                    'gate': flight.gate.gate_number if flight.gate else 'Not assigned',
                    'terminal': flight.departure_terminal.name if flight.departure_terminal else 'Not assigned'
                }
            except Flight.DoesNotExist:
                data = {'found': False}
        else:
            data = {'found': False}
        
        return JsonResponse(data)

class EmergencyAnnouncementView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.is_admin or self.request.user.is_staff_member
    
    def post(self, request):
        title = request.POST.get('title')
        message = request.POST.get('message')
        priority = request.POST.get('priority', 'urgent')
        target_audience = request.POST.get('target_audience', 'all')
        
        if title and message:
            announcement = Announcement.objects.create(
                title=title,
                message=message,
                announcement_type='general',
                priority=priority,
                target_audience=target_audience,
                created_by=request.user,
                is_active=True
            )
            return JsonResponse({'success': True, 'id': announcement.id})
        
        return JsonResponse({'success': False, 'error': 'Title and message are required'})
