from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.utils import timezone
from django.db import transaction
from django.core.exceptions import ValidationError
from django.urls import reverse

from .models import Attendance
from students.models import Student
from core.models import Activity

import csv
import calendar
from datetime import date, datetime, timedelta
import io
from collections import defaultdict

@login_required
def attendance_list(request):
    """
    Display a list of attendance records with filtering options
    """
    # Get today's date
    today = date.today()
    
    # Get filter parameters
    date_filter = request.GET.get('date', '')
    status_filter = request.GET.get('status', 'all')
    search_query = request.GET.get('q', '')
    
    # Base queryset
    records = Attendance.objects.all().order_by('-date', 'student__full_name')
    
    # Apply date filter if provided
    if date_filter:
        try:
            filter_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
            records = records.filter(date=filter_date)
        except ValueError:
            filter_date = today
            # If date is invalid, we still want to set it for the template
            date_filter = today.strftime('%Y-%m-%d')
    else:
        filter_date = None
    
    # Apply status filter if not 'all'
    if status_filter != 'all':
        records = records.filter(status=status_filter)
    
    # Apply search filter if provided
    if search_query:
        records = records.filter(student__full_name__icontains=search_query)
    
    # If there are no records after filtering, show a message
    if not records.exists():
        messages.info(request, "لا توجد سجلات حضور مطابقة للمعايير المحددة.")
    
    context = {
        'records': records,
        'filter_date': filter_date,
        'status_filter': status_filter,
        'search_query': search_query,
        'today': today,
    }
    
    return render(request, 'attendance/attendance_list.html', context)

@login_required
def attendance_today(request):
    """
    Display and handle attendance marking for today
    """
    today = date.today()
    weekday = today.weekday()
    
    # Check if today is a working day (Mon-Thu = 0-3)
    is_working_day = weekday <= 3
    
    # Get all active students
    students = Student.objects.filter(status='active')
    
    # Get any existing attendance records for today
    existing_attendance = Attendance.objects.filter(date=today)
    
    # Create a dictionary to easily look up existing records
    attendance_dict = {attendance.student.id: attendance for attendance in existing_attendance}
    
    # Prepare attendance records for the template
    attendance_records = []
    for student in students:
        if student.id in attendance_dict:
            # Use existing record
            attendance_records.append(attendance_dict[student.id])
        else:
            # Create a temporary record (not saved to database)
            temp_record = Attendance(
                student=student,
                date=today,
                status='present'  # Default to present
            )
            attendance_records.append(temp_record)
    
    if request.method == 'POST':
        with transaction.atomic():
            for student in students:
                status = request.POST.get(f'status_{student.id}', 'absent')
                notes = request.POST.get(f'notes_{student.id}', '')
                
                # Check if there's an existing record
                if student.id in attendance_dict:
                    # Update existing record
                    attendance = attendance_dict[student.id]
                    attendance.status = status
                    attendance.notes = notes
                    attendance.save()
                else:
                    # Create new record
                    try:
                        attendance = Attendance(
                            student=student,
                            date=today,
                            status=status,
                            notes=notes
                        )
                        attendance.full_clean()  # Run validation
                        attendance.save()
                    except ValidationError as e:
                        messages.error(request, f"Error marking attendance for {student.full_name}: {e}")
                        continue
            
            # Log activity
            Activity.objects.create(
                user=request.user,
                description=f"Marked attendance for {today.strftime('%Y-%m-%d')}"
            )
            
            messages.success(request, f"Attendance for {today.strftime('%Y-%m-%d')} has been recorded successfully!")
        
        return redirect('attendance_list')
    
    context = {
        'date': today,
        'attendance_records': attendance_records,
        'is_working_day': is_working_day,
        'day_name': calendar.day_name[weekday],
    }
    
    return render(request, 'attendance/attendance_mark.html', context)

