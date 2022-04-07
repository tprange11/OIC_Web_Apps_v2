from django.contrib import admin
from chs_alumni.models import CHSAlumniDate, CHSAlumniSession

# Register your models here.


class CHSAlumniDateAdmin(admin.ModelAdmin):
    list_display = ['skate_date', 'start_time', 'end_time']


class CHSAlumniSessionAdmin(admin.ModelAdmin):
    list_display = ['skater_name', 'date_display', 'goalie', 'paid']
    list_filter = ['date']
    search_fields = ['skater__last_name', 'skater__first_name']

    def skater_name(self, obj):
        return f"{obj.skater.first_name} {obj.skater.last_name}"

    def date_display(self, obj):
        return f"{obj.date.skate_date} {obj.date.start_time} to {obj.date.end_time}"

# admin.site.register(CHSAlumniDate, CHSAlumniDateAdmin)
# admin.site.register(CHSAlumniSession, CHSAlumniSessionAdmin)
