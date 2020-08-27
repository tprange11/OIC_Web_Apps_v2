from django.shortcuts import render, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count
from django.utils import timezone

from .models import Board, Topic, Post
from .forms import CreateBoardTopicForm, CreateBoardTopicPostReplyForm, PostUpdateForm


class BoardListView(LoginRequiredMixin, ListView):
    '''Page that displays message boards available to the user.'''

    model = Board
    template_name = 'board_list_view.html'
    context_object_name = 'boards'


class BoardTopicListView(LoginRequiredMixin, ListView):
    '''Page that displays topics for a particular message board.'''

    model = Topic
    template_name = 'board_topic_list_view.html'
    context_object_name = 'topics'

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.filter(board=Board.objects.get(slug=self.kwargs['slug'])).annotate(replies=Count('posts'))
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['board'] = Board.objects.get(slug=self.kwargs['slug'])
        return context


class BoardTopicCreateView(LoginRequiredMixin, CreateView):
    '''Page that displays form for creating a new topic.'''

    model = Topic
    template_name = 'board_topic_create_view.html'
    form_class = CreateBoardTopicForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['board'] = Board.objects.get(slug=self.kwargs['slug'])
        return context

    def form_valid(self, form):
        slug = self.kwargs['slug']
        board = get_object_or_404(Board, slug=slug)
        user = self.request.user
        topic = form.save(commit=False)
        topic.board = board
        topic.started_by = user
        topic = form.save()
        post = Post.objects.create(
            message=form.cleaned_data.get('message'),
            topic=topic,
            created_by=user,
            updated_at=timezone.now()
        )
        self.success_url = reverse_lazy('message_boards:topic-post-list', kwargs={'slug': slug, 'pk': topic.pk})
        return super().form_valid(form)


class BoardTopicPostsListView(LoginRequiredMixin, ListView):
    '''Page that displays replies to a board topic.'''
    
    model = Post
    template_name = 'board_topic_posts_list_view.html'
    context_object_name = 'posts'

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.filter(topic=self.kwargs['pk'])
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['board'] = Board.objects.get(slug=self.kwargs['slug'])
        context['topic'] = Topic.objects.get(pk=self.kwargs['pk'])
        return context


class BoardTopicPostReplyCreateView(LoginRequiredMixin, CreateView):
    '''Page that displays form where the user can reply to a post topic.'''

    model = Post
    template_name = 'board_topic_post_reply_create_view.html'
    form_class = CreateBoardTopicPostReplyForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['board'] = Board.objects.get(slug=self.kwargs['slug'])
        context['topic'] = Topic.objects.get(pk=self.kwargs['pk'])
        return context

    def form_valid(self, form):
        pk = self.kwargs['pk']
        slug = self.kwargs['slug']
        topic = get_object_or_404(Topic, pk=pk)
        topic.last_updated = timezone.now()
        topic.save()
        user = self.request.user
        post = form.save(commit=False)
        post.topic = topic
        post.created_by = user
        post.updated_at = timezone.now()
        post = form.save()
        self.success_url = reverse_lazy('message_boards:topic-post-list', kwargs={'slug': slug, 'pk': pk})
        return super().form_valid(form)


class PostUpdateView(LoginRequiredMixin, UpdateView):
    '''Displays page where user can update their posts.'''

    model = Post
    template_name = 'post_update_view.html'
    form_class = PostUpdateForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['board'] = Board.objects.get(slug=self.kwargs['slug'])
        context['topic'] = Topic.objects.get(pk=self.kwargs['topic_pk'])
        return context

    def form_valid(self, form):
        topic = Topic.objects.get(pk=self.kwargs['topic_pk'])
        post = form.save(commit=False)
        post.updated_at = timezone.now()
        # Update Topic last_updated
        topic.last_updated = timezone.now()
        topic.save()
        self.success_url = reverse_lazy('message_boards:topic-post-list', kwargs={'slug': self.kwargs['slug'], 'pk': self.kwargs['topic_pk']})
        return super().form_valid(form)
