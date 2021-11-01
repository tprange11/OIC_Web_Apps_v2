from django.urls import path
from . import views

app_name = 'how_to_videos'

urlpatterns = [
    path('', views.HowToVideoTemplateView.as_view(), name='index'),
    path('browse/', views.HowToVideoCategoryListView.as_view(), name='categories'),
    path('search/', views.HowToVideoSearchResultsListView.as_view(), name='search'),
    path('<slug>/', views.HowToVideoListView.as_view(), name='video-list'),
]
