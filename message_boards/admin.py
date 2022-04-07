from django.contrib import admin
from .models import Board, Topic, Post

# Register your models here.


class BoardAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}


class TopicAdmin(admin.ModelAdmin):
    list_display = ['subject', 'board']


class PostAdmin(admin.ModelAdmin):
    list_display = ['topic', 'created_by']


# admin.site.register(Board, BoardAdmin)
# admin.site.register(Topic, TopicAdmin)
# admin.site.register(Post, PostAdmin)
