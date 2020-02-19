import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'OIC_Web_Apps.settings')

import django
django.setup()

from django.db import IntegrityError
from open_hockey.models import OpenHockeyMember, OpenHockeySessions
from datetime import date, timedelta

the_date = date.today()
# List that holds the Tuesday and Friday open hockey dates for the current week
open_hockey_dates = []


def get_open_hockey_dates(the_date):
    '''Get the open hockey dates for the week.'''

    while the_date.weekday() < 5:
        if the_date.weekday() == 1:
            open_hockey_dates.append(the_date)
        if the_date.weekday() == 4:
            open_hockey_dates.append(the_date)
        the_date += timedelta(days=1)
    return

def add_members_to_open_hockey_sessions():
    '''Add active open hockey members to this weeks open hockey sessions.'''
    model = OpenHockeyMember
    members = model.objects.all()

    for member in members:
        if member.active == True:
            for each_date in open_hockey_dates:
                try:
                    session = OpenHockeySessions(skater=member.member, date=each_date, goalie=False, paid=True)
                    session.save()
                except IntegrityError:
                    continue

def set_expired_members_inactive():
    '''If the member end_date has passed, set active field to false.'''

    model = OpenHockeyMember
    inactive_members = model.objects.filter(end_date__lt=date.today(), active=True).update(active=False)
    return

if __name__ == "__main__":
    get_open_hockey_dates(the_date)
    add_members_to_open_hockey_sessions()
    set_expired_members_inactive()
