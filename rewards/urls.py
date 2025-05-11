from django.urls import path
from . import views

urlpatterns = [
    path('student/<int:student_id>/', views.student_rewards, name='student_rewards'),
    path('student/<int:student_id>/add-points/', views.add_points, name='add_points'),
    path('student/<int:student_id>/add-reward/', views.add_reward, name='add_reward'),
] 