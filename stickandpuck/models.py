from django.db import models, IntegrityError
from django.urls import reverse
from django.contrib.auth import get_user_model
User = get_user_model()

# Create your models here.


class StickAndPuckSkater(models.Model):
    '''Model that holds skater information'''
    guardian = models.ForeignKey(User, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=25)
    last_name = models.CharField(max_length=50)
    date_of_birth = models.DateField(blank=False)

    class Meta:
        # Prevents duplicate skater entries
        unique_together = [['guardian', 'first_name', 'last_name', 'date_of_birth']]
        # Default ordering
        ordering = ['guardian']

    def __str__(self):
        '''Overrides string representation in admin site'''
        return f"{self.first_name} {self.last_name}"

    def get_absolute_url(self):
        '''Returns user to Stick and Puck Skater List after successfully adding a skater'''
        return reverse('stickandpuck:stick-and-puck')


class StickAndPuckSession(models.Model):
    '''Model that holds stick and puck sessions data'''
    guardian = models.ForeignKey(User, on_delete=models.CASCADE)
    skater = models.ForeignKey(StickAndPuckSkater, on_delete=models.CASCADE)
    session_date = models.DateField()
    session_time = models.CharField(max_length=10)
    paid = models.BooleanField(default=False)

    def __str__(self):
        '''Overrides string representation in admin site'''
        return f"Session Date/Time: {str(self.session_date)} {self.session_time}, Skater: {self.skater} Guardian: {self.guardian.get_full_name()}"

    class Meta:
        # Prevents duplicate stick and puck session entries
        unique_together = [['guardian', 'skater', 'session_date', 'session_time']]
        # Default ordering descending session_date, then by session_time
        ordering = ['-session_date', 'session_time']


class StickAndPuckDate(models.Model):
    '''Model that holds stick and puck session dates'''
    session_date = models.DateField()
    session_start_time = models.CharField(max_length=10)
    session_end_time = models.CharField(max_length=10)
    session_notes = models.CharField(max_length=256)

    class Meta:
        # Default ordering descending session_date
        ordering = ['-session_date']
        # Prevents duplicate stick and puck session dates
        unique_together = [['session_date', 'session_start_time', 'session_end_time']]

    def __str__(self):
        '''Overrides string representation in admin site'''
        return f"{self.session_date} Start: {self.session_start_time} End: {self.session_end_time} Notes: {self.session_notes}"
