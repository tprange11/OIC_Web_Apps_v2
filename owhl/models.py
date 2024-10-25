from django.db import models
from django.contrib.auth import get_user_model
User = get_user_model()

class OWHLSkateDate(models.Model):
    '''Model holds dates for the OWHL hockey.'''

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

    def registered_skaters(skate_date):
        '''Returns the number of skaters and goalies registered for a skate date.'''
        num_goalies = OWHLSkateSession.objects.filter(skate_date=skate_date, goalie=True).count()
        num_skaters = OWHLSkateSession.objects.filter(skate_date=skate_date, goalie=False).count()
        return {'num_skaters': num_skaters, 'num_goalies': num_goalies}


class OWHLSkateSession(models.Model):
    '''Model that stores skate session data.'''

    # Model Fields
    skater = models.ForeignKey(User, on_delete=models.CASCADE)
    skate_date = models.ForeignKey(OWHLSkateDate, on_delete=models.CASCADE, related_name='session_skaters')
    goalie = models.BooleanField(default=False)
    paid = models.BooleanField(default=False)

    class Meta:
        # Prevent duplicate entries
        unique_together = ['skater', 'skate_date']
        # Default ordering date descending
        ordering = ['-skate_date']
