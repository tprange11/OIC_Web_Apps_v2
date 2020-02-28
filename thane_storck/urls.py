from django.urls import path
from . import views

app_name = 'thane_storck'

urlpatterns = [
    path('', views.SkateDateListView.as_view(), name='thane-skate'),
    path('register/<pk>/', views.CreateSkateSessionView.as_view(), name='register'),
    path('register/', views.CreateSkateSessionView.as_view(), name='register'),
    path('session/remove/<pk>', views.DeleteSkateSessionView.as_view(), name='session-remove'),
    path('session/list/', views.PrintSkateDateListView.as_view(), name='thane-skate-sessions'),
    path('session/list/print/<pk>', views.PrintSkateDateView.as_view(), name='thane-skate-print'),
    
]
