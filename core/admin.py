from django.contrib import admin
from .models import Activity, UserProfile

@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ('description', 'user', 'timestamp')
    list_filter = ('user', 'timestamp')
    search_fields = ('description', 'user__username')
    date_hierarchy = 'timestamp'

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'get_email')
    search_fields = ('user__username', 'user__email')
    
    def get_email(self, obj):
        return obj.user.email
    get_email.short_description = 'البريد الإلكتروني'
