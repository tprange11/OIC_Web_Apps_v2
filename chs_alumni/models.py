from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.contrib.auth import get_user_model
User = get_user_model()


class CHSAlumniDate(models.Model):
    '''Model holds dates for CHS Alumni Skates.'''

    # Model fields
    skate_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()

    class Meta:
        # Default ordering skate_date descending
        ordering = ['skate_date']
        # Prevent duplicate dates
        unique_together = ['skate_date', 'start_time', 'end_time']
        verbose_name = 'CHS Alumni date'

    def __str__(self):
        return f"{self.skate_date}"

    def registered_skaters(skate_date):
        '''Returns the number of skaters and goalies registered for a skate date.'''
        num_goalies = CHSAlumniSession.objects.filter(date=skate_date, goalie=True).count()
        num_skaters = CHSAlumniSession.objects.filter(date=skate_date, goalie=False).count()
        return {'num_skaters': num_skaters, 'num_goalies': num_goalies}


class CHSAlumniSession(models.Model):
    '''Model stores skate session data.'''

    #Model fields
    skater = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.ForeignKey(CHSAlumniDate, on_delete=models.CASCADE, related_name='session_skaters')
    goalie = models.BooleanField(default=False)
    paid = models.BooleanField(default=False)

    class Meta:
        # Default ordering date descending
        ordering = ['-date']
        # Prevent duplicate entries
        unique_together = ['skater', 'date']
        verbose_name = 'CHS Alumni session'
