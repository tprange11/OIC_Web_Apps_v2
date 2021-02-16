from rest_framework import serializers
from .models import RinkSchedule


class RinkScheduleSerializer(serializers.ModelSerializer):

    class Meta:
        model = RinkSchedule
        fields = ['id', 'schedule_date', 'start_time', 'end_time', 'rink', 'event', 'home_locker_room', 'visitor_locker_room']
