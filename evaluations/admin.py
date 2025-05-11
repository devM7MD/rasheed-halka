from django.contrib import admin
from .models import Evaluation

@admin.register(Evaluation)
class EvaluationAdmin(admin.ModelAdmin):
    list_display = ('student', 'date', 'old_memorization_score', 'new_memorization_score', 
                    'behavior_score', 'activity_score', 'get_total_score', 'get_final_grade')
    list_filter = ('date', 'behavior_score', 'activity_score')
    search_fields = ('student__full_name', 'comments')
    date_hierarchy = 'date'
    
    def get_total_score(self, obj):
        return obj.get_total_score()
    get_total_score.short_description = 'Total Score'
    
    def get_final_grade(self, obj):
        return obj.get_final_grade()
    get_final_grade.short_description = 'Final Grade'
