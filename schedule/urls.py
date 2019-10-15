from django.urls import path, include
from . import views

app_name = 'schedule'

urlpatterns = [
    path('', views.ChooseRink.as_view(), name='choose-rink'),
    path('rink/<rink>', views.RinkScheduleListView.as_view(), name='rink-schedule-list'),
    path('rink/', views.RinkScheduleListView.as_view(), name='rink-schedule-list'),
]