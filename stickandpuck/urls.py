from django.urls import path, include
from . import views

app_name = 'stickandpuck'

urlpatterns = [
    path('', views.StickAndPuckIndex.as_view(), name='stick-and-puck'),
    path('skater/add/', views.CreateStickAndPuckSkaterView.as_view(), name='skater-add'),
    path('skater/list/', views.StickAndPuckSkaterListView.as_view(), name='skater-list'),
    path('skater/delete/<pk>', views.DeleteStickAndPuckSkater.as_view(), name='skater-delete'),
    path('sessions/', views.StickAndPuckSessionListView.as_view(), name='sessions'),
    path('signup/<session_date>/<session_time>', views.CreateStickAndPuckSession.as_view(), name='signup'),
    path('signup/', views.CreateStickAndPuckSession.as_view(), name='signup'),
    path('mysessions/delete/<pk>', views.StickAndPuckSessionDeleteView.as_view(), name='delete-session'),
    path('mysessions/', views.StickAndPuckMySessionsListView.as_view(), name='mysessions'),
    path('print_list/', views.StickAndPuckPrintListView.as_view(), name='print-list'),
    path('print/<date>/<time>/', views.StickAndPuckPrintView.as_view(), name='print'),
    path('availability/<session_date>/<session_time>/', views.StickAndPuckSessionCount.as_view(), name='skater-spots'),
]