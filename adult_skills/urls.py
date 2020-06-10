from django.urls import path
from . import views

app_name = 'adult_skills'

urlpatterns = [
    path('', views.AdultSkillsSkateDateListView.as_view(), name='adult-skills'),
    path('register/<pk>/', views.CreateAdultSkillsSkateSessionView.as_view(), name='register'),
    path('register/', views.CreateAdultSkillsSkateSessionView.as_view(), name='register'),
    path('session/remove/<pk>', views.DeleteAdultSkillsSkateSessionView.as_view(), name='session-remove'),
    path('session/list/', views.AdultSkillsSkateDateStaffListView.as_view(), name='adult-skills-sessions'),    
]