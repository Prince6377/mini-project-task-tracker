from django.contrib import admin
from django.urls import path
from core import views

urlpatterns = [
    path('admin/', admin.site.urls),

    # Project endpoints
    path('projects/', views.create_project, name='create_project'),
    path('projects/list/', views.list_projects, name='list_projects'),
    path('projects/<int:project_id>/tasks/', views.create_task, name='create_task'),

    # Tasks
    path('tasks/', views.list_tasks, name='list_tasks'),

    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),
]
