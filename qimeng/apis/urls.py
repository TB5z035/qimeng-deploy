from django.urls import path

from . import views

urlpatterns = [
    path('ping/', views.ping, name='ping'),
    path('test/', views.test, name='test'),
    path('create/', views.create_det_req, name='create_det_req'),
    path('query/<str:id>/', views.query_det_req, name='query_det_req'),
]