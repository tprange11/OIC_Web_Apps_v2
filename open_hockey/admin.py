from django.contrib import admin
from open_hockey.models import OpenHockeySessions, OpenHockeyMember, OpenHockeyMemberType

# Register your models here.

class OpenHockeySessionsAdmin(admin.ModelAdmin):
    list_display = ['skater_name', 'date', 'goalie', 'paid']
    search_fields = ['skater__first_name', 'skater__last_name']

    def skater_name(self, obj):
        return f"{obj.skater.first_name} {obj.skater.last_name}"


class OpenHockeyMemberAdmin(admin.ModelAdmin):
    list_display = ['member_name', 'member_type', 'end_date', 'active']
    search_fields = ['member__first_name', 'member__last_name']

    def member_name(self, obj):
        return f"{obj.member.first_name} {obj.member.last_name}"


class OpenHockeyMemberTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'cost', 'duration']


admin.site.register(OpenHockeySessions, OpenHockeySessionsAdmin)
admin.site.register(OpenHockeyMember, OpenHockeyMemberAdmin)
admin.site.register(OpenHockeyMemberType, OpenHockeyMemberTypeAdmin)
