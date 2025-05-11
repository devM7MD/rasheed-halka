from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.utils import timezone
from django.db import transaction
from django.db.models import Avg, Max, Min

from .models import Evaluation
from students.models import Student
from core.models import Activity

import csv
import calendar
from datetime import date, datetime
import io
from collections import defaultdict

@login_required
def evaluation_list(request):
    """
    Display a list of student evaluations
    """
    # Get filter parameters
    student_id = request.GET.get('student_id')
    month = request.GET.get('month', date.today().month)
    year = request.GET.get('year', date.today().year)
    
    try:
        month = int(month)
        year = int(year)
    except ValueError:
        month = date.today().month
        year = date.today().year
    
    # Get evaluations for the selected month
    evaluations = Evaluation.get_evaluations_for_month(year, month)
    
    # Apply student filter if selected
    if student_id:
        evaluations = evaluations.filter(student_id=student_id)
    
    # Get students for the filter dropdown
    students = Student.objects.filter(status='active')
    
    # Get available months and years for filter dropdowns
    dates = Evaluation.objects.dates('date', 'month', order='DESC')
    months = list(set([(date.month, calendar.month_name[date.month]) for date in dates]))
    years = list(set([date.year for date in dates]))
    
    # If no evaluations exist yet, add current month and year
    if not months:
        current_month = date.today().month
        months.append((current_month, calendar.month_name[current_month]))
        years.append(date.today().year)
    
    context = {
        'evaluations': evaluations,
        'students': students,
        'months': sorted(months),
        'years': sorted(years, reverse=True),
        'selected_month': month,
        'selected_year': year,
        'selected_student_id': student_id,
        'month_name': calendar.month_name[month],
    }
    
    return render(request, 'evaluations/evaluation_list.html', context)

@login_required
def evaluation_add(request):
    """
    Add a new evaluation for a student
    """
    # Get all active students
    students = Student.objects.filter(status='active')
    
    if request.method == 'POST':
        student_id = request.POST.get('student')
        eval_date = request.POST.get('date')
        old_memorization = request.POST.get('old_memorization_score')
        new_memorization = request.POST.get('new_memorization_score')
        behavior = request.POST.get('behavior_score')
        activity = request.POST.get('activity_score')
        comments = request.POST.get('comments', '')
        
        try:
            # Validate inputs
            student = get_object_or_404(Student, id=student_id)
            eval_date = datetime.strptime(eval_date, '%Y-%m-%d').date()
            old_memorization = int(old_memorization)
            new_memorization = int(new_memorization)
            behavior = int(behavior)
            activity = int(activity)
            
            # Check if an evaluation already exists for this student and date
            if Evaluation.objects.filter(student=student, date=eval_date).exists():
                messages.error(request, f"An evaluation already exists for {student.full_name} on {eval_date.strftime('%Y-%m-%d')}")
                return redirect('evaluation_add')
            
            # Create the evaluation
            evaluation = Evaluation.objects.create(
                student=student,
                date=eval_date,
                old_memorization_score=old_memorization,
                new_memorization_score=new_memorization,
                behavior_score=behavior,
                activity_score=activity,
                comments=comments
            )
            
            # Log activity
            Activity.objects.create(
                user=request.user,
                description=f"Added evaluation for {student.full_name} (Grade: {evaluation.get_final_grade()})"
            )
            
            messages.success(request, f"Evaluation for {student.full_name} has been added successfully!")
            return redirect('evaluation_list')
            
        except ValueError as e:
            messages.error(request, f"Invalid input: {str(e)}")
        except Exception as e:
            messages.error(request, f"Error adding evaluation: {str(e)}")
    
    context = {
        'students': students,
        'today': date.today(),
    }
    
    return render(request, 'evaluations/evaluation_form.html', context)

