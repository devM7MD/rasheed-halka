from django.urls import path
from . import views

urlpatterns = [
    path('', views.plan_list, name='plan_list'),
    path('generate/', views.plan_generate, name='plan_generate'),
    path('<int:plan_id>/', views.plan_detail, name='plan_detail'),
    path('<int:plan_id>/export/', views.export_plan_as_image, name='export_plan'),
    path('export-all/', views.export_all_plans, name='export_all_plans'),
    path('export-all/<str:week_start>/', views.export_all_plans, name='export_all_plans_week'),
    path('<int:plan_id>/cancel/', views.plan_cancel, name='plan_cancel'),
    path('tasks/today/', views.today_tasks, name='today_tasks'),
    path('tasks/<int:task_id>/update/', views.task_update, name='task_update'),
    path('<int:plan_id>/tasks/add/', views.task_add, name='task_add'),
    path('special-session/', views.special_session, name='special_session'),
] 