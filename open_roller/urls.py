from django.urls import path
from . import views

app_name = 'open_roller'

urlpatterns = [
    path('', views.OpenRollerSkateDateListView.as_view(), name='open-roller'),
    path('register/<pk>/', views.CreateOpenRollerSkateSessionView.as_view(), name='register'),
    path('register/', views.CreateOpenRollerSkateSessionView.as_view(), name='register'),
    path('session/remove/<pk>', views.DeleteOpenRollerSkateSessionView.as_view(), name='session-remove'),
    path('session/list/', views.OpenRollerSkateDateStaffListView.as_view(), name='open-roller-sessions'),
]
