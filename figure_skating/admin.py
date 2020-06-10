from django.contrib import admin
from .models import FigureSkater, FigureSkatingDate, FigureSkatingSession

# Register your models here.

class FigureSkaterAdmin(admin.ModelAdmin):
    list_display = ['guardian', 'first_name', 'last_name', 'date_of_birth']


class FigureSkatingDateAdmin(admin.ModelAdmin):
    list_display = ['skate_date', 'start_time', 'end_time', 'available_spots']


class FigureSkatingSessionAdmin(admin.ModelAdmin):
    list_display = ['guardian', 'skater', 'session', 'paid']


admin.site.register(FigureSkater, FigureSkaterAdmin)
admin.site.register(FigureSkatingDate, FigureSkatingDateAdmin)
admin.site.register(FigureSkatingSession, FigureSkatingSessionAdmin)
