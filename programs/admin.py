from django.contrib import admin
from .models import Program


class ProgramAdmin(admin.ModelAdmin):
    list_display = ['program_name', 'max_skaters', 'max_goalies', 'skater_price', 'goalie_price']


admin.site.register(Program, ProgramAdmin)
