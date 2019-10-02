from django.contrib import admin
from stickandpuck.models import StickAndPuckDates, StickAndPuckSessions, StickAndPuckSkaters
# Register your models here.

admin.site.register(StickAndPuckDates)
admin.site.register(StickAndPuckSessions)
admin.site.register(StickAndPuckSkaters)