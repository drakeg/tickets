from django.urls import path

from . import views

app_name = 'inventory'
urlpatterns = [
    path('', views.index, name='index'),
    path('server/<int:server_id>/', views.servers, name='servers'),
    path('os/<int:operating_system_id>/', views.operating_systems, name='operating_systems'),
]
