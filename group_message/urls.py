from django.urls import path
from . import views

app_name = 'group_message'

urlpatterns = [
    path('<group>/', views.GroupMessageView.as_view(), name='group-message'),
    path('', views.GroupMessageView.as_view(), name='group-message'),
]
