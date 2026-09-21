'''One-off script: pull OWHL entries for a hard-coded date range from ScheduleWerks
into OWHLSkateDate. Unlike the sibling scrapers it is not weekday-gated and sends no email.'''
from datetime import date, timedelta
import os, sys, json, requests

if os.name == 'nt':
    sys.path.append("C:\\Users\\brian\\Documents\\Python\\OIC_Web_Apps\\")
else:
    sys.path.append("/home/OIC/OIC_Web_Apps/")
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'OIC_Web_Apps.settings')

import django
django.setup()

from django.db import IntegrityError
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from owhl.models import OWHLSkateDate, OWHLSkateSession
from accounts.models import Profile, UserCredit
from programs.models import Program


skate_dates = []


def get_schedule_data(from_date, to_date):
    '''Fetches the ScheduleWerks calendar and appends OWHL entries to skate_dates.'''
    
    url = f"https://ozaukeeicecenter.schedulewerks.com/public/ajax/swCalGet?tid=-1&from={from_date}&to={to_date}&Complex=-1"

    try:
        response = requests.get(url)
        data = json.loads(response.text)
    except requests.exceptions.RequestException as e:
        return

    for item in data:
        if "OWHL" in item["text"]:
            # start_date is "MM/DD/YYYY HH:MM"; convert to ISO date
            skate_date = item["start_date"].split(" ")[0]
            skate_date = f"{skate_date[6:]}-{skate_date[:2]}-{skate_date[3:5]}"
            start_time = item["st"].replace("P", " PM").replace("A", " AM")
            end_time = item["et"].replace("P", " PM").replace("A", " AM")

            skate_dates.append([skate_date, start_time, end_time])
    return


def add_skate_dates(sessions):
    '''Adds OWHL Hockey skate dates and times to the OWHLSkateDate model.

    Returns whether the LAST session was new (see backlog).
    '''
    model = OWHLSkateDate

    for session in sessions:
        try:
            data = model(skate_date=session[0], start_time=session[1], end_time=session[2])
            data.save()
            new_dates = True
        except IntegrityError:
            new_dates = False
            continue
    return new_dates


if __name__ == "__main__":

    # Hard-coded range from the last manual run
    from_date = "02/16/2023"
    to_date = "03/15/2023"
    
    get_schedule_data(from_date, to_date)

    if len(skate_dates) != 0:
        add_skate_dates(skate_dates)
