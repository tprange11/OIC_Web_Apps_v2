from django.db import models

# Create your models here.

class RinkSchedule(models.Model):
    '''Model that holds daily rink schedule.'''
    schedule_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    rink = models.CharField(max_length=15)
    event = models.CharField(max_length=50)
    notes = models.CharField(max_length=50, blank=True)

    class meta:
        ordering = ['end_time']
        unique_together = [['schedule_date', 'start_time', 'end_time', 'rink']]

    def __str__(self):
        return f"{self.schedule_date} Start: {self.start_time}, End: {self.end_time}, Rink: {self.rink}, Event: {self.event}, Notes: {self.notes}"