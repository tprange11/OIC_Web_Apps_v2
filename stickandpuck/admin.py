from django.contrib import admin
from stickandpuck.models import StickAndPuckDate, StickAndPuckSession, StickAndPuckSkater
# Register your models here.

class StickAndPuckSessionAdmin(admin.ModelAdmin):
    list_display = ['guardian_name', 'skater', 'session_date', 'session_time', 'paid']
    search_fields = ['guardian__first_name', 'guardian__last_name', 'skater__first_name', 'skater__last_name', 'session_date']
    # list_filter = ['session_date']

    def guardian_name(self, obj):
        return f"{obj.guardian.first_name} {obj.guardian.last_name}"


class StickAndPuckSkaterAdmin(admin.ModelAdmin):
    list_display = ['guardian_name', 'first_name', 'last_name', 'date_of_birth']

    def guardian_name(self, obj):
        return f"{obj.guardian.first_name} {obj.guardian.last_name}"


class StickAndPuckDateAdmin(admin.ModelAdmin):
    list_display = ['session_date', 'session_start_time', 'session_end_time', 'session_notes']


admin.site.register(StickAndPuckDate, StickAndPuckDateAdmin)
admin.site.register(StickAndPuckSession, StickAndPuckSessionAdmin)
admin.site.register(StickAndPuckSkater, StickAndPuckSkaterAdmin)
