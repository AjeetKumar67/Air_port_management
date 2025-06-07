from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    # Main Dashboard
    path('', views.DashboardHomeView.as_view(), name='home'),
    
    # Role-specific Dashboards
    path('admin/', views.AdminDashboardView.as_view(), name='admin_dashboard'),
    path('staff/', views.StaffDashboardView.as_view(), name='staff_dashboard'),
    path('airline-staff/', views.AirlineStaffDashboardView.as_view(), name='airline_staff_dashboard'),
    path('passenger/', views.PassengerDashboardView.as_view(), name='passenger_dashboard'),
    
    # Reports and Analytics
    path('reports/', views.ReportsView.as_view(), name='reports'),
    path('reports/bookings/', views.BookingReportsView.as_view(), name='booking_reports'),
    path('reports/flights/', views.FlightReportsView.as_view(), name='flight_reports'),
    path('reports/airlines/', views.AirlineReportsView.as_view(), name='airline_reports'),
    
    # Quick Actions
    path('quick-flight-status/', views.QuickFlightStatusView.as_view(), name='quick_flight_status'),
    path('emergency-announcements/', views.EmergencyAnnouncementView.as_view(), name='emergency_announcements'),
]
