from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.db.models import Q

from .models import Student, Certificate
from .forms import StudentForm, CertificateForm
from core.models import Activity

@login_required
def student_list(request):
    """
    Display a list of all students
    """
    # Get filter parameters
    status_filter = request.GET.get('status', 'active')
    search_query = request.GET.get('q', '')
    
    # Filter students based on status and search query
    if status_filter == 'all':
        students = Student.objects.all()
    else:
        students = Student.objects.filter(status=status_filter)
    
    if search_query:
        students = students.filter(
            Q(full_name__icontains=search_query) | 
            Q(phone_number__icontains=search_query) |
            Q(guardian_name__icontains=search_query)
        )
    
    context = {
        'students': students,
        'status_filter': status_filter,
        'search_query': search_query,
    }
    
    return render(request, 'students/student_list.html', context)

@login_required
def student_detail(request, student_id):
    """
    Display details of a specific student
    """
    student = get_object_or_404(Student, id=student_id)
    certificates = student.certificate_set.all()
    
    context = {
        'student': student,
        'certificates': certificates,
    }
    
    return render(request, 'students/student_detail.html', context)

@login_required
def student_add(request):
    """
    Add a new student
    """
    if request.method == 'POST':
        form = StudentForm(request.POST, request.FILES)
        if form.is_valid():
            student = form.save()
            
            # Log activity
            Activity.objects.create(
                user=request.user,
                description=f"Added new student: {student.full_name}"
            )
            
            messages.success(request, f"Student {student.full_name} has been added successfully!")
            return redirect('student_detail', student_id=student.id)
    else:
        form = StudentForm()
    
    context = {
        'form': form,
        'title': 'Add New Student',
    }
    
    return render(request, 'students/student_form.html', context)

@login_required
def student_edit(request, student_id):
    """
    Edit an existing student
    """
    student = get_object_or_404(Student, id=student_id)
    
    if request.method == 'POST':
        form = StudentForm(request.POST, request.FILES, instance=student)
        if form.is_valid():
            student = form.save()
            
            # Log activity
            Activity.objects.create(
                user=request.user,
                description=f"Updated student: {student.full_name}"
            )
            
            messages.success(request, f"Student {student.full_name} has been updated successfully!")
            return redirect('student_detail', student_id=student.id)
    else:
        form = StudentForm(instance=student)
    
    context = {
        'form': form,
        'student': student,
        'title': 'Edit Student',
    }
    
    return render(request, 'students/student_form.html', context)

@login_required
def student_delete(request, student_id):
    """
    Delete a student
    """
    student = get_object_or_404(Student, id=student_id)
    
    if request.method == 'POST':
        student_name = student.full_name
        student.delete()
        
        # Log activity
        Activity.objects.create(
            user=request.user,
            description=f"Deleted student: {student_name}"
        )
        
        messages.success(request, f"Student {student_name} has been deleted successfully!")
        return redirect('student_list')
    
    context = {
        'student': student,
    }
    
    return render(request, 'students/student_confirm_delete.html', context)

@login_required
def certificate_add(request, student_id):
    """
    Add a certificate to a student
    """
    student = get_object_or_404(Student, id=student_id)
    
    if request.method == 'POST':
        form = CertificateForm(request.POST, request.FILES)
        if form.is_valid():
            certificate = form.save(commit=False)
            certificate.student = student
            certificate.save()
            
            # Log activity
            Activity.objects.create(
                user=request.user,
                description=f"Added certificate for student: {student.full_name}"
            )
            
            messages.success(request, "Certificate has been added successfully!")
            return redirect('student_detail', student_id=student.id)
    else:
        form = CertificateForm()
    
    context = {
        'form': form,
        'student': student,
        'title': 'Add Certificate',
    }
    
    return render(request, 'students/certificate_form.html', context)

@login_required
def certificate_delete(request, certificate_id):
    """
    Delete a certificate
    """
    certificate = get_object_or_404(Certificate, id=certificate_id)
    student = certificate.student
    
    if request.method == 'POST':
        certificate.delete()
        
        # Log activity
        Activity.objects.create(
            user=request.user,
            description=f"Deleted certificate for student: {student.full_name}"
        )
        
        messages.success(request, "Certificate has been deleted successfully!")
        return redirect('student_detail', student_id=student.id)
    
    context = {
        'certificate': certificate,
        'student': student,
    }
    
    return render(request, 'students/certificate_confirm_delete.html', context)
