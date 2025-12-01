from django.contrib import admin
from yeti_skate.models import YetiSkateDate, YetiSkateSession, YetiSkateNewSkater

# Register your models here.


class YetiSkateDateAdmin(admin.ModelAdmin):
    list_display = ['skate_date', 'start_time', 'end_time']


class YetiSkateSessionAdmin(admin.ModelAdmin):
    list_display = ['skater_name', 'skate_date_display', 'goalie', 'paid']
    # list_filter = ['skate_date']
    search_fields = ['skater__last_name', 'skater__first_name', 'skate_date__skate_date']

    def skater_name(self, obj):
        return f"{obj.skater.first_name} {obj.skater.last_name}"

    def skate_date_display(self, obj):
        return f"{obj.skate_date.skate_date} {obj.skate_date.start_time} to {obj.skate_date.end_time}"


class YetiSkateNewSkaterAdmin(admin.ModelAdmin):
    list_display = ['skater_name']
    
    def skater_name(self, obj):
        return f"{obj.skater.first_name} {obj.skater.last_name}"


admin.site.register(YetiSkateDate, YetiSkateDateAdmin)
admin.site.register(YetiSkateSession, YetiSkateSessionAdmin)
admin.site.register(YetiSkateNewSkater, YetiSkateNewSkaterAdmin)