@login_required
def attendance_edit(request, attendance_id):
    """
    Edit an existing attendance record
    """
    attendance = get_object_or_404(Attendance, id=attendance_id)
    
    if request.method == 'POST':
        status = request.POST.get('status')
        notes = request.POST.get('notes', '')
        
        attendance.status = status
        attendance.notes = notes
        attendance.save()
        
        # Log activity
        Activity.objects.create(
            user=request.user,
            description=f"Updated attendance for {attendance.student.full_name} on {attendance.date.strftime('%Y-%m-%d')}"
        )
        
        messages.success(request, "Attendance record has been updated successfully!")
        return redirect('attendance_list')
    
    context = {
        'attendance': attendance,
    }
    
    return render(request, 'attendance/attendance_edit.html', context)

@login_required
def attendance_edit_date(request):
    """
    تعديل سجلات الحضور لتاريخ معين
    """
    today = date.today()
    
    # الحصول على التاريخ المطلوب من الاستعلام
    date_param = request.GET.get('date', today.strftime('%Y-%m-%d'))
    
    try:
        selected_date = datetime.strptime(date_param, '%Y-%m-%d').date()
    except ValueError:
        selected_date = today
    
    # جلب الطلاب النشطين
    students = Student.objects.filter(status='active')
    
    # جلب سجلات الحضور الموجودة للتاريخ المحدد
    existing_attendance = Attendance.objects.filter(date=selected_date)
    
    # إنشاء قاموس للوصول السريع للسجلات الموجودة
    attendance_dict = {attendance.student.id: attendance for attendance in existing_attendance}
    
    # إعداد سجلات الحضور للقالب
    attendance_records = []
    for student in students:
        if student.id in attendance_dict:
            # استخدام السجل الموجود
            attendance_records.append(attendance_dict[student.id])
        else:
            # إنشاء سجل مؤقت (غير محفوظ في قاعدة البيانات)
            temp_record = Attendance(
                student=student,
                date=selected_date,
                status='absent'  # الغياب هو الافتراضي للتواريخ السابقة
            )
            attendance_records.append(temp_record)
    
    if request.method == 'POST':
        # إنشاء قائمة لتتبع التغييرات
        changes_made = 0
        errors_occurred = 0
        
        try:
            with transaction.atomic():
                for student in students:
                    student_id = student.id
                    status = request.POST.get(f'status_{student_id}', 'absent')
                    notes = request.POST.get(f'notes_{student_id}', '')
                    
                    # التحقق من وجود سجل
                    if student_id in attendance_dict:
                        # تحديث السجل الموجود
                        attendance = attendance_dict[student_id]
                        # تحقق مما إذا كان هناك تغيير فعلي
                        if attendance.status != status or attendance.notes != notes:
                            attendance.status = status
                            attendance.notes = notes
                            attendance.save()
                            changes_made += 1
                    else:
                        # إنشاء سجل جديد
                        try:
                            attendance = Attendance(
                                student=student,
                                date=selected_date,
                                status=status,
                                notes=notes
                            )
                            # تخطي التحقق لتواريخ الماضي (السماح بإضافة حضور لأيام غير أيام العمل)
                            if selected_date < today:
                                attendance.save()
                            else:
                                attendance.full_clean()  # تشغيل التحقق
                                attendance.save()
                            changes_made += 1
                        except ValidationError as e:
                            errors_occurred += 1
                            error_message = str(e)
                            # تحقق مما إذا كان الخطأ بسبب يوم غير عمل
                            if "Attendance can only be marked for working days" in error_message:
                                # إذا كان الخطأ بسبب يوم غير عمل، فقم بحفظه على أي حال
                                attendance.save(force_insert=True)
                                changes_made += 1
                            else:
                                messages.error(request, f"خطأ في تسجيل حضور {student.full_name}: {error_message}")
                                continue
                
                # تسجيل النشاط فقط إذا تم إجراء تغييرات
                if changes_made > 0:
                    Activity.objects.create(
                        user=request.user,
                        description=f"تم تعديل سجل الحضور لتاريخ {selected_date.strftime('%Y-%m-%d')} ({changes_made} تغييرات)"
                    )
                    messages.success(request, f"تم تسجيل الحضور لتاريخ {selected_date.strftime('%Y-%m-%d')} بنجاح! ({changes_made} تغييرات)")
                else:
                    messages.info(request, f"لم يتم إجراء أي تغييرات على سجل الحضور لتاريخ {selected_date.strftime('%Y-%m-%d')}")
                
                if errors_occurred > 0:
                    messages.warning(request, f"حدثت {errors_occurred} أخطاء أثناء معالجة بعض السجلات.")
        
        except Exception as e:
            messages.error(request, f"حدث خطأ أثناء حفظ سجلات الحضور: {str(e)}")
        
        # إعادة تحميل الصفحة بدلاً من الانتقال إلى قائمة الحضور
        return redirect(reverse('attendance_edit_date') + f"?date={selected_date.strftime('%Y-%m-%d')}")
    
    # الحصول على التقويم لعرض 14 يوم سابق للاختيار
    calendar_dates = []
    for i in range(14):
        day = today - timedelta(days=i)
        # إضافة أيام العمل فقط (الاثنين-الخميس)
        if day.weekday() <= 3:  # 0-3 هي الاثنين إلى الخميس
            calendar_dates.append(day)
    
    context = {
        'date': selected_date,
        'attendance_records': attendance_records,
        'calendar_dates': calendar_dates,
        'day_name': calendar.day_name[selected_date.weekday()],
    }
    
    return render(request, 'attendance/attendance_edit_date.html', context)

