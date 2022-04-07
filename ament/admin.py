from django.contrib import admin
from ament.models import AmentSkateDate, AmentSkateSession

# Register your models here.


class AmentSkateDateAdmin(admin.ModelAdmin):
    list_display = ['skate_date', 'start_time', 'end_time']


class AmentSkateSessionAdmin(admin.ModelAdmin):
    list_display = ['skater_name', 'skate_date_display', 'goalie', 'paid']
    list_filter = ['skate_date']
    search_fields = ['skater__last_name', 'skater__first_name']

    def skater_name(self, obj):
        return f"{obj.skater.first_name} {obj.skater.last_name}"

    def skate_date_display(self, obj):
        return f"{obj.skate_date.skate_date} {obj.skate_date.start_time} to {obj.skate_date.end_time}"


admin.site.register(AmentSkateDate, AmentSkateDateAdmin)
admin.site.register(AmentSkateSession, AmentSkateSessionAdmin)