@login_required
def evaluation_edit(request, evaluation_id):
    """
    Edit an existing evaluation
    """
    evaluation = get_object_or_404(Evaluation, id=evaluation_id)
    
    if request.method == 'POST':
        try:
            # Get form values
            old_memorization = int(request.POST.get('old_memorization_score'))
            new_memorization = int(request.POST.get('new_memorization_score'))
            behavior = int(request.POST.get('behavior_score'))
            activity = int(request.POST.get('activity_score'))
            comments = request.POST.get('comments', '')
            
            # Update evaluation
            evaluation.old_memorization_score = old_memorization
            evaluation.new_memorization_score = new_memorization
            evaluation.behavior_score = behavior
            evaluation.activity_score = activity
            evaluation.comments = comments
            evaluation.save()
            
            # Log activity
            Activity.objects.create(
                user=request.user,
                description=f"Updated evaluation for {evaluation.student.full_name} (Grade: {evaluation.get_final_grade()})"
            )
            
            messages.success(request, f"Evaluation for {evaluation.student.full_name} has been updated successfully!")
            return redirect('evaluation_list')
            
        except ValueError as e:
            messages.error(request, f"Invalid input: {str(e)}")
        except Exception as e:
            messages.error(request, f"Error updating evaluation: {str(e)}")
    
    context = {
        'evaluation': evaluation,
    }
    
    return render(request, 'evaluations/evaluation_edit.html', context)

@login_required
def evaluation_delete(request, evaluation_id):
    """
    Delete an evaluation
    """
    evaluation = get_object_or_404(Evaluation, id=evaluation_id)
    
    if request.method == 'POST':
        student_name = evaluation.student.full_name
        evaluation.delete()
        
        # Log activity
        Activity.objects.create(
            user=request.user,
            description=f"Deleted evaluation for {student_name}"
        )
        
        messages.success(request, f"Evaluation for {student_name} has been deleted successfully!")
        return redirect('evaluation_list')
    
    context = {
        'evaluation': evaluation,
    }
    
    return render(request, 'evaluations/evaluation_confirm_delete.html', context)

