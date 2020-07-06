from django.urls import path
from . import views

app_name = 'womens_hockey'

urlpatterns = [
    path('', views.WomensHockeySkateDateListView.as_view(), name='womens-hockey'),
    path('register/<pk>/',
         views.CreateWomensHockeySkateSessionView.as_view(), name='register'),
    path('register/', views.CreateWomensHockeySkateSessionView.as_view(),
         name='register'),
    path('session/remove/<pk>',
         views.DeleteWomensHockeySkateSessionView.as_view(), name='session-remove'),
    path('session/list/', views.WomensHockeySkateDateStaffListView.as_view(),
         name='womens-hockey-sessions'),
]
