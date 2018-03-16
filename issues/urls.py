from django.urls import path

from . import views

app_name = 'issues'
urlpatterns = [
    path('', views.index, name='index'),
    path('issues/new/', views.issue_new, name='issue_new'),
    path('issues/<int:issue_id>/', views.issues, name='issue'),
]
