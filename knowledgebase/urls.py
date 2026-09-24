from django.urls import path

from . import views

app_name = "knowledgebase"

urlpatterns = [
    path("", views.index, name="index"),
    path("new/", views.article_new, name="new"),
    path("<int:article_id>/", views.article_detail, name="detail"),
]
