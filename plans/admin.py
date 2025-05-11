from django.contrib import admin
from .models import MemorizationPlan, DailyTask

class DailyTaskInline(admin.TabularInline):
    model = DailyTask
    extra = 1

@admin.register(MemorizationPlan)
class MemorizationPlanAdmin(admin.ModelAdmin):
    list_display = ('student', 'week_start', 'week_end', 'current_surah', 'current_ayah', 'target_ayahs_per_day')
    list_filter = ('week_start', 'week_end')
    search_fields = ('student__full_name',)
    date_hierarchy = 'week_start'
    inlines = [DailyTaskInline]

@admin.register(DailyTask)
class DailyTaskAdmin(admin.ModelAdmin):
    list_display = ('get_student_name', 'date', 'task_type', 'status')
    list_filter = ('date', 'task_type', 'status')
    search_fields = ('plan__student__full_name', 'description')
    date_hierarchy = 'date'
    
    def get_student_name(self, obj):
        return obj.plan.student.full_name
    get_student_name.short_description = 'Student'
