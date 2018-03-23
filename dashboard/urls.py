from django.urls import path
from django.contrib import admin
from django.contrib.auth import views as auth_views

from . import views

app_name = 'dashboard'
urlpatterns = [
    path('', views.index, name='index'),
    path('login/', auth_views.login, name='login'),
    path('logout/', auth_views.logout, {'next_page':'/'}, name='logout'),
    path('signup/', views.signup, name='signup'),
    path('admin/', admin.site.urls, name='admin'),
]
