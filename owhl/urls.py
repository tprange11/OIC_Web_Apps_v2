from django.urls import path
from . import views

app_name = 'owhl'

urlpatterns = [
    path('', views.OWHLSkateDateListView.as_view(), name='owhl'),
    path('register/<pk>/', views.CreateOWHLSkateSessionView.as_view(), name='register'),
    path('register/', views.CreateOWHLSkateSessionView.as_view(), name='register'),
    path('session/remove/<pk>', views.DeleteOWHLSkateSessionView.as_view(), name='session-remove'),
    path('session/list/', views.OWHLSkateDateStaffListView.as_view(), name='owhl-sessions'),
]
