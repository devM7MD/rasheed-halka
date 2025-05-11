from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.db import transaction
from django.db import models
from django.template.loader import render_to_string
from django.conf import settings

from .models import MemorizationPlan, DailyTask
from students.models import Student
from core.models import Activity
from attendance.models import Attendance

from datetime import date, timedelta
import os
import io
import weasyprint
from weasyprint import HTML, CSS

@login_required
def plan_list(request):
    """
    Display a list of memorization plans
    """
    # Get filter parameters
    student_id = request.GET.get('student_id')
    week_start = request.GET.get('week_start')
    
    # Base queryset
    plans = MemorizationPlan.objects.all()
    
    # Apply filters
    if student_id:
        plans = plans.filter(student_id=student_id)
    
    if week_start:
        try:
            start_date = timezone.datetime.strptime(week_start, '%Y-%m-%d').date()
            plans = plans.filter(week_start=start_date)
        except ValueError:
            pass
    
    # Get unique weeks for the filter dropdown
    weeks = MemorizationPlan.objects.values_list('week_start', flat=True).distinct().order_by('-week_start')
    
    # Get students for the filter dropdown
    students = Student.objects.filter(status='active')
    
    context = {
        'plans': plans,
        'weeks': weeks,
        'students': students,
        'selected_student_id': student_id,
        'selected_week': week_start,
    }
    
    return render(request, 'plans/plan_list.html', context)

@login_required
def plan_detail(request, plan_id):
    """
    Display details of a specific memorization plan
    """
    plan = get_object_or_404(MemorizationPlan, id=plan_id)
    # الحصول على المهام اليومية مرتبة حسب التاريخ ثم نوع المهمة
    # حفظ جديد ثم مراجعة ثم الدروس الأخرى
    daily_tasks = DailyTask.objects.filter(plan=plan).order_by('date', 
                                                           models.Case(
                                                               models.When(task_type='new', then=models.Value(1)),
                                                               models.When(task_type='review', then=models.Value(2)),
                                                               default=models.Value(3),
                                                               output_field=models.IntegerField(),
                                                           ))
    
    context = {
        'plan': plan,
        'daily_tasks': daily_tasks,
    }
    
    return render(request, 'plans/plan_detail.html', context)

@login_required
def plan_generate(request):
    """
    Generate new memorization plans
    """
    today = date.today()
    students = Student.objects.filter(status='active')
    
    if request.method == 'POST':
        week_start_str = request.POST.get('week_start')
        target_ayahs = int(request.POST.get('target_ayahs', 5))
        include_review = request.POST.get('include_review') == '1'
        review_surah = int(request.POST.get('review_surah', 0))
        review_ayah_count = int(request.POST.get('review_ayah_count', 10))
        
        try:
            # Get the start of the week
            week_start = timezone.datetime.strptime(week_start_str, '%Y-%m-%d').date()
            
            # Calculate the end of the week (Thursday)
            week_end = week_start + timedelta(days=3)
            
            # Get selected students
            selected_students = request.POST.getlist('students[]')
            
            if not selected_students:
                messages.warning(request, "الرجاء اختيار طالب واحد على الأقل.")
                return redirect('plan_generate')
            
            plans_created = 0
            
            for student_id in selected_students:
                try:
                    student = Student.objects.get(id=student_id)
                    
                    # Get current Surah and Ayah from the form
                    current_surah = int(request.POST.get(f'surah_{student_id}', 1))
                    current_ayah = int(request.POST.get(f'ayah_{student_id}', 1))
                    
                    # Check if a plan already exists for this student and week
                    existing_plan = MemorizationPlan.objects.filter(
                        student=student,
                        week_start=week_start
                    ).first()
                    
                    if existing_plan:
                        # Update the existing plan
                        existing_plan.current_surah = current_surah
                        existing_plan.current_ayah = current_ayah
                        existing_plan.target_ayahs_per_day = target_ayahs
                        existing_plan.save()
                        
                        # Clear existing tasks and regenerate
                        existing_plan.dailytask_set.all().delete()
                        generate_daily_tasks_with_review(existing_plan, include_review, review_surah, review_ayah_count)
                        
                        # Log activity
                        Activity.objects.create(
                            user=request.user,
                            description=f"تم تحديث خطة الحفظ للطالب {student.full_name} (أسبوع {week_start.strftime('%Y-%m-%d')})"
                        )
                    else:
                        # Create a new plan
                        plan = MemorizationPlan.objects.create(
                            student=student,
                            week_start=week_start,
                            week_end=week_end,
                            current_surah=current_surah,
                            current_ayah=current_ayah,
                            target_ayahs_per_day=target_ayahs
                        )
                        
                        # Generate daily tasks
                        generate_daily_tasks_with_review(plan, include_review, review_surah, review_ayah_count)
                        
                        # Log activity
                        Activity.objects.create(
                            user=request.user,
                            description=f"تم إنشاء خطة حفظ للطالب {student.full_name} (أسبوع {week_start.strftime('%Y-%m-%d')})"
                        )
                    
                    plans_created += 1
                except Student.DoesNotExist:
                    messages.error(request, f"لم يتم العثور على الطالب رقم {student_id}")
                except Exception as e:
                    messages.error(request, f"خطأ عند معالجة خطة الطالب: {str(e)}")
            
            if plans_created > 0:
                messages.success(request, f"تم إنشاء {plans_created} خطة حفظ بنجاح!")
                return redirect('plan_list')
            else:
                messages.warning(request, "لم يتم إنشاء أي خطط.")
        except Exception as e:
            messages.error(request, f"حدث خطأ أثناء إنشاء الخطط: {str(e)}")
    
    context = {
        'students': students,
        'today': today,
    }
    
    return render(request, 'plans/plan_generate.html', context)

