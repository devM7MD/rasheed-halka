from django.contrib import admin
from .models import Student, Certificate

class CertificateInline(admin.TabularInline):
    model = Certificate
    extra = 1

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'category', 'study_level', 'status', 'phone_number')
    list_filter = ('status', 'category', 'study_level', 'registration_date')
    search_fields = ('full_name', 'phone_number', 'guardian_name')
    date_hierarchy = 'registration_date'
    inlines = [CertificateInline]

@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ('student', 'title', 'issue_date')
    list_filter = ('issue_date',)
    search_fields = ('title', 'student__full_name')
    date_hierarchy = 'issue_date'
