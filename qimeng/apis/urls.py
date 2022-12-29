from django.urls import path

from . import views

urlpatterns = [
    path('ping/', views.ping, name='ping'),
    path('list/', views.test, name='test'),
    path('list_bricks/', views.test_bricks, name='list_bricks'),
    path('update_bricks/', views.update_bricks, name='update_bricks'),
    path('create/', views.create_det_req, name='create_det_req'),
    path('query/<str:id>/', views.query_det_req, name='query_det_req'),
    path('clear/', views.clear, name='clear'),
]