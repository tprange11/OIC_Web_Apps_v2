from django.urls import path
from . import views

app_name = 'kranich'

urlpatterns = [
    path('', views.KranichSkateDateListView.as_view(), name='kranich'),
    path('register/<pk>/', views.CreateKranichSkateSessionView.as_view(), name='register'),
    path('register/', views.CreateKranichSkateSessionView.as_view(), name='register'),
    path('session/remove/<pk>', views.DeleteKranichSkateSessionView.as_view(), name='session-remove'),
    # path('session/list/', views.YetiSkateDateStaffListView.as_view(), name='yeti-skate-sessions'),
]
