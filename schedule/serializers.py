from rest_framework import serializers
from .models import RinkSchedule

from datetime import datetime, date


class RinkScheduleSerializer(serializers.ModelSerializer):
    '''Schedule rows for the JSON API; times are 12-hour strings and countdown_time is
    today's date joined to the start time, in the format the countdown JS expects.'''

    start_time = serializers.TimeField(format='%I:%M %p')
    end_time = serializers.TimeField(format='%I:%M %p')
    countdown_time = serializers.SerializerMethodField()

    class Meta:
        model = RinkSchedule
        fields = ['id', 'schedule_date', 'start_time', 'end_time', 'countdown_time', 'rink', 'event', 'home_locker_room', 'visitor_locker_room']

    def get_countdown_time(self, obj):
        return date.isoformat(datetime.now())+" "+obj.start_time.strftime('%H:%M:%S')
