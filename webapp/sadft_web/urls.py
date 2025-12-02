"""
URL configuration for sadft_web project.
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('filesystem.urls')),
]

