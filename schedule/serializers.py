from rest_framework import serializers
from .models import RinkSchedule

# from datetime import datetime, date


class RinkScheduleSerializer(serializers.ModelSerializer):

    start_time = serializers.TimeField(format='%I:%M %p')
    end_time = serializers.TimeField(format='%I:%M %p')

    class Meta:
        model = RinkSchedule
        fields = ['id', 'schedule_date', 'start_time', 'end_time', 'rink', 'event', 'home_locker_room', 'visitor_locker_room']