@login_required
def attendance_report(request):
    """
    Generate and display attendance reports
    """
    today = date.today()
    current_year = today.year
    current_month = today.month
    
    # Get parameters from request
    selected_month = int(request.GET.get('month', current_month))
    selected_year = int(request.GET.get('year', current_year))
    
    # Get list of years for dropdown (current year and two previous years)
    years = range(current_year - 2, current_year + 1)
    
    # Get month name
    month_name = calendar.month_name[selected_month]
    
    # Get all working days in the month (Mon-Thu)
    working_days = []
    calendar_days = []  # All days for calendar view
    month_range = calendar.monthrange(selected_year, selected_month)
    total_days = 0
    
    for day in range(1, month_range[1] + 1):
        current_date = date(selected_year, selected_month, day)
        # Add all days to calendar
        calendar_days.append({
            'date': current_date,
            'day': day,
            'weekday': current_date.weekday()
        })
        
        # Count only working days (Mon-Thu) for statistics
        if current_date.weekday() <= 3:  # 0-3 هي الاثنين إلى الخميس
            working_days.append(current_date)
            total_days += 1
    
    # Get active students
    students = Student.objects.filter(status='active')
    
    # Get attendance records for the month
    start_date = date(selected_year, selected_month, 1)
    if selected_month == 12:
        end_date = date(selected_year + 1, 1, 1) - timedelta(days=1)
    else:
        end_date = date(selected_year, selected_month + 1, 1) - timedelta(days=1)
    
    attendance_records = Attendance.objects.filter(
        date__range=[start_date, end_date]
    ).select_related('student')
    
    # Count totals for calculating percentages
    total_present = 0
    total_absent = 0
    total_excused = 0
    
    # Create student attendance data
    student_attendance = []
    calendar_data = []
    
    for student in students:
        student_records = [record for record in attendance_records if record.student_id == student.id]
        
        # Count for this student
        present = len([r for r in student_records if r.status == 'present'])
        absent = len([r for r in student_records if r.status == 'absent'])
        excused = len([r for r in student_records if r.status == 'excused'])
        
        # Add to totals
        total_present += present
        total_absent += absent
        total_excused += excused
        
        # Calculate attendance rate
        total_student_days = present + absent + excused
        attendance_rate = round((present / total_student_days) * 100) if total_student_days > 0 else 0
        
        # Add to student attendance list
        student_attendance.append({
            'student': student,
            'present': present,
            'absent': absent,
            'excused': excused,
            'attendance_rate': attendance_rate
        })
        
        # Create calendar data for this student
        calendar_student = {
            'name': student.full_name,
            'days': []
        }
        
        # Map attendance records by date for easy lookup
        record_by_date = {record.date: record for record in student_records}
        
        # Add status for each day in the month
        for day_info in calendar_days:
            day_date = day_info['date']
            if day_date in record_by_date:
                record = record_by_date[day_date]
                calendar_student['days'].append({
                    'status': record.status,
                    'is_weekend': day_info['weekday'] > 3
                })
            else:
                calendar_student['days'].append({
                    'status': None,
                    'is_weekend': day_info['weekday'] > 3
                })
        
        calendar_data.append(calendar_student)
    
    # Calculate overall percentages
    total_days_all = total_present + total_absent + total_excused
    present_percentage = round((total_present / total_days_all) * 100) if total_days_all > 0 else 0
    absent_percentage = round((total_absent / total_days_all) * 100) if total_days_all > 0 else 0
    excused_percentage = round((total_excused / total_days_all) * 100) if total_days_all > 0 else 0
    
    context = {
        'selected_month': selected_month,
        'selected_year': selected_year,
        'month_name': month_name,
        'years': years,
        'working_days': working_days,
        'calendar_days': calendar_days,
        'total_days': total_days,
        'student_attendance': student_attendance,
        'calendar_data': calendar_data,
        'present_percentage': present_percentage,
        'absent_percentage': absent_percentage,
        'excused_percentage': excused_percentage,
        'total_present': total_present,
        'total_absent': total_absent,
        'total_excused': total_excused,
        'total_days_all': total_days_all,
    }
    
    return render(request, 'attendance/attendance_report.html', context)

