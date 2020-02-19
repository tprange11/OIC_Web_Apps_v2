from django.urls import path, include
from . import views

app_name = 'open_hockey'

urlpatterns = [
    path('', views.OpenHockeySessionsPage.as_view(), name='open-hockey'),
    path('success/', views.OpenHockeySessionsSuccess.as_view(), name='open-hockey-success'),
    path('signup/<date>/', views.CreateOpenHockeySessions.as_view(), name='open-hockey-signup'),
    path('signup/', views.CreateOpenHockeySessions.as_view(), name='open-hockey-signup'),
    path('print/', views.OpenHockeySessionsPrint.as_view(), name='open-hockey-print'),
    path('list/<date>/', views.OpenHockeySessionsView.as_view(), name='open-hockey-list'),
    path('sessions/', views.SkaterOpenHockeySessions.as_view(), name='skater-sessions'),
    path('sessions/delete/<pk>/', views.DeleteOpenHockeySessions.as_view(), name='delete-skater-session'),
    path('member/add/', views.CreateOpenHockeyMemberView.as_view(), name='member-add'),
    path('member/', views.OpenHockeyMemberView.as_view(), name='member-detail'),
    path('member/<member>', views.OpenHockeyMemberView.as_view(), name='member-detail'),
    path('member/list/', views.OpenHockeyMemberListView.as_view(), name='member-list'),
    path('member/update/<pk>/', views.UpdateOpenHockeyMemberView.as_view(), name='member-update'),
]