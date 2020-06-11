from django.urls import path
from . import views

app_name = 'mike_schultz'

urlpatterns = [
    path('', views.MikeSchultzSkateDateListView.as_view(), name='mike-schultz'),
    path('register/<pk>/', views.CreateMikeSchultzSkateSessionView.as_view(), name='register'),
    path('register/', views.CreateMikeSchultzSkateSessionView.as_view(), name='register'),
    path('session/remove/<pk>', views.DeleteMikeSchultzSkateSessionView.as_view(), name='session-remove'),
    path('session/list/', views.MikeSchultzSkateDateStaffListView.as_view(), name='mike-schultz-sessions'),
]
