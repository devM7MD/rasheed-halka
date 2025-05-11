from django.urls import path
from . import views

urlpatterns = [
    path('', views.evaluation_list, name='evaluation_list'),
    path('add/', views.evaluation_add, name='evaluation_add'),
    path('<int:evaluation_id>/edit/', views.evaluation_edit, name='evaluation_edit'),
    path('<int:evaluation_id>/delete/', views.evaluation_delete, name='evaluation_delete'),
    path('report/', views.evaluation_report, name='evaluation_report'),
] 