from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

# Create your models here.

class Activity(models.Model):
    """
    Model to track user activities in the system
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    description = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Activity'
        verbose_name_plural = 'Activities'
    
    def __str__(self):
        return f"{self.user.username} - {self.description} ({self.timestamp.strftime('%Y-%m-%d %H:%M')})"

class UserProfile(models.Model):
    """
    Extension of the User model to store additional information
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_image = models.ImageField(upload_to='profile_images/', null=True, blank=True)
    
    def __str__(self):
        return f"{self.user.username}'s Profile"

# Signal to create a user profile when a user is created
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    try:
        instance.userprofile.save()
    except UserProfile.DoesNotExist:
        UserProfile.objects.create(user=instance)
