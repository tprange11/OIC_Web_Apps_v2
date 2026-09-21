from django.db import models, IntegrityError
from django.urls import reverse
from django.contrib.auth import get_user_model
User = get_user_model()

from datetime import datetime


class OpenHockeySessionsManager(models.Manager):
    '''Manager class for OpenHockeySessions Model'''

    def goalie_count(self, session_date):
        '''Number of goalies signed up for a session date.'''
        goalies = self.all().filter(date=session_date, goalie=True).count()
        return goalies

    def skater_count(self, session_date):
        '''Number of skaters (non-goalies) signed up for a session date.'''
        skaters = self.all().filter(date=session_date, goalie=False).count()
        return skaters

    def get_session_participants(self, session_date):
        '''All sign-ups for a session date.'''
        participants = self.all().filter(date=session_date)
        return participants

    def get_skater_sessions(self, username, the_date):
        '''Sessions a user is signed up for on or after the_date, oldest first.'''
        skater_sessions = self.all().filter(skater=username, date__gte=the_date).order_by('date')
        return skater_sessions

class OpenHockeySessions(models.Model):
    '''One user's sign-up for one open hockey session date.'''

    # Model fields
    skater = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    date = models.DateField()
    goalie = models.BooleanField(default=False)
    paid = models.BooleanField(default=False)
    objects = OpenHockeySessionsManager()

    def __str__(self):
        if self.goalie:
            string = f"{str(self.date)}, {self.skater.first_name} {self.skater.last_name}, GOALIE"
        else:
            string = f"{str(self.date)}, {self.skater.first_name} {self.skater.last_name}"
        return string
    
    class Meta:
        # A skater can't sign up twice for the same session
        unique_together = [['skater', 'date']]
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

    def __str__(self):
        return f"{self.member.last_name}, {self.member.first_name}, Membership ends: {self.end_date}"

    def get_absolute_url(self):
        '''Where CreateOpenHockeyMemberView redirects after a successful save.'''
        return reverse('open_hockey:member-detail')


    class Meta:
        ordering = ['-end_date']
        # One membership row per user
        unique_together = [['member']]
