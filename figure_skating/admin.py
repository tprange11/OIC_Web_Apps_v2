from django.contrib import admin
from .models import FigureSkater, FigureSkatingDate, FigureSkatingSession

# Register your models here.

class FigureSkaterAdmin(admin.ModelAdmin):
    list_display = ['guardian', 'first_name', 'last_name', 'date_of_birth']


class FigureSkatingDateAdmin(admin.ModelAdmin):
    search_fields = ['skate_date']
    list_display = ['skate_date', 'start_time', 'end_time', 'available_spots', 'up_down_charge']


class FigureSkatingSessionAdmin(admin.ModelAdmin):
    list_display = ['guardian_name', 'skater', 'session', 'paid']
    list_filter = ['session']
    search_fields = ['guardian__first_name', 'guardian__last_name', 'skater__first_name', 'skater__last_name', 'session__skate_date']

    def guardian_name(self, obj):
        return f"{obj.guardian.first_name} {obj.guardian.last_name}"


admin.site.register(FigureSkater, FigureSkaterAdmin)
admin.site.register(FigureSkatingDate, FigureSkatingDateAdmin)
admin.site.register(FigureSkatingSession, FigureSkatingSessionAdmin)