def generate_daily_tasks_with_review(plan, include_review=True, review_surah=0, review_ayah_count=10):
    """
    Custom function to generate daily tasks for a plan with review options
    """
    # Delete any existing tasks for this plan
    plan.dailytask_set.all().delete()
    
    # Get surah and ayah information
    surah_lengths = {
        1: 7,    # الفاتحة
        2: 286,  # البقرة
        3: 200,  # آل عمران
        4: 176,  # النساء
        5: 120,  # المائدة
        6: 165,  # الأنعام
        7: 206,  # الأعراف
        8: 75,   # الأنفال
        9: 129,  # التوبة
        10: 109, # يونس
        11: 123, # هود
        12: 111, # يوسف
        13: 43,  # الرعد
        14: 52,  # إبراهيم
        15: 99,  # الحجر
        16: 128, # النحل
        17: 111, # الإسراء
        18: 110, # الكهف
        19: 98,  # مريم
        20: 135, # طه
        21: 112, # الأنبياء
        22: 78,  # الحج
        23: 118, # المؤمنون
        24: 64,  # النور
        25: 77,  # الفرقان
        26: 227, # الشعراء
        27: 93,  # النمل
        28: 88,  # القصص
        29: 69,  # العنكبوت
        30: 60,  # الروم
        31: 34,  # لقمان
        32: 30,  # السجدة
        33: 73,  # الأحزاب
        34: 54,  # سبأ
        35: 45,  # فاطر
        36: 83,  # يس
        37: 182, # الصافات
        38: 88,  # ص
        39: 75,  # الزمر
        40: 85,  # غافر
        41: 54,  # فصلت
        42: 53,  # الشورى
        43: 89,  # الزخرف
        44: 59,  # الدخان
        45: 37,  # الجاثية
        46: 35,  # الأحقاف
        47: 38,  # محمد
        48: 29,  # الفتح
        49: 18,  # الحجرات
        50: 45,  # ق
        51: 60,  # الذاريات
        52: 49,  # الطور
        53: 62,  # النجم
        54: 55,  # القمر
        55: 78,  # الرحمن
        56: 96,  # الواقعة
        57: 29,  # الحديد
        58: 22,  # المجادلة
        59: 24,  # الحشر
        60: 13,  # الممتحنة
        61: 14,  # الصف
        62: 11,  # الجمعة
        63: 11,  # المنافقون
        64: 18,  # التغابن
        65: 12,  # الطلاق
        66: 12,  # التحريم
        67: 30,  # الملك
        68: 52,  # القلم
        69: 52,  # الحاقة
        70: 44,  # المعارج
        71: 28,  # نوح
        72: 28,  # الجن
        73: 20,  # المزمل
        74: 56,  # المدثر
        75: 40,  # القيامة
        76: 31,  # الإنسان
        77: 50,  # المرسلات
        78: 40,  # النبأ
        79: 46,  # النازعات
        80: 42,  # عبس
        81: 29,  # التكوير
        82: 19,  # الانفطار
        83: 36,  # المطففين
        84: 25,  # الانشقاق
        85: 22,  # البروج
        86: 17,  # الطارق
        87: 19,  # الأعلى
        88: 26,  # الغاشية
        89: 30,  # الفجر
        90: 20,  # البلد
        91: 15,  # الشمس
        92: 21,  # الليل
        93: 11,  # الضحى
        94: 8,   # الشرح
        95: 8,   # التين
        96: 19,  # العلق
        97: 5,   # القدر
        98: 8,   # البينة
        99: 8,   # الزلزلة
        100: 11, # العاديات
        101: 11, # القارعة
        102: 8,  # التكاثر
        103: 3,  # العصر
        104: 9,  # الهمزة
        105: 5,  # الفيل
        106: 4,  # قريش
        107: 7,  # الماعون
        108: 3,  # الكوثر
        109: 6,  # الكافرون
        110: 3,  # النصر
        111: 5,  # المسد
        112: 4,  # الإخلاص
        113: 5,  # الفلق
        114: 6   # الناس
    }
    
    current_surah = plan.current_surah
    current_ayah = plan.current_ayah
    
    # Create tasks for Monday to Thursday
    for i in range(4):
        task_date = plan.week_start + timezone.timedelta(days=i)
        
        # For future plans, we don't need to check attendance
        # We'll just create the tasks and let them be managed later
        # Try-except block removed for future attendance
        
        # Calculate end ayah
        end_ayah = current_ayah + plan.target_ayahs_per_day - 1
        
        # Check if we need to move to the next surah
        if current_surah in surah_lengths and end_ayah > surah_lengths[current_surah]:
            # Calculate remaining ayahs in current surah
            remaining_ayahs = surah_lengths[current_surah] - current_ayah + 1
            
            # Create task for current surah's remaining ayahs
            DailyTask.objects.create(
                plan=plan,
                date=task_date,
                task_type='new',
                surah_start=current_surah,
                ayah_start=current_ayah,
                ayah_end=surah_lengths[current_surah],
                status='pending'
            )
            
            # Move to next surah
            current_surah += 1
            current_ayah = 1
            
            # Create task for beginning of next surah if we have ayahs left to assign
            remaining_target = plan.target_ayahs_per_day - remaining_ayahs
            if remaining_target > 0:
                end_ayah = min(remaining_target, surah_lengths.get(current_surah, 999))
                
                DailyTask.objects.create(
                    plan=plan,
                    date=task_date,
                    task_type='new',
                    surah_start=current_surah,
                    ayah_start=1,
                    ayah_end=end_ayah,
                    status='pending'
                )
                
                current_ayah = end_ayah + 1
        else:
            # Create task within the same surah
            DailyTask.objects.create(
                plan=plan,
                date=task_date,
                task_type='new',
                surah_start=current_surah,
                ayah_start=current_ayah,
                ayah_end=end_ayah,
                status='pending'
            )
            
            current_ayah = end_ayah + 1
        
        # Also create a review task if requested
        if include_review:
            # Determine if the student has memorized enough content to review
            has_previous_memorization = False
            if plan.current_surah > 1:
                has_previous_memorization = True
            elif plan.current_surah == 1 and plan.current_ayah > 10:
                has_previous_memorization = True
            
            if has_previous_memorization:
                # Determine review content based on user selection
                if review_surah == 0:
                    # Use same surah as new memorization (default)
                    review_start = max(1, current_ayah - review_ayah_count)
                    review_surah = current_surah
                    
                    if review_start < 1:
                        # Need to go back to previous surah
                        review_surah -= 1
                        if review_surah in surah_lengths:
                            review_start = max(1, surah_lengths[review_surah] - (review_ayah_count - current_ayah))
                    
                    # End ayah is the last one before the new memorization
                    review_end = current_ayah - 1 if review_surah == current_surah else surah_lengths.get(review_surah, 999)
                else:
                    # Use custom surah for review
                    review_start = 1
                    review_end = min(review_ayah_count, surah_lengths.get(review_surah, 999))
                
                # Create the review task if we have valid values
                if review_end >= review_start and review_surah > 0:
                    DailyTask.objects.create(
                        plan=plan,
                        date=task_date,
                        task_type='review',
                        surah_start=review_surah,
                        ayah_start=review_start,
                        ayah_end=review_end,
                        status='pending'
                    )

