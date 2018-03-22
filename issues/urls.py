from django.urls import path

from . import views

app_name = 'issues'
urlpatterns = [
    path('', views.index, name='index'),
    path('issues/new/', views.issue_new, name='issue_new'),
    path('issues/my/', views.my_issues, name='my_issues'),
    path('issues/unassigned/', views.unassigned_issues, name='unassigned_issues'),
    path('issues/<int:issue_id>/', views.issues, name='issue'),
    path('issues/search/', views.search, name='search'),
]
