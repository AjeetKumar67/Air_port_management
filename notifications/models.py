from django.db import models
from django.conf import settings
from django.utils import timezone

class Announcement(models.Model):
    ANNOUNCEMENT_TYPE_CHOICES = [
        ('general', 'General'),
        ('flight_delay', 'Flight Delay'),
        ('flight_cancellation', 'Flight Cancellation'),
        ('boarding_call', 'Boarding Call'),
        ('gate_change', 'Gate Change'),
        ('security_alert', 'Security Alert'),
        ('weather_update', 'Weather Update'),
        ('maintenance', 'Maintenance'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    TARGET_AUDIENCE_CHOICES = [
        ('all', 'All Users'),
        ('passengers', 'Passengers'),
        ('staff', 'Staff'),
        ('airline_staff', 'Airline Staff'),
        ('admins', 'Admins'),
        ('specific_flight', 'Specific Flight'),
    ]
    
    title = models.CharField(max_length=200)
    message = models.TextField()
    announcement_type = models.CharField(max_length=20, choices=ANNOUNCEMENT_TYPE_CHOICES, default='general')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    target_audience = models.CharField(max_length=20, choices=TARGET_AUDIENCE_CHOICES, default='all')
    
    # Optional flight-specific announcement
    flight = models.ForeignKey('flights.Flight', on_delete=models.CASCADE, null=True, blank=True, related_name='announcements')
    
    # Scheduling
    is_active = models.BooleanField(default=True)
    start_time = models.DateTimeField(default=timezone.now)
    end_time = models.DateTimeField(null=True, blank=True)
    
    # Auto-repeat options
    repeat_announcement = models.BooleanField(default=False)
    repeat_interval = models.PositiveIntegerField(default=0, help_text="Repeat interval in minutes")
    
    # Metadata
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='created_announcements')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def is_currently_active(self):
        now = timezone.now()
        if not self.is_active:
            return False
        if self.start_time > now:
            return False
        if self.end_time and self.end_time < now:
            return False
        return True
    
    def __str__(self):
        return f"{self.get_announcement_type_display()}: {self.title}"
    
    class Meta:
        ordering = ['-created_at']

class Notification(models.Model):
    NOTIFICATION_TYPE_CHOICES = [
        ('booking_confirmation', 'Booking Confirmation'),
        ('check_in_reminder', 'Check-in Reminder'),
        ('boarding_call', 'Boarding Call'),
        ('flight_delay', 'Flight Delay'),
        ('flight_cancellation', 'Flight Cancellation'),
        ('gate_change', 'Gate Change'),
        ('baggage_update', 'Baggage Update'),
        ('system_alert', 'System Alert'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(max_length=30, choices=NOTIFICATION_TYPE_CHOICES)
    
    # Related objects
    booking = models.ForeignKey('bookings.Booking', on_delete=models.CASCADE, null=True, blank=True, related_name='notifications')
    flight = models.ForeignKey('flights.Flight', on_delete=models.CASCADE, null=True, blank=True, related_name='notifications')
    announcement = models.ForeignKey(Announcement, on_delete=models.CASCADE, null=True, blank=True, related_name='notifications')
    
    # Status
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    is_sent = models.BooleanField(default=False)
    sent_at = models.DateTimeField(null=True, blank=True)
    
    # Delivery methods
    send_email = models.BooleanField(default=True)
    send_sms = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def mark_as_read(self):
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save()
    
    def __str__(self):
        return f"{self.get_notification_type_display()} - {self.user.username}"
    
    class Meta:
        ordering = ['-created_at']

class UserNotificationPreference(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notification_preferences')
    
    # Email notifications
    email_booking_confirmations = models.BooleanField(default=True)
    email_flight_updates = models.BooleanField(default=True)
    email_check_in_reminders = models.BooleanField(default=True)
    email_promotional = models.BooleanField(default=False)
    
    # SMS notifications
    sms_booking_confirmations = models.BooleanField(default=False)
    sms_flight_updates = models.BooleanField(default=True)
    sms_check_in_reminders = models.BooleanField(default=False)
    
    # System notifications
    system_announcements = models.BooleanField(default=True)
    system_alerts = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Notification Preferences - {self.user.username}"

class AnnouncementRead(models.Model):
    """Track which users have seen which announcements"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    announcement = models.ForeignKey(Announcement, on_delete=models.CASCADE)
    read_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'announcement']
        ordering = ['-read_at']
    
    def __str__(self):
        return f"{self.user.username} read {self.announcement.title}"
