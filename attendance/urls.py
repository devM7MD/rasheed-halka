from django.urls import path
from . import views

urlpatterns = [
    path('', views.attendance_list, name='attendance_list'),
    path('today/', views.attendance_today, name='attendance_today'),
    path('edit/<int:attendance_id>/', views.attendance_edit, name='attendance_edit'),
    path('edit-date/', views.attendance_edit_date, name='attendance_edit_date'),
    path('report/', views.attendance_report, name='attendance_report'),
] 