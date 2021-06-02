from django.contrib import admin
from owhl.models import OWHLSkateDate, OWHLSkateSession


class OWHLSkateDateAdmin(admin.ModelAdmin):
    list_display = ['skate_date', 'start_time', 'end_time']


class OWHLSkateSessionAdmin(admin.ModelAdmin):
    list_display = ['skater', 'skate_date', 'goalie', 'paid']
    list_filter = ['skate_date']
    search_fields = ['skater__first_name', 'skater__last_name']


admin.site.register(OWHLSkateDate, OWHLSkateDateAdmin)
admin.site.register(OWHLSkateSession, OWHLSkateSessionAdmin)
