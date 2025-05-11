from django.contrib import admin
from .models import Attendance

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('student', 'date', 'status', 'notes')
    list_filter = ('date', 'status')
    search_fields = ('student__full_name', 'notes')
    date_hierarchy = 'date'
