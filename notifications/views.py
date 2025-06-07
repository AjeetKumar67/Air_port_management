from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, View
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.utils import timezone
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Notification, Announcement, UserNotificationPreference, AnnouncementRead
from .forms import AnnouncementForm, NotificationPreferencesForm

class NotificationListView(LoginRequiredMixin, ListView):
    model = Notification
    template_name = 'notifications/notification_list.html'
    context_object_name = 'notifications'
    paginate_by = 20
    
    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user).order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['unread_count'] = self.get_queryset().filter(is_read=False).count()
        return context

class NotificationDetailView(LoginRequiredMixin, DetailView):
    model = Notification
    template_name = 'notifications/notification_detail.html'
    context_object_name = 'notification'
    
    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)
    
    def get_object(self):
        obj = super().get_object()
        if not obj.is_read:
            obj.mark_as_read()
        return obj

class MarkNotificationReadView(LoginRequiredMixin, View):
    def post(self, request, pk):
        notification = get_object_or_404(Notification, pk=pk, user=request.user)
        notification.mark_as_read()
        return JsonResponse({'status': 'success'})

class MarkAllNotificationsReadView(LoginRequiredMixin, View):
    def post(self, request):
        Notification.objects.filter(user=request.user, is_read=False).update(
            is_read=True,
            read_at=timezone.now()
        )
        return JsonResponse({'status': 'success'})

class AnnouncementListView(ListView):
    model = Announcement
    template_name = 'notifications/announcement_list.html'
    context_object_name = 'announcements'
    paginate_by = 10
    
    def get_queryset(self):
        queryset = Announcement.objects.filter(is_active=True)
        # Filter announcements based on user role and target audience
        user = self.request.user
        if user.is_authenticated:
            if user.is_passenger:
                queryset = queryset.filter(
                    Q(target_audience='all') | 
                    Q(target_audience='passengers')
                )
            elif user.is_staff_member:
                queryset = queryset.filter(
                    Q(target_audience='all') | 
                    Q(target_audience='staff')
                )
            elif user.is_airline_staff:
                queryset = queryset.filter(
                    Q(target_audience='all') | 
                    Q(target_audience='airline_staff')
                )
            elif user.is_admin:
                # Admins can see all announcements
                pass
        else:
            queryset = queryset.filter(target_audience='all')
        
        return queryset.order_by('-created_at')

class AnnouncementDetailView(DetailView):
    model = Announcement
    template_name = 'notifications/announcement_detail.html'
    context_object_name = 'announcement'
    
    def get_object(self):
        obj = super().get_object()
        # Mark announcement as read for authenticated users
        if self.request.user.is_authenticated:
            AnnouncementRead.objects.get_or_create(
                user=self.request.user,
                announcement=obj
            )
        return obj

class StaffRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and (
            self.request.user.is_admin or self.request.user.is_staff_member
        )

class AnnouncementCreateView(StaffRequiredMixin, CreateView):
    model = Announcement
    form_class = AnnouncementForm
    template_name = 'notifications/announcement_form.html'
    success_url = reverse_lazy('notifications:announcement_list')
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, 'Announcement created successfully!')
        return super().form_valid(form)

class AnnouncementUpdateView(StaffRequiredMixin, UpdateView):
    model = Announcement
    form_class = AnnouncementForm
    template_name = 'notifications/announcement_form.html'
    success_url = reverse_lazy('notifications:announcement_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Announcement updated successfully!')
        return super().form_valid(form)

class AnnouncementDeleteView(StaffRequiredMixin, DeleteView):
    model = Announcement
    template_name = 'notifications/announcement_confirm_delete.html'
    success_url = reverse_lazy('notifications:announcement_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Announcement deleted successfully!')
        return super().delete(request, *args, **kwargs)

class NotificationPreferencesView(LoginRequiredMixin, View):
    template_name = 'notifications/notification_preferences.html'
    
    def get(self, request):
        preferences, created = UserNotificationPreference.objects.get_or_create(
            user=request.user
        )
        form = NotificationPreferencesForm(instance=preferences)
        return render(request, self.template_name, {'form': form})
    
    def post(self, request):
        preferences, created = UserNotificationPreference.objects.get_or_create(
            user=request.user
        )
        form = NotificationPreferencesForm(request.POST, instance=preferences)
        if form.is_valid():
            form.save()
            messages.success(request, 'Notification preferences updated successfully!')
            return redirect('notifications:notification_preferences')
        return render(request, self.template_name, {'form': form})

# API Views for AJAX requests
class UnreadNotificationCountView(LoginRequiredMixin, View):
    def get(self, request):
        count = Notification.objects.filter(user=request.user, is_read=False).count()
        return JsonResponse({'unread_count': count})

class RecentNotificationsView(LoginRequiredMixin, View):
    def get(self, request):
        notifications = Notification.objects.filter(
            user=request.user
        ).order_by('-created_at')[:5]
        
        data = []
        for notification in notifications:
            data.append({
                'id': notification.id,
                'title': notification.title,
                'message': notification.message[:100] + '...' if len(notification.message) > 100 else notification.message,
                'is_read': notification.is_read,
                'created_at': notification.created_at.strftime('%Y-%m-%d %H:%M'),
                'notification_type': notification.get_notification_type_display(),
            })
        
        return JsonResponse({'notifications': data})
