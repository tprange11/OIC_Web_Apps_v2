from django.db import models
from django.contrib.auth import get_user_model
User = get_user_model()

from accounts.models import ChildSkater

class OpenRollerSkateDate(models.Model):
    '''A scheduled Open Roller Hockey skate (date plus start/end time strings like "8:00 PM").'''

    # Model Fields
    skate_date = models.DateField()
    start_time = models.CharField(max_length=10)
    end_time = models.CharField(max_length=10)

    class Meta:
        ordering = ['skate_date']
        # Prevent duplicate dates
        unique_together = ['skate_date', 'start_time', 'end_time']

    def __str__(self):
        return f"{self.skate_date}"


class OpenRollerSkateSession(models.Model):
    '''One ChildSkater's sign-up for one skate date, registered by user.'''

    # Model Fields
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    skater = models.ForeignKey(ChildSkater, on_delete=models.CASCADE, null=True)
    skate_date = models.ForeignKey(OpenRollerSkateDate, on_delete=models.CASCADE, related_name='session_skaters')
    goalie = models.BooleanField(default=False)
    paid = models.BooleanField(default=False)

    class Meta:
        # Prevent duplicate entries
        unique_together = ['user', 'skater', 'skate_date']
        ordering = ['-skate_date']
