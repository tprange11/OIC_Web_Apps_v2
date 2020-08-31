from django.urls import path
from . import views

app_name = 'lady_hawks'

urlpatterns = [
    path('', views.LadyHawksSkateDateListView.as_view(), name='lady-hawks'),
    path('register/<pk>/', views.CreateLadyHawksSkateSessionView.as_view(), name='register'),
    path('register/', views.CreateLadyHawksSkateSessionView.as_view(), name='register'),
    path('session/remove/<pk>', views.DeleteLadyHawksSkateSessionView.as_view(), name='session-remove'),
    path('session/list/', views.LadyHawksSkateDateStaffListView.as_view(), name='lady-hawks-sessions'),
]