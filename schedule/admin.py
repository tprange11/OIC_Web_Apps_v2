from django.contrib import admin
from schedule.models import RinkSchedule
# Register your models here.


class RinkScheduleAdmin(admin.ModelAdmin):
    list_display = ['schedule_date', 'start_time', 'end_time', 'rink', 'event', 'notes']


admin.site.register(RinkSchedule, RinkScheduleAdmin)
