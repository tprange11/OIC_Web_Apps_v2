from django.urls import path
from . import views

app_name = 'bald_eagles'

urlpatterns = [
    path('', views.BaldEaglesSkateDateListView.as_view(), name='bald-eagles'),
    path('register/<pk>/', views.CreateBaldEaglesSessionView.as_view(), name='register'),
    path('register/', views.CreateBaldEaglesSessionView.as_view(), name='register'),
    path('session/remove/<pk>/', views.DeleteBaldEaglesSessionView.as_view(), name='session-remove'),
    path('session/list/', views.BaldEaglesSessionStaffListView.as_view(), name='bald-eagles-skate-sessions'),
]
