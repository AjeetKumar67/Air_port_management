from django.urls import path
from . import views

app_name = 'flights'

urlpatterns = [
    # Flight URLs
    path('', views.flight_list_view, name='flight_list'),
    path('<int:flight_id>/', views.flight_detail_view, name='flight_detail'),
    path('search/', views.flight_search_view, name='flight_search'),
    path('status/', views.flight_status_view, name='flight_status'),
    
    # Admin Flight Management URLs
    path('manage/', views.flight_management_view, name='flight_manage'),
    path('create/', views.create_flight_view, name='flight_create'),
    path('<int:flight_id>/edit/', views.edit_flight_view, name='flight_edit'),
    path('<int:flight_id>/delete/', views.delete_flight_view, name='flight_delete'),
    
    # Airline URLs
    path('airlines/', views.airline_list_view, name='airline_list'),
    path('airlines/<int:airline_id>/', views.airline_detail_view, name='airline_detail'),
    path('airlines/create/', views.create_airline_view, name='airline_create'),
    path('airlines/<int:airline_id>/edit/', views.edit_airline_view, name='airline_edit'),
    
    # Terminal and Gate URLs
    path('terminals/', views.terminal_list_view, name='terminal_list'),
    path('terminals/<int:terminal_id>/', views.terminal_detail_view, name='terminal_detail'),
    path('gates/', views.gate_list_view, name='gate_list'),
    path('gates/<int:gate_id>/', views.gate_detail_view, name='gate_detail'),
    
    # Aircraft URLs
    path('aircraft/', views.aircraft_list_view, name='aircraft_list'),
    path('aircraft/<int:aircraft_id>/', views.aircraft_detail_view, name='aircraft_detail'),
    path('aircraft/create/', views.create_aircraft_view, name='aircraft_create'),
]
