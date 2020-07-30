from django.contrib import admin
from mike_schultz.models import MikeSchultzSkateDate, MikeSchultzSkateSession

# Register your models here.


class MikeSchultzSkateDateAdmin(admin.ModelAdmin):
    list_display = ['skate_date', 'start_time', 'end_time']


class MikeSchultzSkateSessionAdmin(admin.ModelAdmin):
    list_display = ['user_name', 'skater', 'skate_date', 'goalie', 'paid']
    list_filter = ['skate_date']
    search_fields = ['user__first_name', 'user__last_name', 'skater__first_name', 'skater__last_name']

    def user_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"


admin.site.register(MikeSchultzSkateDate, MikeSchultzSkateDateAdmin)
admin.site.register(MikeSchultzSkateSession, MikeSchultzSkateSessionAdmin)
