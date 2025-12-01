from django.contrib import admin
from .models import PrivateSkate, PrivateSkateDate, PrivateSkateSession

class PrivateSkateAdmin(admin.ModelAdmin):
    list_display = ['name', 'page_url', 'max_skaters', 'max_goalies', 'skater_price', 'goalie_price']
    list_filter = ['name']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}

    def page_url(self, obj):
        return f"https://www.oicwebapp.com/web_apps/private_skates/{obj.slug}/"


class PrivateSkateDateAdmin(admin.ModelAdmin):
    list_display = ['private_skate', 'date', 'start_time', 'end_time']
    list_filter = ['date']
    # search_fields = ['']


class PrivateSkateSessionAdmin(admin.ModelAdmin):
    list_display = ['private_skate', 'user_name', 'skater_name', 'skate_date', 'goalie', 'paid']
    # list_filter = ['skate_date', 'skater']
    search_fields = [
        'skate_date__private_skate__name', 
        'user__first_name', 
        'user__last_name',
        'skater__first_name',
        'skater__last_name'
        ]

    def user_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"

    def skater_name(self, obj):
        return f"{obj.skater.first_name} {obj.skater.last_name}"

    def private_skate(self, obj):
        return f"{obj.skate_date.private_skate.name}"


admin.site.register(PrivateSkate, PrivateSkateAdmin)
admin.site.register(PrivateSkateDate, PrivateSkateDateAdmin)
admin.site.register(PrivateSkateSession, PrivateSkateSessionAdmin)
