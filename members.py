import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'OIC_Web_Apps.settings')

import django
django.setup()

from django.db import IntegrityError
from open_hockey.models import OpenHockeyMember, OpenHockeySessions
from datetime import date, timedelta

the_date = date.today()
open_hockey_dates = []


def get_open_hockey_dates(the_date):
    while the_date.weekday() < 5:
        if the_date.weekday() == 1:
            open_hockey_dates.append(the_date)
        if the_date.weekday() == 4:
            open_hockey_dates.append(the_date)

        the_date += timedelta(days=1)
    # return open_hockey_dates


def add_members_to_open_hockey_sessions():
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

if __name__ == "__main__":
    get_open_hockey_dates(the_date)
    add_members_to_open_hockey_sessions()
