from django.db import models

# Create your models here.

class RinkSchedule(models.Model):
    '''Model that holds daily rink schedule.'''
    schedule_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    rink = models.CharField(max_length=15)
    event = models.CharField(max_length=100, help_text="Field format for two teams: Put home team first and separate with \' vs \', a space then, lowercase vs, then a space")
    home_locker_room = models.CharField(max_length=50, null=True, blank=True)
    visitor_locker_room = models.CharField(max_length=50, null=True, blank=True)
    notes = models.CharField(max_length=50, blank=True)

    class Meta:
        ordering = ['end_time']
        unique_together = ['schedule_date', 'start_time', 'end_time', 'rink']
        verbose_name_plural = 'Rink Schedule'

    def __str__(self):
        return f"{self.schedule_date} Start: {self.start_time}, End: {self.end_time}, Rink: {self.rink}, Event: {self.event}, Notes: {self.notes}"
