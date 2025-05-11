from django.urls import path
from . import views

urlpatterns = [
    path('', views.student_list, name='student_list'),
    path('add/', views.student_add, name='student_add'),
    path('<int:student_id>/', views.student_detail, name='student_detail'),
    path('<int:student_id>/edit/', views.student_edit, name='student_edit'),
    path('<int:student_id>/delete/', views.student_delete, name='student_delete'),
    path('<int:student_id>/add-certificate/', views.certificate_add, name='certificate_add'),
    path('certificate/<int:certificate_id>/delete/', views.certificate_delete, name='certificate_delete'),
] 