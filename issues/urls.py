from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('<int:issues_id>/', views.issues, name='issues'),
]
