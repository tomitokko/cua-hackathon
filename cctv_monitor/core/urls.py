from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('api/start_stream', views.start_stream, name='start_stream'),
    path('api/stop_stream', views.stop_stream, name='stop_stream'),
    path('api/status', views.status, name='status'),
    path('api/frame', views.frame, name='frame'),
]
