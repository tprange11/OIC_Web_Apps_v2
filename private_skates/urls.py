from django.urls import path
from . import views

app_name = 'private_skates'

urlpatterns = [
    path('', views.PrivateSkateListView.as_view(), name="private-skates"),
    path('<slug>/', views.PrivateSkateDatesListView.as_view(), name="skate-dates"),
    path('register/<pk>/', views.PrivateSkateSessionCreateView.as_view(), name="register"),
    path('register/', views.PrivateSkateSessionCreateView.as_view(), name="register"),
    path('remove/<pk>/', views.PrivateSkateSessionDeleteView.as_view(), name="remove-session"),
    
]
