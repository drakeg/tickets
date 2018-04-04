from django.urls import path

from . import views

app_name = 'account'
urlpatterns = [
    path('', views.index, name='index'),
    #path('server/new/', views.servers_new, name='servers_new'),
]