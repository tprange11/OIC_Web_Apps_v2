from django.db import models, IntegrityError
from django.urls import reverse
from django.contrib.auth import get_user_model
User = get_user_model()


class StickAndPuckSkater(models.Model):
    '''A skater (usually a minor) registered under a guardian user.'''
    guardian = models.ForeignKey(User, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=25)
    last_name = models.CharField(max_length=50)
    date_of_birth = models.DateField(blank=False)

    class Meta:
        # Prevents duplicate skater entries
        unique_together = [['guardian', 'first_name', 'last_name', 'date_of_birth']]
        ordering = ['guardian']

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    def get_absolute_url(self):
        '''Stick and puck index page (the create view overrides success_url to the skater list).'''
        return reverse('stickandpuck:stick-and-puck')


class StickAndPuckSession(models.Model):
    '''One skater's sign-up for one stick and puck session (date + time).'''
    guardian = models.ForeignKey(User, on_delete=models.CASCADE)
    skater = models.ForeignKey(StickAndPuckSkater, on_delete=models.CASCADE)
    session_date = models.DateField()
    session_time = models.CharField(max_length=10)
    paid = models.BooleanField(default=False)

    def __str__(self):
        return f"Session Date/Time: {str(self.session_date)} {self.session_time}, Skater: {self.skater} Guardian: {self.guardian.get_full_name()}"

    class Meta:
        # Prevents duplicate stick and puck session entries
        unique_together = [['guardian', 'skater', 'session_date', 'session_time']]
        ordering = ['-session_date', 'session_time']


class StickAndPuckDate(models.Model):
    '''A scheduled stick and puck session (date, start/end time, age-group note).'''
    session_date = models.DateField()
    session_start_time = models.CharField(max_length=10)
    session_end_time = models.CharField(max_length=10)
    session_notes = models.CharField(max_length=256)

    class Meta:
        ordering = ['-session_date']
        # Prevents duplicate stick and puck session dates
        unique_together = [['session_date', 'session_start_time', 'session_end_time']]

    def __str__(self):
        return f"{self.session_date} Start: {self.session_start_time} End: {self.session_end_time} Notes: {self.session_notes}"