@login_required
def evaluation_report(request):
    """
    Generate evaluation reports
    """
    # Get report parameters
    report_type = request.GET.get('type', 'monthly')
    export_format = request.GET.get('format', None)
    month = request.GET.get('month', date.today().month)
    year = request.GET.get('year', date.today().year)
    
    try:
        month = int(month)
        year = int(year)
    except ValueError:
        month = date.today().month
        year = date.today().year
    
    # Get evaluations based on report type
    if report_type == 'monthly':
        evaluations = Evaluation.get_evaluations_for_month(year, month)
        title = f"Monthly Evaluation Report: {calendar.month_name[month]} {year}"
    else:  # student
        student_id = request.GET.get('student_id')
        if student_id:
            student = get_object_or_404(Student, id=student_id)
            evaluations = Evaluation.objects.filter(student=student).order_by('-date')
            title = f"Student Evaluation Report: {student.full_name}"
        else:
            evaluations = Evaluation.objects.all().order_by('-date')
            title = "All Students Evaluation Report"
    
    # Prepare statistics
    stats = {}
    avg_old_memorization = 0
    avg_new_memorization = 0
    avg_behavior = 0
    avg_activity = 0
    avg_percentage = 0
    total_evaluations = evaluations.count()
    student_evaluations = []
    
    if evaluations:
        # Calculate global averages
        avg_old_memorization = evaluations.aggregate(Avg('old_memorization_score'))['old_memorization_score__avg'] or 0
        avg_new_memorization = evaluations.aggregate(Avg('new_memorization_score'))['new_memorization_score__avg'] or 0
        avg_behavior = evaluations.aggregate(Avg('behavior_score'))['behavior_score__avg'] or 0
        avg_activity = evaluations.aggregate(Avg('activity_score'))['activity_score__avg'] or 0
        
        # Calculate average total and percentage
        avg_total = avg_old_memorization + avg_new_memorization + avg_behavior + avg_activity
        avg_percentage = (avg_total / 40.0) * 100
        
        stats['avg_total'] = evaluations.aggregate(
            total=Avg('old_memorization_score') + Avg('new_memorization_score') + 
                  Avg('behavior_score') + Avg('activity_score')
        )['total']
        
        stats['avg_memorization'] = evaluations.aggregate(
            memorization=Avg('old_memorization_score') + Avg('new_memorization_score')
        )['memorization']
        
        stats['avg_behavior'] = avg_behavior
        stats['avg_activity'] = avg_activity
        stats['highest_total'] = max([e.get_total_score() for e in evaluations])
        stats['lowest_total'] = min([e.get_total_score() for e in evaluations])
        
        # Group evaluations by student
        student_data = {}
        
        for evaluation in evaluations:
            student_id = evaluation.student.id
            student_name = evaluation.student.full_name
            
            if student_id not in student_data:
                student_data[student_id] = {
                    'name': student_name,
                    'evaluations': [],
                }
            
            student_data[student_id]['evaluations'].append(evaluation)
        
        # Calculate averages for each student
        for student_id, data in student_data.items():
            evals = data['evaluations']
            eval_count = len(evals)
            
            # Calculate student averages
            student_avg_old = sum(e.old_memorization_score for e in evals) / eval_count
            student_avg_new = sum(e.new_memorization_score for e in evals) / eval_count
            student_avg_behavior = sum(e.behavior_score for e in evals) / eval_count
            student_avg_activity = sum(e.activity_score for e in evals) / eval_count
            
            # Calculate average total and percentage
            student_avg_total = student_avg_old + student_avg_new + student_avg_behavior + student_avg_activity
            student_avg_percentage = (student_avg_total / 40.0) * 100
            
            student_evaluations.append({
                'name': data['name'],
                'evaluation_count': eval_count,
                'avg_old_memorization': student_avg_old,
                'avg_new_memorization': student_avg_new,
                'avg_behavior': student_avg_behavior,
                'avg_activity': student_avg_activity,
                'avg_total': student_avg_total,
                'avg_percentage': student_avg_percentage,
            })
    
    # Get students for the filter dropdown
    students = Student.objects.filter(status='active')
    
    # Get available months and years for filter dropdowns
    dates = Evaluation.objects.dates('date', 'month', order='DESC')
    months = list(set([(date.month, calendar.month_name[date.month]) for date in dates]))
    years = list(set([date.year for date in dates]))
    
    # If no evaluations exist yet, add current month and year
    if not months:
        current_month = date.today().month
        months.append((current_month, calendar.month_name[current_month]))
        years.append(date.today().year)
    
    # Export data if requested
    if export_format and export_format == 'csv':
        return export_evaluations_csv(evaluations, title, report_type)
    
    context = {
        'title': title,
        'evaluations': evaluations,
        'report_type': report_type,
        'stats': stats,
        'students': students,
        'months': sorted(months),
        'years': sorted(years, reverse=True),
        'selected_month': month,
        'selected_year': year,
        'selected_student_id': request.GET.get('student_id'),
        # Add missing context variables
        'total_evaluations': total_evaluations,
        'avg_old_memorization': avg_old_memorization,
        'avg_new_memorization': avg_new_memorization,
        'avg_behavior': avg_behavior,
        'avg_activity': avg_activity,
        'avg_percentage': avg_percentage,
        'student_evaluations': student_evaluations,
        'month_name': calendar.month_name[month],
    }
    
    return render(request, 'evaluations/evaluation_report.html', context)

def export_evaluations_csv(evaluations, title, report_type):
    """
    Export evaluations data as CSV
    """
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{title.replace(" ", "_")}.csv"'
    
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    
    # Write header row
    header = ['Student Name', 'Date', 'Old Memorization', 'New Memorization',
              'Behavior', 'Activity', 'Total Score', 'Percentage', 'Grade']
    writer.writerow(header)
    
    # Write data rows
    for evaluation in evaluations:
        row = [
            evaluation.student.full_name,
            evaluation.date.strftime('%Y-%m-%d'),
            evaluation.old_memorization_score,
            evaluation.new_memorization_score,
            evaluation.behavior_score,
            evaluation.activity_score,
            evaluation.get_total_score(),
            f"{evaluation.get_percentage():.1f}%",
            evaluation.get_final_grade()
        ]
        writer.writerow(row)
    
    response.write(buffer.getvalue())
    return response
