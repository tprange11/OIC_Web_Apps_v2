from django.db import models


class Program(models.Model):
    '''Model holds details for OIC skating programs.'''

    # Model Fields
    program_name = models.CharField(max_length=100, unique=True)
    max_skaters = models.IntegerField(blank=True, null=True, default=22)
    max_goalies = models.IntegerField(blank=True, null=True)
    skater_price = models.IntegerField(blank=True, null=True)
    goalie_price = models.IntegerField(blank=True, null=True)

    class Meta:
        ordering = ['pk']

    def __str__(self):
        return f'{ self.program_name }'