def export_attendance_csv(report_data, title, report_type, working_days=None):
    """
    Export attendance data as CSV
    """
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{title.replace(" ", "_")}.csv"'
    
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    
    # Write header row
    header = ['Student Name']
    
    if report_type == 'weekly':
        # Add days of the week (Mon-Thu)
        for i in range(4):
            day = (report_data[list(report_data.keys())[0]]['student'].week_start + timedelta(days=i)).strftime('%Y-%m-%d')
            header.append(day)
    else:  # monthly
        # Add all working days in the month
        for day in working_days:
            header.append(day.strftime('%Y-%m-%d'))
    
    header.append('Present')
    header.append('Absent')
    header.append('Excused')
    header.append('Attendance Rate (%)')
    
    writer.writerow(header)
    
    # Write data rows
    for student_id, data in report_data.items():
        student = data['student']
        row = [student.full_name]
        
        present_count = 0
        absent_count = 0
        excused_count = 0
        
        if report_type == 'weekly':
            # Add status for each day of the week
            for i in range(4):
                day = (student.week_start + timedelta(days=i)).strftime('%Y-%m-%d')
                if day in data['days']:
                    attendance = data['days'][day]
                    row.append(attendance.get_status_display())
                    
                    if attendance.status == 'present':
                        present_count += 1
                    elif attendance.status == 'absent':
                        absent_count += 1
                    elif attendance.status == 'excused':
                        excused_count += 1
                else:
                    row.append('-')
        else:  # monthly
            # Add status for each working day
            for day in working_days:
                day_str = day.strftime('%Y-%m-%d')
                if day_str in data['days']:
                    attendance = data['days'][day_str]
                    row.append(attendance.get_status_display())
                    
                    if attendance.status == 'present':
                        present_count += 1
                    elif attendance.status == 'absent':
                        absent_count += 1
                    elif attendance.status == 'excused':
                        excused_count += 1
                else:
                    row.append('-')
        
        # Add summary statistics
        row.append(present_count)
        row.append(absent_count)
        row.append(excused_count)
        
        # Calculate attendance rate
        total_days = present_count + absent_count + excused_count
        if total_days > 0:
            attendance_rate = (present_count / total_days) * 100
            row.append(f"{attendance_rate:.1f}%")
        else:
            row.append('0.0%')
        
        writer.writerow(row)
    
    response.write(buffer.getvalue())
    return response
