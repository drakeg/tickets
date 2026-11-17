from django.urls import path
from . import views

app_name = 'account'
urlpatterns = [
    path('', views.index, name='index'),
    path('roles/', views.roles, name='roles'),
    path('register/', views.register, name='register')
]