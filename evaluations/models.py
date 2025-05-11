from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from students.models import Student
from django.utils import timezone

class Evaluation(models.Model):
    """
    Model to store student evaluations
    """
    
    GRADE_CHOICES = [
        ('excellent', 'Excellent'),
        ('very_good', 'Very Good'),
        ('good', 'Good'),
        ('acceptable', 'Acceptable'),
        ('average', 'Average'),
        ('weak', 'Weak'),
    ]
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    date = models.DateField()
    
    # Old memorization (review) score
    old_memorization_score = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        help_text="Score for old memorization review (0-10)"
    )
    
    # New memorization score
    new_memorization_score = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        help_text="Score for new memorization (0-10)"
    )
    
    # Behavior score
    behavior_score = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        help_text="Score for behavior (0-10)"
    )
    
    # Activity score
    activity_score = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        help_text="Score for class activities (0-10)"
    )
    
    # Comments
    comments = models.TextField(blank=True, null=True)
    
    # Auto fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date', 'student__full_name']
        unique_together = ['student', 'date']
        verbose_name = 'Evaluation'
        verbose_name_plural = 'Evaluations'
    
    def __str__(self):
        return f"{self.student.full_name} - {self.date.strftime('%Y-%m-%d')} - {self.get_final_grade()}"
    
    def get_total_score(self):
        """Calculate total score out of 40"""
        return self.old_memorization_score + self.new_memorization_score + self.behavior_score + self.activity_score
    
    def get_percentage(self):
        """Calculate percentage score (0-100%)"""
        return (self.get_total_score() / 40.0) * 100
    
    def get_memorization_score(self):
        """Calculate combined memorization score (old + new)"""
        return self.old_memorization_score + self.new_memorization_score
    
    def get_memorization_percentage(self):
        """Calculate memorization percentage"""
        return (self.get_memorization_score() / 20.0) * 100
    
    def get_behavior_grade(self):
        """Convert behavior score to grade"""
        score = self.behavior_score
        if score == 10:
            return 'excellent'
        elif score == 9:
            return 'very_good'
        elif score == 8:
            return 'good'
        elif score in [6, 7]:
            return 'acceptable'
        elif score in [4, 5]:
            return 'average'
        else:  # 1-3
            return 'weak'
    
    def get_final_grade(self):
        """Calculate final grade based on total percentage"""
        percentage = self.get_percentage()
        
        if percentage >= 90:
            return "Excellent"
        elif percentage >= 80:
            return "Very Good"
        elif percentage >= 70:
            return "Good"
        elif percentage >= 60:
            return "Acceptable"
        elif percentage >= 50:
            return "Average"
        else:
            return "Weak"
    
    @staticmethod
    def get_evaluations_for_month(year, month):
        """
        Get all evaluations for a specific month
        Args:
            year: Year as integer
            month: Month as integer (1-12)
        Returns:
            QuerySet of Evaluation objects
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
        
        return Evaluation.objects.filter(date__range=[month_start, month_end])
