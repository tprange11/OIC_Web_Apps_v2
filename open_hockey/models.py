from django.db import models, IntegrityError
from django.urls import reverse
from django.contrib.auth import get_user_model
User = get_user_model()

from datetime import datetime

# Create your models here.


class OpenHockeySessionsManager(models.Manager):
    '''Manager class for OpenHockeySessions Model'''

    # returns number of goalies signed up for a particular session of open hockey
    def goalie_count(self, session_date):
        goalies = self.all().filter(date=session_date, goalie=True).count()
        return goalies

    # returns number of skaters signed up for a particular session of open hockey
    def skater_count(self, session_date):
        skaters = self.all().filter(date=session_date, goalie=False).count()
        return skaters

    # returns participants of a particular session of open hockey 
    def get_session_participants(self, session_date):
        participants = self.all().filter(date=session_date)
        return participants

    # returns open hockey sessions that a particular skater is signed up for
    def get_skater_sessions(self, username, the_date):
        skater_sessions = self.all().filter(skater=username, date__gte=the_date).order_by('date')
        return skater_sessions

class OpenHockeySessions(models.Model):
    '''OpenHockeySessions model holds open hockey session dates and participants'''

    # Model fields
    skater = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    date = models.DateField()
    goalie = models.BooleanField(default=False)
    paid = models.BooleanField(default=False)
    objects = OpenHockeySessionsManager()

    # Overrides string representation of OpenHockeySessions in the admin site
    def __str__(self):
        if self.goalie:
            string = f"{str(self.date)}, {self.skater.first_name} {self.skater.last_name}, GOALIE"
        else:
            string = f"{str(self.date)}, {self.skater.first_name} {self.skater.last_name}"
        return string
    
    class Meta:
        # requires that skater and date be a unique pair, skater can't sign up twice for the same session
        unique_together = [['skater', 'date']]
        # default ordering is in descending date order
        ordering = ['-date']


class OpenHockeyMemberType(models.Model):
    '''Model that holds the different Open Hockey Membership types'''

    # Model Fields
    name = models.CharField(max_length=25)
    cost = models.IntegerField()
    duration = models.IntegerField(help_text='Number of Days')

    def __str__(self):
        return f"{self.name}, Cost ${self.cost}"

    class Meta:
        ordering = ['duration']


class OpenHockeyMember(models.Model):
    '''OpenHockeyMember model is a table of skaters who have prepaid 
    for open hockey for a specified time frame'''

    # Model fields
    member = models.ForeignKey(User, on_delete=models.CASCADE, related_name='member')
    member_type = models.ForeignKey(OpenHockeyMemberType, on_delete=models.CASCADE, null=True)
    end_date = models.DateField()
    active = models.BooleanField()

    # Overrides string representation of OpenHockeyMember in the admin site 
    def __str__(self):
        return f"{self.member.last_name}, {self.member.first_name}, Membership ends: {self.end_date}"

    # The URL that is returned after successfully adding an open hockey member
    def get_absolute_url(self):
        return reverse('open_hockey:member-detail')


    class Meta:
        # Default ordering descending end_date
        ordering = ['-end_date']
        # Members can't be added twice
        unique_together = [['member']]
