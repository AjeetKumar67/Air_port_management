from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    # Notification URLs
    path('', views.NotificationListView.as_view(), name='notification_list'),
    path('<int:pk>/', views.NotificationDetailView.as_view(), name='notification_detail'),
    path('<int:pk>/mark-read/', views.MarkNotificationReadView.as_view(), name='mark_notification_read'),
    path('mark-all-read/', views.MarkAllNotificationsReadView.as_view(), name='mark_all_notifications_read'),
    
    # Announcement URLs
    path('announcements/', views.AnnouncementListView.as_view(), name='announcement_list'),
    path('announcements/<int:pk>/', views.AnnouncementDetailView.as_view(), name='announcement_detail'),
    path('announcements/create/', views.AnnouncementCreateView.as_view(), name='announcement_create'),
    path('announcements/<int:pk>/edit/', views.AnnouncementUpdateView.as_view(), name='announcement_edit'),
    path('announcements/<int:pk>/delete/', views.AnnouncementDeleteView.as_view(), name='announcement_delete'),
    
    # Notification Preferences
    path('preferences/', views.NotificationPreferencesView.as_view(), name='notification_preferences'),
    
    # API endpoints for AJAX requests
    path('api/unread-count/', views.UnreadNotificationCountView.as_view(), name='unread_notification_count'),
    path('api/recent/', views.RecentNotificationsView.as_view(), name='recent_notifications'),
]
