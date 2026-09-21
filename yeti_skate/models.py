from django.db import models
from django.contrib.auth import get_user_model
User = get_user_model()


class YetiSkateDate(models.Model):
    '''A scheduled Yeti skate. Times are free-text: the scraper writes "06:00:00" here
    while the sibling apps store "6:00 AM" style strings (see backlog).'''

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

        Called on the class (YetiSkateDate.registered_skaters(pk)); it has no self.
        '''
        num_goalies = YetiSkateSession.objects.filter(skate_date=skate_date, goalie=True).count()
        num_skaters = YetiSkateSession.objects.filter(skate_date=skate_date, goalie=False).count()
        return {'num_skaters': num_skaters, 'num_goalies': num_goalies}


class YetiSkateSession(models.Model):
    '''One user's sign-up for one YetiSkateDate.'''

    # Model Fields
    skater = models.ForeignKey(User, on_delete=models.CASCADE)
    skate_date = models.ForeignKey(YetiSkateDate, on_delete=models.CASCADE, related_name='session_skaters')
    goalie = models.BooleanField(default=False)
    paid = models.BooleanField(default=False)


    class Meta:
        # Prevent duplicate entries
        unique_together = ['skater', 'skate_date']
        ordering = ['-skate_date']


class YetiSkateNewSkater(models.Model):
    '''Users listed here are "new skaters" and may only register for Friday skates on Thursday.'''

    skater = models.ForeignKey(User, on_delete=models.CASCADE)
