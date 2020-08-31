from django.contrib import admin
from .models import BaldEaglesSession, BaldEaglesSkateDate


class BaldEaglesSkateDateAdmin(admin.ModelAdmin):
    list_display = ['skate_date', 'start_time', 'end_time']


class BaldEaglesSessionAdmin(admin.ModelAdmin):
    list_display = ['skater_name', 'session_date_display', 'goalie', 'paid']
    list_filter = ['session_date']
    search_fields = ['skater__last_name', 'skater__first_name']

    def skater_name(self, obj):
        return f"{obj.skater.first_name} {obj.skater.last_name}"

    def session_date_display(self, obj):
        return f"{obj.session_date.skate_date} {obj.session_date.start_time} to \
            {obj.session_date.end_time}"


admin.site.register(BaldEaglesSkateDate, BaldEaglesSkateDateAdmin)
admin.site.register(BaldEaglesSession, BaldEaglesSessionAdmin)
