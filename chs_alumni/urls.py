from chs_alumni.views import CreateCHSAlumniSessionView
from django.urls import path
from . import views

app_name = 'chs_alumni'

urlpatterns = [
    path('', views.CHSAlumniSkateDateListView.as_view(), name='chs-alumni'),
    path('register/', views.CreateCHSAlumniSessionView.as_view(), name='register'),
    path('register/<pk>/', views.CreateCHSAlumniSessionView.as_view(), name='register'),
    path('session/remove/<pk>', views.DeleteCHSAlumniSessionView.as_view(), name='session-remove'),
    path('session/list/', views.CHSAlumniSkateDateStaffListView.as_view(), name='skate-sessions')
]
