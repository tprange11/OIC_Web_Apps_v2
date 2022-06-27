from django.urls import path
from . import views

app_name = 'nacho_skate'

urlpatterns = [
    path('', views.NachoSkateDateListView.as_view(), name='index'),
    path('register/<pk>/', views.CreateNachoSkateSessionView.as_view(), name='register'),
    path('register/', views.CreateNachoSkateSessionView.as_view(), name='register'),
    path('session/remove/<pk>/<paid>/<skater_pk>', views.DeleteNachoSkateSessionView.as_view(), name='session-remove'),
]
