from django.contrib import admin
from .models import Profile, ReleaseOfLiability, ChildSkater

# Register your models here.

class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user_name', 'open_hockey_email', 'stick_and_puck_email', 'figure_skating_email', 
                    'thane_storck_email', 'adult_skills_email', 'mike_schultz_email', 'yeti_skate_email']
    readonly_fields = ['slug', 'user', 'open_hockey_email', 'stick_and_puck_email', 'figure_skating_email', 'thane_storck_email', 
                    'adult_skills_email', 'mike_schultz_email', 'yeti_skate_email']

    def user_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"


class ReleaseOfLiabilityAdmin(admin.ModelAdmin):
    list_display = ['user_name', 'release_of_liability', 'release_of_liability_date_signed']
    readonly_fields = ['user', 'user_name', 'release_of_liability', 'release_of_liability_date_signed']
    search_fields = ['user__first_name', 'user__last_name']

    def user_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"


class ChildSkaterAdmin(admin.ModelAdmin):
    list_display = ['user_name', 'first_name', 'last_name', 'date_of_birth']
    # readonly_fields = ['user', 'user_name', 'first_name', 'last_name', 'date_of_birth']

    def user_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"

admin.site.register(Profile, ProfileAdmin)
admin.site.register(ReleaseOfLiability, ReleaseOfLiabilityAdmin)
admin.site.register(ChildSkater, ChildSkaterAdmin)
