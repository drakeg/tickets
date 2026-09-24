from django.urls import path

from . import views

app_name = "knowledgebase"

urlpatterns = [
    path("", views.index, name="index"),
    path("new/", views.article_new, name="new"),
    path("search/", views.search, name="search"),
    path("<int:article_id>/", views.article_detail, name="detail"),
    path("<int:article_id>/edit/", views.article_edit, name="edit"),
    path("<int:article_id>/delete/", views.article_delete, name="delete"),
]
