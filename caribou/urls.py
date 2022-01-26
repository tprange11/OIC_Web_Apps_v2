from django.urls import path
from . import views

app_name = 'caribou'

urlpatterns = [
    path('', views.CaribouSkateDateListView.as_view(), name='caribou'),
    path('register/<pk>/', views.CreateCaribouSkateSessionView.as_view(), name='register'),
    path('register/', views.CreateCaribouSkateSessionView.as_view(), name='register'),
    path('session/remove/<pk>', views.DeleteCaribouSkateSessionView.as_view(), name='session-remove'),
]
