from django.db import models, IntegrityError
from django.contrib.auth import get_user_model
User = get_user_model()

class SkateDate(models.Model):
    '''A scheduled Thane Storck skate (date plus start/end time strings like "8:00 PM").'''

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

    def registered_skaters(skate_date):
        '''Returns the number of skaters and goalies registered for a skate date.

        Called on the class (SkateDate.registered_skaters(pk)); it has no self.
        '''
        num_goalies = SkateSession.objects.filter(skate_date=skate_date, goalie=True).count()
        num_skaters = SkateSession.objects.filter(skate_date=skate_date, goalie=False).count()
        return {'num_skaters': num_skaters, 'num_goalies': num_goalies}


class SkateSession(models.Model):
    '''One user's sign-up for one SkateDate.'''

    # Model Fields
    skater = models.ForeignKey(User, on_delete=models.CASCADE)
    skate_date = models.ForeignKey(SkateDate, on_delete=models.CASCADE, related_name='session_skaters')
    goalie = models.BooleanField(default=False)
    paid = models.BooleanField(default=False)

    class Meta:
        # Prevent duplicate entries
        unique_together = ['skater', 'skate_date']
        ordering = ['-skate_date']