@login_required
def plan_cancel(request, plan_id):
    """
    Delete a memorization plan
    """
    plan = get_object_or_404(MemorizationPlan, id=plan_id)
    
    if request.method == 'POST':
        # Get student info before deletion for activity log
        student_name = plan.student.full_name
        plan_week = plan.week_start.strftime('%Y-%m-%d')
        
        # Delete the plan and its associated tasks
        plan.delete()
        
        # Log activity
        Activity.objects.create(
            user=request.user,
            description=f"تم حذف خطة الحفظ للطالب {student_name} (أسبوع {plan_week})"
        )
        
        messages.success(request, "تم حذف خطة الحفظ بنجاح!")
        return redirect('plan_list')
    
    context = {
        'plan': plan,
    }
    
    return render(request, 'plans/plan_cancel.html', context)

@login_required
def task_update(request, task_id):
    """
    Update the status of a daily task
    """
    task = get_object_or_404(DailyTask, id=task_id)
    
    # الحصول على الصفحة التي سيتم إعادة التوجيه إليها
    redirect_page = request.GET.get('redirect', 'plan')
    
    if request.method == 'POST':
        status = request.POST.get('status')
        comments = request.POST.get('comments', '')
        
        task.status = status
        task.comments = comments
        task.save()
        
        # Log activity
        Activity.objects.create(
            user=request.user,
            description=f"Updated task status for {task.plan.student.full_name} to {task.get_status_display()}"
        )
        
        messages.success(request, "Task status has been updated successfully!")
        
        # إعادة التوجيه حسب المعلمة المستلمة
        if redirect_page == 'today':
            return redirect('today_tasks')
        else:
            return redirect('plan_detail', plan_id=task.plan.id)
    
    context = {
        'task': task,
    }
    
    return render(request, 'plans/task_update.html', context)

