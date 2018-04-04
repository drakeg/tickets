"""tickets URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path, re_path

urlpatterns = [
    re_path(r'^api/', include('djoser.urls')),
    re_path(r"^search/", include("watson.urls", namespace="watson"), kwargs={"paginate_by":10}),
    path('inventory/', include('inventory.urls')),
    path('issues/', include('issues.urls')),
    path('projects/', include('projects.urls')),
    path('admin/', admin.site.urls),
    path('knowledgebase/', include('knowledgebase.urls')),
    path('', include('dashboard.urls')),
    path('account/', include('accounts.urls')),
]

urlpatterns += [
    path('accounts/', include('django.contrib.auth.urls')),
]
