from django.contrib import admin
from .models import Profile, ReleaseOfLiability, ChildSkater, UserCredit

# Register your models here.

class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user_name']
    list_filter = ['open_hockey_email', 'stick_and_puck_email', 'figure_skating_email', 'thane_storck_email', 
                    'adult_skills_email', 'mike_schultz_email', 'yeti_skate_email', 'womens_hockey_email',
                    'bald_eagles_email', 'lady_hawks_email', 'chs_alumni_email', 'kranich_email', 'nacho_skate_email']
    readonly_fields = ['slug', 'user']
    # readonly_fields = ['slug', 'user', 'open_hockey_email', 'stick_and_puck_email', 'figure_skating_email',
    #                 'thane_storck_email', 'adult_skills_email', 'mike_schultz_email', 'yeti_skate_email', 
    #                 'womens_hockey_email', 'bald_eagles_email', 'lady_hawks_email', 'chs_alumni_email']
    search_fields = ['user__first_name', 'user__last_name', 'slug']

    def user_name(self, obj):
        return f"{obj.user.get_full_name()}"


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

class UserCreditAdmin(admin.ModelAdmin):
    fields = ['user', 'slug', 'balance', 'pending', 'paid']
    list_display = ['user_name', 'balance', 'pending', 'paid']
    readonly_fields = ['user', 'slug']
    search_fields = ['user__first_name', 'user__last_name']

    def user_name(self, obj):
        return f"{obj.user.get_full_name()}"


admin.site.register(Profile, ProfileAdmin)
admin.site.register(ReleaseOfLiability, ReleaseOfLiabilityAdmin)
admin.site.register(ChildSkater, ChildSkaterAdmin)
admin.site.register(UserCredit, UserCreditAdmin)
