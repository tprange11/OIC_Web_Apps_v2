from django.contrib import admin
from .models import Profile

# Register your models here.

class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user_name', 'open_hockey_email', 'stick_and_puck_email', 'figure_skating_email']
    readonly_fields = ['open_hockey_email', 'stick_and_puck_email', 'figure_skating_email']

    def user_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"

admin.site.register(Profile, ProfileAdmin)
