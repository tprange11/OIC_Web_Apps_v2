from django.urls import path
from . import views

app_name = 'yeti_skate'

urlpatterns = [
    path('', views.YetiSkateDateListView.as_view(), name='yeti-skate'),
    path('register/<pk>/', views.CreateYetiSkateSessionView.as_view(), name='register'),
    path('register/', views.CreateYetiSkateSessionView.as_view(), name='register'),
    path('session/remove/<pk>/<paid>/<skater_pk>', views.DeleteYetiSkateSessionView.as_view(), name='session-remove'),
    path('session/list/', views.YetiSkateDateStaffListView.as_view(), name='yeti-skate-sessions'),
]
