from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash

from .models import Activity
from students.models import Student
from attendance.models import Attendance
from plans.models import MemorizationPlan
from evaluations.models import Evaluation

from datetime import date

def login_view(request):
    """
    Handle user login
    """
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            Activity.objects.create(
                user=user,
                description=f"تم تسجيل الدخول بنجاح"
            )
            messages.success(request, f"مرحباً بك، {username}!")
            return redirect('dashboard')
        else:
            messages.error(request, "بيانات الدخول غير صحيحة. يرجى المحاولة مرة أخرى.")
    
    return render(request, 'core/login.html')

def logout_view(request):
    """
    Handle user logout
    """
    if request.user.is_authenticated:
        username = request.user.username
        Activity.objects.create(
            user=request.user,
            description=f"تم تسجيل الخروج"
        )
        logout(request)
        messages.success(request, "تم تسجيل الخروج بنجاح.")
    
    return redirect('login')

@login_required
def dashboard(request):
    """
    Display the dashboard with key metrics and recent activities
    """
    # Get today's date
    today = date.today()
    
    # Calculate metrics
    total_students = Student.objects.filter(status='active').count()
    present_today = Attendance.objects.filter(date=today, status='present').count()
    active_plans = MemorizationPlan.objects.filter(week_start__lte=today, week_end__gte=today).count()
    evaluation_count = Evaluation.objects.count()
    
    # Get recent activities
    recent_activities = Activity.objects.all()[:10]
    
    # Get today's tasks
    today_tasks = []
    if 'plans' in request.META.get('INSTALLED_APPS', []):
        from plans.models import DailyTask
        today_tasks = DailyTask.objects.filter(date=today)
    
    context = {
        'total_students': total_students,
        'present_today': present_today,
        'active_plans': active_plans,
        'evaluation_count': evaluation_count,
        'recent_activities': recent_activities,
        'today_tasks': today_tasks,
    }
    
    return render(request, 'core/dashboard.html', context)

@login_required
def profile_view(request):
    """
    Handle user profile settings
    """
    user = request.user
    password_form = PasswordChangeForm(user)
    
    if request.method == 'POST':
        if 'update_profile' in request.POST:
            # Handle profile information update
            username = request.POST.get('username')
            email = request.POST.get('email')
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            
            # Update user information
            user.username = username
            user.email = email
            user.first_name = first_name
            user.last_name = last_name
            user.save()
            
            # Process profile image if provided
            if 'profile_image' in request.FILES:
                # Assume we're using UserProfile model with a profile_image field
                try:
                    profile = user.userprofile
                except:
                    # If UserProfile doesn't exist, we're not handling it here
                    pass
                else:
                    profile.profile_image = request.FILES['profile_image']
                    profile.save()
            
            Activity.objects.create(
                user=user,
                description="تم تحديث معلومات الحساب"
            )
            messages.success(request, "تم تحديث معلومات الحساب بنجاح.")
            
        elif 'update_password' in request.POST:
            # Handle password change
            password_form = PasswordChangeForm(user, request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)  # Important to keep user logged in
                
                Activity.objects.create(
                    user=user,
                    description="تم تغيير كلمة المرور"
                )
                messages.success(request, "تم تغيير كلمة المرور بنجاح.")
            else:
                for error in password_form.errors.values():
                    messages.error(request, error)
    
    context = {
        'password_form': password_form,
    }
    
    return render(request, 'core/profile.html', context)
