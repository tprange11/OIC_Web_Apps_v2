from django.contrib import admin
from .models import Program, UserCreditIncentive


class ProgramAdmin(admin.ModelAdmin):
    list_display = ['program_name', 'max_skaters', 'max_goalies', 'skater_price', 'goalie_price', 'private']


class UserCreditIncentiveAdmin(admin.ModelAdmin):
    list_display = ['price_point', 'incentive']

admin.site.register(Program, ProgramAdmin)
admin.site.register(UserCreditIncentive, UserCreditIncentiveAdmin)
