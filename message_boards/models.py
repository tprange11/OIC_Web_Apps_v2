from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
User = get_user_model()


class Board(models.Model):
    '''Model that stores message board name and description.'''

    # Model Fields
    name = models.CharField(max_length=30, unique=True)
    description = models.CharField(max_length=100)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, null=True, blank=True)
    slug = models.SlugField(null=True)

    class Meta:
        # Default order message board name ascending
        ordering = ['pk']

    def __str__(self):
        return f'{self.name}'

    def get_posts_count(self):
        return Post.objects.filter(topic__board=self).count()

    def get_last_post(self):
        return Post.objects.filter(topic__board=self).order_by('-created_at').first()


class Topic(models.Model):
    '''Model that stores Message Board Topic data.'''

    # Model Fields
    subject = models.CharField(max_length=60)
    last_updated = models.DateTimeField(auto_now=True)
    board = models.ForeignKey(Board, related_name='topics', on_delete=models.CASCADE)
    started_by = models.ForeignKey(User, related_name='topics', on_delete=models.CASCADE)
    locked = models.BooleanField(default=False)
    sticky = models.BooleanField(default=False)

    class Meta:
        ordering = ['-sticky', '-last_updated']

    def __str__(self):
        return f'{self.subject}'


class Post(models.Model):
    '''Model that stores individual post data.'''

    # Model Fields
    message = models.TextField(max_length=4000)
    topic = models.ForeignKey(Topic, related_name='posts', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(null=True)
    created_by = models.ForeignKey(User, related_name='posts', on_delete=models.CASCADE)
    updated_by = models.ForeignKey(User, related_name='+', null=True, on_delete=models.CASCADE)

    class Meta:
        ordering = ['created_at']
