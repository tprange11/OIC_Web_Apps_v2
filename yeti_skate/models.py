from django.db import models, IntegrityError
from django.contrib.auth import get_user_model
User = get_user_model()

class YetiSkateDate(models.Model):
    '''Model holds dates for the Yeti Skate.'''

    # Model Fields
    skate_date = models.DateField()
    start_time = models.CharField(max_length=10)
    end_time = models.CharField(max_length=10)

    class Meta:
        # Default ordering skate_date descending
        ordering = ['skate_date']
        # Prevent duplicate dates
        unique_together = ['skate_date', 'start_time', 'end_time']

    def __str__(self):
        return f"{self.skate_date}"

    def skates_a_go(skate_date):
        return YetiSkateSession.objects.filter(skate_date=skate_date, goalie=False).count() >= 5


class YetiSkateSession(models.Model):
    '''Model that stores skate session data.'''

    # Model Fields
    skater = models.ForeignKey(User, on_delete=models.CASCADE)
    skate_date = models.ForeignKey(YetiSkateDate, on_delete=models.CASCADE, related_name='session_skaters')
    goalie = models.BooleanField(default=False)
    paid = models.BooleanField(default=False)

    class Meta:
        # Prevent duplicate entries
        unique_together = ['skater', 'skate_date']
        # Default ordering date descending
        ordering = ['-skate_date']
