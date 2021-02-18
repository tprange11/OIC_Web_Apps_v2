from django.urls import path, include
from . import views

app_name = 'programs'

urlpatterns = [
    path('api/public/', views.PublicProgramListAPIView.as_view()),
]
