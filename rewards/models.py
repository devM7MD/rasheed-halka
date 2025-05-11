from django.db import models
from django.utils import timezone
from students.models import Student
from django.contrib.auth.models import User

class PointsEntry(models.Model):
    """
    Model to track points awarded to students
    """
    POINTS_TYPE_CHOICES = [
        ('memorization', 'Memorization'),
        ('review', 'Review'),
        ('attendance', 'Attendance'),
        ('behavior', 'Behavior'),
        ('activities', 'Activities'),
    ]
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    points = models.PositiveIntegerField()
    points_type = models.CharField(max_length=15, choices=POINTS_TYPE_CHOICES)
    description = models.CharField(max_length=255)
    date = models.DateField(default=timezone.now)
    teacher = models.ForeignKey(User, on_delete=models.CASCADE)
    notes = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date', 'student__full_name']
        verbose_name = 'Points Entry'
        verbose_name_plural = 'Points Entries'
    
    def __str__(self):
        return f"{self.student.full_name} - {self.points} points ({self.get_points_type_display()})"

class Reward(models.Model):
    """
    Model to track rewards redeemed by students
    """
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    description = models.TextField()
    points_cost = models.PositiveIntegerField()
    date = models.DateField(default=timezone.now)
    teacher = models.ForeignKey(User, on_delete=models.CASCADE)
    notes = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date', 'student__full_name']
        verbose_name = 'Reward'
        verbose_name_plural = 'Rewards'
    
    def __str__(self):
        return f"{self.student.full_name} - {self.name} ({self.points_cost} points)"

class RewardCatalog(models.Model):
    """
    Model to define available rewards in the system
    """
    name = models.CharField(max_length=100)
    description = models.TextField()
    points_required = models.PositiveIntegerField()
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['points_required', 'name']
        verbose_name = 'Reward Catalog Item'
        verbose_name_plural = 'Reward Catalog'
    
    def __str__(self):
        return f"{self.name} - {self.points_required} points"
