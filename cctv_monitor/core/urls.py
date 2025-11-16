from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('monitor/', views.start_monitoring_view, name='monitor-start'),
    path('monitor/<int:session_id>/status/', views.monitor_status_view, name='monitor-status'),
]
