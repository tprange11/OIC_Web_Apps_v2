from django.contrib import admin
from adult_skills.models import AdultSkillsSkateDate, AdultSkillsSkateSession

# Register your models here.


class AdultSkillsSkateDateAdmin(admin.ModelAdmin):
    list_display = ['skate_date', 'start_time', 'end_time']


class AdultSkillsSkateSessionAdmin(admin.ModelAdmin):
    list_display = ['skater_name', 'skate_date_display', 'goalie', 'paid']

    def skater_name(self, obj):
        return f"{obj.skater.first_name} {obj.skater.last_name}"

    def skate_date_display(self, obj):
        return f"{obj.skate_date.skate_date} {obj.skate_date.start_time} to {obj.skate_date.end_time}"


admin.site.register(AdultSkillsSkateDate, AdultSkillsSkateDateAdmin)
admin.site.register(AdultSkillsSkateSession, AdultSkillsSkateSessionAdmin)