@login_required
def special_session(request):
    """
    Create a special session (non-memorization task) for students
    """
    # Get all active students
    students = Student.objects.filter(status='active')
    
    if request.method == 'POST':
        with transaction.atomic():
            session_date = request.POST.get('session_date')
            session_type = request.POST.get('session_type')
            description = request.POST.get('description', '')
            
            try:
                session_date = timezone.datetime.strptime(session_date, '%Y-%m-%d').date()
            except ValueError:
                messages.error(request, "Invalid date format. Please use YYYY-MM-DD.")
                return redirect('special_session')
            
            # Get selected students
            selected_students = []
            for student in students:
                if request.POST.get(f'student_{student.id}'):
                    selected_students.append(student)
            
            if not selected_students:
                messages.error(request, "Please select at least one student.")
                return redirect('special_session')
            
            # Find plans for the selected date
            for student in selected_students:
                plans = MemorizationPlan.objects.filter(
                    student=student,
                    week_start__lte=session_date,
                    week_end__gte=session_date
                )
                
                if plans.exists():
                    plan = plans.first()
                    
                    # Cancel any existing tasks for this day
                    DailyTask.objects.filter(
                        plan=plan,
                        date=session_date
                    ).update(status='canceled')
                    
                    # Create the special session task
                    DailyTask.objects.create(
                        plan=plan,
                        date=session_date,
                        task_type=session_type,
                        description=description,
                        status='pending'
                    )
                else:
                    # Create a new plan for this week
                    week_start = session_date - timedelta(days=session_date.weekday())
                    week_end = week_start + timedelta(days=3)
                    
                    plan = MemorizationPlan.objects.create(
                        student=student,
                        week_start=week_start,
                        week_end=week_end,
                        current_surah=1,
                        current_ayah=1,
                        target_ayahs_per_day=5
                    )
                    
                    # Create the special session task
                    DailyTask.objects.create(
                        plan=plan,
                        date=session_date,
                        task_type=session_type,
                        description=description,
                        status='pending'
                    )
            
            # Log activity
            Activity.objects.create(
                user=request.user,
                description=f"Created special session '{DailyTask.TASK_TYPE_CHOICES[session_type][1]}' for {len(selected_students)} students on {session_date.strftime('%Y-%m-%d')}"
            )
            
            messages.success(request, "Special session has been created successfully!")
            return redirect('plan_list')
    
    context = {
        'students': students,
        'session_types': DailyTask.TASK_TYPE_CHOICES[2:],  # Exclude 'new' and 'review'
    }
    
    return render(request, 'plans/special_session.html', context)

