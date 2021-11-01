from django.contrib import admin
from .models import Category, Keyword, HowToVideo


class CategoryAdmin(admin.ModelAdmin):
    list_display = ['video_category', 'staff_only']
    prepopulated_fields = {'slug': ('video_category',)}
    # readonly_fields = ['slug']


class KeywordAdmin(admin.ModelAdmin):
    list_display = ['keyword']

class HowToVideoAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'staff_only', 'active', 'date_created', 'last_modified']


admin.site.register(Category, CategoryAdmin)
admin.site.register(Keyword, KeywordAdmin)
admin.site.register(HowToVideo, HowToVideoAdmin)
