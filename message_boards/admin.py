from django.contrib import admin
from .models import Board, Topic, Post


class BoardAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}


class TopicAdmin(admin.ModelAdmin):
    list_display = ['subject', 'board']


class PostAdmin(admin.ModelAdmin):
    list_display = ['topic', 'created_by']


# Registration is intentionally switched off: the message boards are not exposed in
# the admin at the moment. Uncomment to manage boards/topics/posts there again.
# admin.site.register(Board, BoardAdmin)
# admin.site.register(Topic, TopicAdmin)
# admin.site.register(Post, PostAdmin)
