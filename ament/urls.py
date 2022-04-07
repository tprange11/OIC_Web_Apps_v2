from django.urls import path
from . import views

app_name = 'ament'

urlpatterns = [
    path('', views.AmentSkateDateListView.as_view(), name='skate-dates'),
    path('register/<pk>/', views.CreateAmentSkateSessionView.as_view(), name='register'),
    path('register/', views.CreateAmentSkateSessionView.as_view(), name='register'),
    path('session/remove/<pk>/<paid>/<skater_pk>', views.DeleteAmentSkateSessionView.as_view(), name='session-remove'),
]
