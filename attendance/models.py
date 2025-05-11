from django.db import models
from students.models import Student
from django.utils import timezone
from django.core.exceptions import ValidationError
import calendar

class Attendance(models.Model):
    """
    Model to track student attendance on working days (Mon-Thu)
    """
    
    STATUS_CHOICES = [
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('excused', 'Excused'),
    ]
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    notes = models.TextField(blank=True, null=True)
    
    # Auto fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date', 'student__full_name']
        unique_together = ['student', 'date']
        verbose_name = 'Attendance'
        verbose_name_plural = 'Attendance Records'
    
    def __str__(self):
        return f"{self.student.full_name} - {self.date.strftime('%Y-%m-%d')} - {self.get_status_display()}"
    
    def clean(self):
        """
        Validate that attendance is only for working days (Mon-Thu)
        Allow editing on any day, but creation only on working days
        """
        if not self.pk:  # Only validate on creation
            weekday = self.date.weekday()
            if weekday > 3:  # 0=Monday, 3=Thursday, 4=Friday, etc.
                day_name = calendar.day_name[weekday]
                raise ValidationError(f"Attendance can only be marked for working days (Mon-Thu). {day_name} is not a working day.")
    
    def is_present(self):
        return self.status == 'present'
    
    def is_absent(self):
        return self.status == 'absent'
    
    def is_excused(self):
        return self.status == 'excused'
    
    @staticmethod
    def get_attendance_for_week(week_start):
        """
        Get all attendance records for a specific week
        Args:
            week_start: datetime.date object of the first day of the week (Monday)
        Returns:
            QuerySet of Attendance objects
        """
        week_end = week_start + timezone.timedelta(days=3)  # Monday to Thursday
        return Attendance.objects.filter(date__range=[week_start, week_end])
    
    @staticmethod
    def get_attendance_for_month(year, month):
        """
        Get all attendance records for a specific month
        Args:
            year: Year as integer
            month: Month as integer (1-12)
        Returns:
            QuerySet of Attendance objects
        """
        month_start = timezone.datetime(year, month, 1).date()
        
        # Calculate the end of the month
        if month == 12:
            next_month = 1
            next_year = year + 1
        else:
            next_month = month + 1
            next_year = year
        
        month_end = timezone.datetime(next_year, next_month, 1).date() - timezone.timedelta(days=1)
        
        return Attendance.objects.filter(date__range=[month_start, month_end])
