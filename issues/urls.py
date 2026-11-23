from django.urls import path

from . import views

app_name = 'issues'
urlpatterns = [
    path('', views.index, name='index'),
    path('issues/new/', views.issue_new, name='issue_new'),
    path('issues/my/', views.my_issues, name='my_issues'),
    path('issues/unassigned/', views.unassigned_issues, name='unassigned_issues'),
    path('issues/<int:issue_id>/edit/', views.issue_edit, name='issue_edit'),
    path('issues/<int:issue_id>/status/', views.issue_quick_status, name='issue_quick_status'),
    path('issues/<int:issue_id>/claim/', views.issue_claim, name='issue_claim'),
    path('issues/<int:issue_id>/release/', views.issue_release, name='issue_release'),
    path('issues/<int:issue_id>/history.csv', views.issue_history_csv, name='issue_history_csv'),
    path('issues/<int:issue_id>/', views.issues, name='issue'),
    path('issues/search/', views.search, name='search'),
]
