from django.contrib import admin
from stickandpuck.models import StickAndPuckDates, StickAndPuckSessions, StickAndPuckSkaters
# Register your models here.

class StickAndPuckSessionsAdmin(admin.ModelAdmin):
    list_display = ['guardian_name', 'skater', 'session_date', 'session_time', 'paid']
    search_fields = ['guardian__first_name', 'guardian__last_name', 'skater', 'session_date']

    def guardian_name(self, obj):
        return f"{obj.guardian.first_name} {obj.guardian.last_name}"


class StickAndPuckSkatersAdmin(admin.ModelAdmin):
    list_display = ['guardian_name', 'first_name', 'last_name', 'date_of_birth']

    def guardian_name(self, obj):
        return f"{obj.guardian.first_name} {obj.guardian.last_name}"


class StickAndPuckDatesAdmin(admin.ModelAdmin):
    list_display = ['session_date', 'session_start_time', 'session_end_time', 'session_notes']


admin.site.register(StickAndPuckDates, StickAndPuckDatesAdmin)
admin.site.register(StickAndPuckSessions, StickAndPuckSessionsAdmin)
admin.site.register(StickAndPuckSkaters, StickAndPuckSkatersAdmin)
