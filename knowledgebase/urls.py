from django.urls import path

from . import views

app_name = 'knowledgebase'
urlpatterns = [
    path('', views.index, name='index'),
]
