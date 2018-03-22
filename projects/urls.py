from django.urls import path

from . import views

app_name = 'projects'
urlpatterns = [
    path('', views.index, name='index'),
    path('projects/new/', views.project_new, name='project_new'),
    path('projects/my/', views.my_projects, name='my_projects'),
    path('projects/unassigned/', views.unassigned_projects, name='unassigned_projects'),
    path('projects/<int:project_id>/', views.project, name='project'),
    path('projects/search/', views.search, name='search'),
]
