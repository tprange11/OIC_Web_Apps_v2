from django.db import models
from django.contrib.auth import get_user_model
User = get_user_model()


class NachoSkateDate(models.Model):
    '''A scheduled Nacho skate. Uses real TimeFields, unlike the CharField times in the sibling apps.'''

    # Model Fields
    skate_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()

    class Meta:
        ordering = ['skate_date']
        # Prevent duplicate dates
        unique_together = ['skate_date', 'start_time', 'end_time']

    def __str__(self):
        return f"{self.skate_date}"

    def registered_skaters(skate_date):
        '''Returns the number of skaters and goalies registered for a skate date.

        Called on the class (NachoSkateDate.registered_skaters(pk)); it has no self.
        '''
        num_goalies = NachoSkateSession.objects.filter(skate_date=skate_date, goalie=True).count()
        num_skaters = NachoSkateSession.objects.filter(skate_date=skate_date, goalie=False).count()
        return {'num_skaters': num_skaters, 'num_goalies': num_goalies}


class NachoSkateSession(models.Model):
    '''One user's sign-up for one NachoSkateDate.'''

    # Model Fields
    skater = models.ForeignKey(User, on_delete=models.CASCADE)
    skate_date = models.ForeignKey(NachoSkateDate, on_delete=models.CASCADE, related_name='session_skaters')
    goalie = models.BooleanField(default=False)
    paid = models.BooleanField(default=False)

    class Meta:
        # Prevent duplicate entries
        unique_together = ['skater', 'skate_date']
        ordering = ['-skate_date']


class NachoSkateRegular(models.Model):
    '''Skaters that fetch_nacho_skate_dates.py auto-registers for every new skate date.

    They are only added when their credit balance covers the skater price (user
    credit pk 870 is exempt).
    '''

    regular = models.ForeignKey(User, on_delete=models.CASCADE)
