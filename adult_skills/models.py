from django.db import models
from django.contrib.auth import get_user_model
User = get_user_model()


class AdultSkillsSkateDate(models.Model):
    '''Model that holds dates for Adult Skills skates.'''

    # Model Fields
    skate_date = models.DateField()
    start_time = models.CharField(max_length=10)
    end_time = models.CharField(max_length=10)

    class Meta:
        #Default ordering
        ordering = ['skate_date']
        # Prevent duplicate dates
        unique_together = ['skate_date', 'start_time', 'end_time']

    def __str__(self):
        return(f"{self.skate_date}")

    def registered_skaters(skate_date):
        '''Returns the number of skaters and goalies registered for a skate date.'''
        num_goalies = AdultSkillsSkateSession.objects.filter(skate_date=skate_date, goalie=True).count()
        num_skaters = AdultSkillsSkateSession.objects.filter(skate_date=skate_date, goalie=False).count()
        return {'num_skaters': num_skaters, 'num_goalies': num_goalies}


class AdultSkillsSkateSession(models.Model):
    '''Model that stores adult skills skate session data.'''

    # Model Fields
    skater = models.ForeignKey(User, on_delete=models.CASCADE)
    skate_date = models.ForeignKey(AdultSkillsSkateDate, on_delete=models.CASCADE)
    goalie = models.BooleanField(default=False)
    paid = models.BooleanField(default=False)

    class Meta:
        # Prevent duplicate entries
        unique_together = ['skater', 'skate_date']
        # Default ordering
        ordering = ['-skate_date']
