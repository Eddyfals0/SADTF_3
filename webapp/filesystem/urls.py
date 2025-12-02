"""
URLs para la aplicación filesystem
"""
from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('api/get-coordinator-host/', views.get_coordinator_host, name='get_coordinator_host'),
    path('api/nodes/', views.get_active_nodes, name='get_active_nodes'),
    path('api/files/', views.list_files, name='list_files'),
    path('api/files/upload/', views.upload_file, name='upload_file'),
    path('api/files/download/', views.download_file, name='download_file'),
    path('api/files/delete/', views.delete_file, name='delete_file'),
    path('api/files/info/', views.get_file_info, name='get_file_info'),
    path('api/blocks/', views.get_block_table, name='get_block_table'),
    path('api/cleanup/', views.cleanup_all, name='cleanup_all'),
]
