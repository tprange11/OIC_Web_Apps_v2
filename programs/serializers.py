from django.db import models
from rest_framework import serializers
from .models import Program


class ProgramSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Program
        fields = ['id', 'program_name', 'description', 'message', 'days_and_times', 
                    'max_skaters', 'max_goalies', 'skater_price', 'goalie_price', 
                    'private']
