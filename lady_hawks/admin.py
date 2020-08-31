from django.contrib import admin
from lady_hawks.models import LadyHawksSkateDate, LadyHawksSkateSession


class LadyHawksSkateDateAdmin(admin.ModelAdmin):
    list_display = ['skate_date', 'start_time', 'end_time']


class LadyHawksSkateSessionAdmin(admin.ModelAdmin):
    list_display = ['user_name', 'skater', 'skate_date', 'goalie', 'paid']
    list_filter = ['skate_date']
    search_fields = ['user__first_name', 'user__last_name', 'skater__first_name', 'skater__last_name']

    def user_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"


admin.site.register(LadyHawksSkateDate, LadyHawksSkateDateAdmin)
admin.site.register(LadyHawksSkateSession, LadyHawksSkateSessionAdmin)
