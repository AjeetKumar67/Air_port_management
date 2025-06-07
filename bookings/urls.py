from django.urls import path
from . import views

app_name = 'bookings'

urlpatterns = [
    # Booking URLs
    path('', views.BookingListView.as_view(), name='booking_list'),
    path('<int:pk>/', views.BookingDetailView.as_view(), name='booking_detail'),
    path('create/<int:flight_id>/', views.BookingCreateView.as_view(), name='booking_create'),
    path('<int:pk>/cancel/', views.CancelBookingView.as_view(), name='booking_cancel'),
    
    # Check-in URLs
    path('<int:pk>/checkin/', views.CheckInView.as_view(), name='checkin'),
    path('<int:pk>/boarding-pass/', views.BoardingPassView.as_view(), name='boarding_pass'),
    path('boarding-pass/<int:pk>/download/', views.BoardingPassDownloadView.as_view(), name='boarding_pass_download'),
    
    # Seat Selection URLs
    path('<int:booking_id>/select-seat/', views.SeatSelectionView.as_view(), name='seat_selection'),
    path('api/available-seats/', views.AvailableSeatsAPIView.as_view(), name='available_seats_api'),
    
    # Baggage URLs
    path('<int:booking_id>/baggage/', views.BaggageManagementView.as_view(), name='baggage_management'),
    
    # API URLs
    path('api/flight-search/', views.FlightSearchAPIView.as_view(), name='flight_search_api'),
]