@login_required
def task_add(request, plan_id):
    """
    إضافة مهمة جديدة للخطة
    """
    plan = get_object_or_404(MemorizationPlan, id=plan_id)
    
    if request.method == 'POST':
        task_date = request.POST.get('task_date')
        task_type = request.POST.get('task_type')
        
        try:
            task_date = timezone.datetime.strptime(task_date, '%Y-%m-%d').date()
            
            # التحقق من أن التاريخ ضمن نطاق الخطة
            if task_date < plan.week_start or task_date > plan.week_end:
                messages.error(request, "التاريخ المحدد خارج نطاق فترة الخطة.")
                return redirect('plan_detail', plan_id=plan.id)
            
            # إنشاء المهمة بناءً على النوع
            if task_type in ['new', 'review']:
                surah_start = int(request.POST.get('surah_start', 1))
                ayah_start = int(request.POST.get('ayah_start', 1))
                ayah_end = int(request.POST.get('ayah_end', 1))
                
                # التحقق من أن الآية النهائية أكبر من أو تساوي الآية البدائية
                if ayah_end < ayah_start:
                    messages.error(request, "الآية النهائية يجب أن تكون أكبر من أو تساوي الآية البدائية.")
                    return redirect('plan_detail', plan_id=plan.id)
                
                # إنشاء المهمة
                DailyTask.objects.create(
                    plan=plan,
                    date=task_date,
                    task_type=task_type,
                    surah_start=surah_start,
                    ayah_start=ayah_start,
                    ayah_end=ayah_end,
                    status='pending'
                )
            else:
                description = request.POST.get('description', '')
                
                # وضع وصف افتراضي إذا كان فارغاً
                if not description:
                    if task_type == 'tajweed':
                        description = 'درس في أحكام التجويد'
                    elif task_type == 'fiqh':
                        description = 'درس في فقه العبادات'
                    elif task_type == 'jibal':
                        description = 'درس يا جبال أوبي'
                
                # إنشاء المهمة
                DailyTask.objects.create(
                    plan=plan,
                    date=task_date,
                    task_type=task_type,
                    description=description,
                    status='pending'
                )
            
            # تسجيل النشاط
            Activity.objects.create(
                user=request.user,
                description=f"تمت إضافة مهمة جديدة للطالب {plan.student.full_name} بتاريخ {task_date.strftime('%Y-%m-%d')}"
            )
            
            messages.success(request, "تمت إضافة المهمة بنجاح.")
            
        except ValueError as e:
            messages.error(request, f"خطأ في البيانات المدخلة: {str(e)}")
        except Exception as e:
            messages.error(request, f"حدث خطأ أثناء إضافة المهمة: {str(e)}")
    
    # إعادة التوجيه إلى صفحة تفاصيل الخطة مع تحديث البيانات
    return redirect('plan_detail', plan_id=plan.id)

@login_required
def today_tasks(request):
    """
    عرض مهام اليوم لجميع الطلاب
    """
    today = timezone.now().date()
    
    # الحصول على جميع المهام المتعلقة بتاريخ اليوم
    tasks = DailyTask.objects.filter(
        date=today,
        status__in=['pending', 'in_progress']  # فقط المهام المعلقة أو قيد التنفيذ
    ).order_by(
        'plan__student__full_name',
        models.Case(
            models.When(task_type='new', then=models.Value(1)),
            models.When(task_type='review', then=models.Value(2)),
            default=models.Value(3),
            output_field=models.IntegerField(),
        )
    )
    
    # البحث - يمكن تصفية المهام حسب الطالب
    student_filter = request.GET.get('student_id')
    if student_filter:
        tasks = tasks.filter(plan__student_id=student_filter)
    
    # الحصول على جميع الطلاب النشطين للفلتر
    students = Student.objects.filter(status='active')
    
    context = {
        'today': today,
        'tasks': tasks,
        'students': students,
        'selected_student_id': student_filter,
    }
    
    return render(request, 'plans/today_tasks.html', context)

