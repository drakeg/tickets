from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('projects/new/', views.project_new, name='project_new'),
    path('<int:project_id>/', views.project, name='project'),
]
