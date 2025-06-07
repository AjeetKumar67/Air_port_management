from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q
from .models import User
from .forms import UserRegistrationForm, UserLoginForm, UserProfileForm
from django.contrib.auth.forms import PasswordChangeForm

def register_view(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            messages.success(request, 'Registration successful! Please login.')
            return redirect('users:login')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'users/register.html', {'form': form})

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard:home')
    
    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            
            try:
                user = User.objects.get(email=email)
                user = authenticate(request, username=user.username, password=password)
                if user:
                    login(request, user)
                    next_url = request.GET.get('next', 'dashboard:home')
                    messages.success(request, f'Welcome back, {user.get_full_name()}!')
                    return redirect(next_url)
                else:
                    messages.error(request, 'Invalid email or password.')
            except User.DoesNotExist:
                messages.error(request, 'Invalid email or password.')
    else:
        form = UserLoginForm()
    
    return render(request, 'users/login.html', {'form': form})

@login_required
def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('users:login')

@login_required
def profile_view(request):
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('users:profile')
    else:
        form = UserProfileForm(instance=request.user)
    
    return render(request, 'users/profile.html', {'form': form})

@login_required
def change_password_view(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # Keep user logged in after password change
            messages.success(request, 'Password changed successfully!')
            return redirect('users:profile')
    else:
        form = PasswordChangeForm(request.user)
        # Add CSS classes to form fields
        for field in form.fields.values():
            field.widget.attrs.update({'class': 'form-control'})
    
    return render(request, 'users/change_password.html', {'form': form})

@login_required
def user_management_view(request):
    if request.user.role != 'admin':
        messages.error(request, 'Access denied. Admin privileges required.')
        return redirect('dashboard:home')
    
    search_query = request.GET.get('search', '')
    role_filter = request.GET.get('role', '')
    
    users = User.objects.all()
    
    if search_query:
        users = users.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(username__icontains=search_query)
        )
    
    if role_filter:
        users = users.filter(role=role_filter)
    
    users = users.order_by('-date_joined')
    
    paginator = Paginator(users, 20)
    page_number = request.GET.get('page')
    users_page = paginator.get_page(page_number)
    
    context = {
        'users': users_page,
        'search_query': search_query,
        'role_filter': role_filter,
        'roles': User.ROLE_CHOICES,
    }
    
    return render(request, 'users/user_management.html', context)

@login_required
def user_detail_view(request, user_id):
    if request.user.role not in ['admin', 'staff']:
        messages.error(request, 'Access denied.')
        return redirect('dashboard:home')
    
    user = get_object_or_404(User, id=user_id)
    
    context = {
        'user_detail': user,
        'bookings': user.bookings.all()[:10] if user.role == 'passenger' else None,
        'flight_assignments': user.flight_assignments.all()[:10] if user.role in ['staff', 'airline_staff'] else None,
    }
    
    return render(request, 'users/user_detail.html', context)

@login_required
def toggle_user_status(request, user_id):
    if request.user.role != 'admin':
        return JsonResponse({'success': False, 'message': 'Access denied'})
    
    if request.method == 'POST':
        user = get_object_or_404(User, id=user_id)
        user.is_active = not user.is_active
        user.save()
        
        status = 'activated' if user.is_active else 'deactivated'
        return JsonResponse({
            'success': True, 
            'message': f'User {status} successfully',
            'is_active': user.is_active
        })
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})

@login_required
def update_user_role(request, user_id):
    if request.user.role != 'admin':
        return JsonResponse({'success': False, 'message': 'Access denied'})
    
    if request.method == 'POST':
        user = get_object_or_404(User, id=user_id)
        new_role = request.POST.get('role')
        
        if new_role in dict(User.ROLE_CHOICES):
            user.role = new_role
            user.save()
            return JsonResponse({
                'success': True, 
                'message': f'User role updated to {user.get_role_display()}'
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})
