from django.db import models
from django.contrib.auth import get_user_model
User = get_user_model()


class FigureSkatingDate(models.Model):
    '''Model holds dates for Open Figure Skating.'''

    #Model Fields
    skate_date = models.DateField()
    start_time = models.CharField(max_length=10)
    end_time = models.CharField(max_length=10)
    available_spots = models.IntegerField(default=0)

    class Meta:
        # Default ordering skate_date descending
        ordering = ['skate_date']
        # Prevent duplicate dates
        unique_together = ['skate_date', 'start_time', 'end_time']

    def __str__(self):
        return f"{self.skate_date} @ {self.start_time}"


class FigureSkater(models.Model):
    '''Model stores figure skater name and dob.'''

    # Model Fields
    guardian = models.ForeignKey(User, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=25)
    last_name = models.CharField(max_length=50)
    date_of_birth = models.DateField(blank=True)

    class Meta:
        # Prevent duplicate skater entries
        unique_together = ['guardian', 'first_name', 'last_name', 'date_of_birth']
        # Default ordering
        ordering = ['guardian']

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class FigureSkatingSession(models.Model):
    '''Model stores figure skating session data.'''

    # Model Fields
    guardian = models.ForeignKey(User, on_delete=models.CASCADE)
    skater = models.ForeignKey(FigureSkater, on_delete=models.CASCADE)
    session = models.ForeignKey(FigureSkatingDate, on_delete=models.CASCADE)
    paid = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.skater} {self.session} {self.paid}"

    class Meta:
        # Prevent duplicate session entries
        unique_together = ['skater', 'session']
        # Default ordering
        ordering = ['-session__skate_date']
