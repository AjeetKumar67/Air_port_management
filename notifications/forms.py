from django import forms
from django.core.exceptions import ValidationError
from .models import Announcement, UserNotificationPreference

class AnnouncementForm(forms.ModelForm):
    class Meta:
        model = Announcement
        fields = [
            'title', 'message', 'announcement_type', 'priority', 
            'target_audience', 'flight', 'start_time', 'end_time',
            'repeat_announcement', 'repeat_interval'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter announcement title...'
            }),
            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Enter announcement message...'
            }),
            'announcement_type': forms.Select(attrs={'class': 'form-control'}),
            'priority': forms.Select(attrs={'class': 'form-control'}),
            'target_audience': forms.Select(attrs={'class': 'form-control'}),
            'flight': forms.Select(attrs={'class': 'form-control'}),
            'start_time': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'end_time': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'repeat_announcement': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'repeat_interval': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'placeholder': 'Minutes'
            }),
        }
        labels = {
            'title': 'Announcement Title',
            'message': 'Announcement Message',
            'announcement_type': 'Type',
            'priority': 'Priority Level',
            'target_audience': 'Target Audience',
            'flight': 'Related Flight (Optional)',
            'start_time': 'Start Time',
            'end_time': 'End Time (Optional)',
            'repeat_announcement': 'Repeat Announcement',
            'repeat_interval': 'Repeat Every (Minutes)',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make flight field optional and filter by active flights
        self.fields['flight'].required = False
        self.fields['flight'].empty_label = "Select a flight (optional)"
        
        # Set up conditional fields
        self.fields['end_time'].required = False
        self.fields['repeat_interval'].required = False
    
    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        repeat_announcement = cleaned_data.get('repeat_announcement')
        repeat_interval = cleaned_data.get('repeat_interval')
        target_audience = cleaned_data.get('target_audience')
        flight = cleaned_data.get('flight')
        
        # Validate time range
        if start_time and end_time and end_time <= start_time:
            raise ValidationError("End time must be after start time.")
        
        # Validate repeat settings
        if repeat_announcement and not repeat_interval:
            raise ValidationError("Repeat interval is required when repeat announcement is enabled.")
        
        if repeat_interval and repeat_interval < 1:
            raise ValidationError("Repeat interval must be at least 1 minute.")
        
        # Validate flight-specific announcements
        if target_audience == 'specific_flight' and not flight:
            raise ValidationError("Flight must be selected for flight-specific announcements.")
        
        return cleaned_data

class NotificationPreferencesForm(forms.ModelForm):
    class Meta:
        model = UserNotificationPreference
        fields = [
            'email_booking_confirmations', 'email_flight_updates', 
            'email_check_in_reminders', 'email_promotional',
            'sms_booking_confirmations', 'sms_flight_updates', 
            'sms_check_in_reminders',
            'system_announcements', 'system_alerts'
        ]
        widgets = {
            'email_booking_confirmations': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'email_flight_updates': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'email_check_in_reminders': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'email_promotional': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'sms_booking_confirmations': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'sms_flight_updates': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'sms_check_in_reminders': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'system_announcements': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'system_alerts': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'email_booking_confirmations': 'Email Booking Confirmations',
            'email_flight_updates': 'Email Flight Updates',
            'email_check_in_reminders': 'Email Check-in Reminders',
            'email_promotional': 'Email Promotional Messages',
            'sms_booking_confirmations': 'SMS Booking Confirmations',
            'sms_flight_updates': 'SMS Flight Updates',
            'sms_check_in_reminders': 'SMS Check-in Reminders',
            'system_announcements': 'System Announcements',
            'system_alerts': 'System Alerts',
        }

class QuickAnnouncementForm(forms.Form):
    """Quick announcement form for emergency situations"""
    title = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Emergency announcement title...'
        })
    )
    message = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Emergency message...'
        })
    )
    priority = forms.ChoiceField(
        choices=[
            ('high', 'High'),
            ('urgent', 'Urgent')
        ],
        widget=forms.Select(attrs={'class': 'form-control'}),
        initial='urgent'
    )
    target_audience = forms.ChoiceField(
        choices=[
            ('all', 'All Users'),
            ('passengers', 'All Passengers'),
            ('staff', 'All Staff'),
        ],
        widget=forms.Select(attrs={'class': 'form-control'}),
        initial='all'
    )