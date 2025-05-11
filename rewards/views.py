from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from .models import PointsEntry, Reward, RewardCatalog
from students.models import Student
from core.models import Activity

@login_required
def student_rewards(request, student_id):
    """
    Display rewards and points for a specific student
    """
    student = get_object_or_404(Student, id=student_id)
    
    # Get all points entries for this student
    points_entries = PointsEntry.objects.filter(student=student)
    rewards = Reward.objects.filter(student=student)
    
    # Calculate total points
    total_points_earned = points_entries.aggregate(Sum('points'))['points__sum'] or 0
    total_points_spent = rewards.aggregate(Sum('points_cost'))['points_cost__sum'] or 0
    total_points = total_points_earned - total_points_spent
    
    # Calculate points by type
    point_types = {
        'memorization': points_entries.filter(points_type='memorization').aggregate(Sum('points'))['points__sum'] or 0,
        'review': points_entries.filter(points_type='review').aggregate(Sum('points'))['points__sum'] or 0,
        'attendance': points_entries.filter(points_type='attendance').aggregate(Sum('points'))['points__sum'] or 0,
        'behavior': points_entries.filter(points_type='behavior').aggregate(Sum('points'))['points__sum'] or 0,
        'activities': points_entries.filter(points_type='activities').aggregate(Sum('points'))['points__sum'] or 0,
    }
    
    # Get upcoming rewards from catalog
    upcoming_rewards = []
    for item in RewardCatalog.objects.filter(is_active=True):
        progress = min(100, int((total_points / item.points_required) * 100)) if item.points_required > 0 else 0
        upcoming_rewards.append({
            'name': item.name,
            'description': item.description,
            'points_required': item.points_required,
            'progress': progress
        })
    
    # Combine points entries and rewards for the log display
    all_rewards = []
    for entry in points_entries:
        all_rewards.append({
            'is_point': True,
            'date': entry.date,
            'description': entry.description,
            'points_type': entry.points_type,
            'points': entry.points,
            'teacher': entry.teacher,
            'notes': entry.notes
        })
    
    for reward in rewards:
        all_rewards.append({
            'is_point': False,
            'date': reward.date,
            'description': reward.description,
            'name': reward.name,
            'points_cost': reward.points_cost,
            'teacher': reward.teacher,
            'notes': reward.notes
        })
    
    # Sort combined list by date (newest first)
    all_rewards.sort(key=lambda x: x['date'], reverse=True)
    
    context = {
        'student': student,
        'rewards': all_rewards,
        'total_points': total_points,
        'point_types': point_types,
        'upcoming_rewards': upcoming_rewards
    }
    
    return render(request, 'students/rewards.html', context)

@login_required
def add_points(request, student_id):
    """
    Add points to a student
    """
    student = get_object_or_404(Student, id=student_id)
    
    if request.method == 'POST':
        points_type = request.POST.get('points_type')
        points_amount = int(request.POST.get('points_amount', 0))
        reason = request.POST.get('reason', '')
        
        if points_amount <= 0:
            messages.error(request, "Points amount must be greater than zero.")
            return redirect('student_rewards', student_id=student.id)
        
        # Create points entry
        PointsEntry.objects.create(
            student=student,
            points=points_amount,
            points_type=points_type,
            description=reason,
            teacher=request.user
        )
        
        # Log activity
        Activity.objects.create(
            user=request.user,
            description=f"Added {points_amount} points to {student.full_name} for {reason}"
        )
        
        messages.success(request, f"{points_amount} points added successfully to {student.full_name}!")
        return redirect('student_rewards', student_id=student.id)
    
    # GET request shouldn't reach here
    return redirect('student_rewards', student_id=student.id)

@login_required
def add_reward(request, student_id):
    """
    Add a reward redemption for a student
    """
    student = get_object_or_404(Student, id=student_id)
    
    # Calculate total available points
    points_earned = PointsEntry.objects.filter(student=student).aggregate(Sum('points'))['points__sum'] or 0
    points_spent = Reward.objects.filter(student=student).aggregate(Sum('points_cost'))['points_cost__sum'] or 0
    available_points = points_earned - points_spent
    
    # Get reward catalog items
    catalog_items = RewardCatalog.objects.filter(is_active=True)
    
    if request.method == 'POST':
        reward_name = request.POST.get('reward_name')
        reward_description = request.POST.get('reward_description')
        points_cost = int(request.POST.get('points_cost', 0))
        notes = request.POST.get('notes', '')
        
        # Check if student has enough points
        if points_cost > available_points:
            messages.error(request, f"Student doesn't have enough points. Available: {available_points}, Required: {points_cost}")
            return redirect('add_reward', student_id=student.id)
        
        # Create reward redemption
        Reward.objects.create(
            student=student,
            name=reward_name,
            description=reward_description,
            points_cost=points_cost,
            teacher=request.user,
            notes=notes
        )
        
        # Log activity
        Activity.objects.create(
            user=request.user,
            description=f"Redeemed {points_cost} points for {student.full_name}: {reward_name}"
        )
        
        messages.success(request, f"Reward '{reward_name}' successfully redeemed for {student.full_name}!")
        return redirect('student_rewards', student_id=student.id)
    
    context = {
        'student': student,
        'available_points': available_points,
        'catalog_items': catalog_items
    }
    
    return render(request, 'students/reward_form.html', context)
