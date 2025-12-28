from django.contrib import admin
from schedule.models import RinkSchedule, LockerRoomRule, NameNormalizationRule


class RinkScheduleAdmin(admin.ModelAdmin):
    list_display = [
        'schedule_date',
        'start_time',
        'end_time',
        'rink',
        'event',
        'home_locker_room',
        'visitor_locker_room',
    ]
    search_fields = ['schedule_date']


admin.site.register(RinkSchedule, RinkScheduleAdmin)


@admin.register(LockerRoomRule)
class LockerRoomRuleAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "priority",
        "rink",
        "team_contains",
        "home_locker_room",
        "visitor_locker_room",
        "active",
    )
    list_filter = ("active", "rink")
    search_fields = ("team_contains",)
    ordering = ("priority",)

@admin.register(NameNormalizationRule)
class NameNormalizationRuleAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "priority",
        "match_text",
        "replace_with",
        "active",
        "updated_dt",
    )
    list_filter = ("active",)
    search_fields = ("match_text", "replace_with")
    ordering = ("priority",)
