from django.db import models
from django.urls import reverse
from accounts.models import ChildSkater
from django.contrib.auth import get_user_model
User = get_user_model()


class PrivateSkate(models.Model):
    '''Model that holds data for ad-hoc private skates.'''
    name = models.CharField(max_length=75, unique=True)
    max_skaters = models.IntegerField(blank=True, null=True, default=None, help_text="If no maximum, leave blank! Enter 0 for no skaters.")
    max_goalies = models.IntegerField(blank=True, null=True, default=None, help_text="If no maximum, leave blank! Enter 0 for no goalies.")
    skater_price = models.IntegerField(default=12)
    goalie_price = models.IntegerField(default=0)
    slug = models.SlugField(max_length=75, help_text="CREATE A NEW GROUP IN AUTHENTICATION AND AUTHORIZATION WITH THIS SLUG!!!!")

    class Meta:
        ordering = ['name']

    def __str__(self) -> str:
        return self.name


class PrivateSkateDate(models.Model):
    '''Model that holds dates and times for ad-hoc private skates.'''

    # Fields
    private_skate = models.ForeignKey(PrivateSkate, on_delete=models.CASCADE, related_name='skate_dates')
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()

    class Meta:
        ordering = ['date']
        unique_together = ['private_skate', 'date']

    def __str__(self) -> str:
        return f"{self.date}, {self.start_time.strftime('%I:%M %p')} to {self.end_time.strftime('%I:%M %p')}"

    def registered_skaters(self, skate_date):
        '''Returns the number of skaters and goalies registered for a skate date.'''
        num_goalies = PrivateSkateSession.objects.filter(skate_date=skate_date, goalie=True).count()
        num_skaters = PrivateSkateSession.objects.filter(skate_date=skate_date, goalie=False).count()
        return {'num_skaters': num_skaters, 'num_goalies': num_goalies}


class PrivateSkateSession(models.Model):
    '''Model that holds skater sessions for private skates.'''

    # Fields
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    skater = models.ForeignKey(ChildSkater, on_delete=models.CASCADE)
    skate_date = models.ForeignKey(PrivateSkateDate, on_delete=models.CASCADE, related_name='session_skaters')
    goalie = models.BooleanField(default=False)
    paid = models.BooleanField(default=False)

    # def get_absolute_url(self):
    #     return reverse('private_skates:skate-dates', kwargs={'slug': PrivateSkate.objects.get(pk=self.skate_date).slug})

    class Meta:
        unique_together = ['user', 'skater', 'skate_date']
        ordering = ['-skate_date']