@login_required
def export_plan_as_image(request, plan_id):
    """
    Export plan as an image for sharing with parents
    """
    plan = get_object_or_404(MemorizationPlan, id=plan_id)
    
    # Get daily tasks
    daily_tasks = DailyTask.objects.filter(plan=plan).order_by('date', 
                                                           models.Case(
                                                               models.When(task_type='new', then=models.Value(1)),
                                                               models.When(task_type='review', then=models.Value(2)),
                                                               default=models.Value(3),
                                                               output_field=models.IntegerField(),
                                                           ))
    
    # Render the template to string
    html_string = render_to_string('plans/plan_pdf.html', {
        'plan': plan,
        'daily_tasks': daily_tasks,
        'student': plan.student,
    })
    
    # Create WeasyPrint HTML object
    html = HTML(string=html_string, base_url=request.build_absolute_uri('/'))
    
    # Add custom CSS
    css = CSS(string='''
        @page {
            size: A4;
            margin: 1cm;
            @top-center {
                content: "الخطة الأسبوعية";
                font-weight: bold;
            }
            @bottom-center {
                content: "نظام ادارة حلقة رشيد الهبشي";
            }
        }
        body {
            font-family: 'Tajawal', sans-serif;
            direction: rtl;
            text-align: right;
        }
        .student-info {
            margin-bottom: 20px;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 5px;
            background-color: #f5f5f5;
        }
        .plan-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }
        .plan-table th, .plan-table td {
            border: 1px solid #ddd;
            padding: 8px;
            text-align: right;
        }
        .plan-table th {
            background-color: #05668D;
            color: white;
        }
        .plan-table tr:nth-child(even) {
            background-color: #f2f2f2;
        }
    ''')
    
    # Generate PDF
    pdf_file = html.write_pdf(stylesheets=[css])
    
    # Create HTTP response with PDF
    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="plan_{plan.student.full_name}_{plan.week_start}.pdf"'
    
    # Log activity
    Activity.objects.create(
        user=request.user,
        description=f"تم تصدير خطة الحفظ للطالب {plan.student.full_name} لأسبوع {plan.week_start}"
    )
    
    return response

@login_required
def export_all_plans(request, week_start=None):
    """
    Export all plans for a specific week as one PDF
    """
    # Get the week start date
    if week_start:
        try:
            start_date = timezone.datetime.strptime(week_start, '%Y-%m-%d').date()
        except ValueError:
            start_date = date.today() - timedelta(days=date.today().weekday())
    else:
        # Default to current week
        start_date = date.today() - timedelta(days=date.today().weekday())
    
    # Get all plans for this week
    plans = MemorizationPlan.objects.filter(week_start=start_date)
    
    if not plans.exists():
        messages.warning(request, "لا توجد خطط للأسبوع المحدد.")
        return redirect('plan_list')
    
    # Render the template to string
    html_string = render_to_string('plans/all_plans_pdf.html', {
        'plans': plans,
        'week_start': start_date,
        'week_end': start_date + timedelta(days=3)
    })
    
    # Create WeasyPrint HTML object
    html = HTML(string=html_string, base_url=request.build_absolute_uri('/'))
    
    # Add custom CSS
    css = CSS(string='''
        @page {
            size: A4;
            margin: 1cm;
            @top-center {
                content: "خطط الحفظ الأسبوعية";
                font-weight: bold;
            }
            @bottom-center {
                content: "نظام ادارة حلقة رشيد الهبشي";
            }
        }
        body {
            font-family: 'Tajawal', sans-serif;
            direction: rtl;
            text-align: right;
        }
        .plan {
            margin-bottom: 30px;
            page-break-inside: avoid;
        }
        .student-info {
            margin-bottom: 20px;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 5px;
            background-color: #f5f5f5;
        }
        .plan-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }
        .plan-table th, .plan-table td {
            border: 1px solid #ddd;
            padding: 8px;
            text-align: right;
        }
        .plan-table th {
            background-color: #05668D;
            color: white;
        }
        .plan-table tr:nth-child(even) {
            background-color: #f2f2f2;
        }
        .page-break {
            page-break-after: always;
        }
    ''')
    
    # Generate PDF
    pdf_file = html.write_pdf(stylesheets=[css])
    
    # Create HTTP response with PDF
    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="all_plans_{start_date}.pdf"'
    
    # Log activity
    Activity.objects.create(
        user=request.user,
        description=f"تم تصدير جميع خطط الحفظ لأسبوع {start_date}"
    )
    
    return response
