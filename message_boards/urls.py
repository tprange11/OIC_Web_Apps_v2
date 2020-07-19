from django.urls import path
from . import views

app_name = 'message_boards'

urlpatterns = [
    path('', views.BoardListView.as_view(), name='message-boards'),
    path('<slug>/', views.BoardTopicListView.as_view(), name='board-topics'),
    path('<slug>/new_topic/', views.BoardTopicCreateView.as_view(), name='new-topic'),
    path('<slug>/topic/<pk>/', views.BoardTopicPostsListView.as_view(), name='topic-post-list'),
    path('<slug>/topic/<pk>/post_reply/', views.BoardTopicPostReplyCreateView.as_view(), name='topic-post-reply'),
    path('<slug>/topic/<topic_pk>/edit/<pk>/', views.PostUpdateView.as_view(), name='post-edit'),
]
