from datetime import date, timedelta
import os, sys, requests, json

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
from stickandpuck.models import StickAndPuckDate
from accounts.models import Profile

skate_dates = []

def get_schedule_data(from_date, to_date):
    '''Scrapes Ozaukee Ice Center schedule website for stick and puck session dates.'''

    url = f"https://ozaukeeicecenter.schedulewerks.com/public/ajax/swCalGet?tid=-1&from={from_date}&to={to_date}&Complex=-1"

    try:
        response = requests.get(url)
        data = json.loads(response.text)
    except requests.exceptions.RequestException as e:
        # print(e)
        return

    for item in data:
        if "Stick&Puck" in item["text"]:
            skate_date = item["start_date"].split(" ")[0]
            skate_date = f"{skate_date[6:]}-{skate_date[:2]}-{skate_date[3:5]}"
            start_time = item["st"].replace("P", " PM").replace("A", " AM")
            end_time = item["et"].replace("P", " PM").replace("A", " AM")

            skate_dates.append([skate_date, start_time, end_time, ''])

    return

def add_stick_and_puck_dates(sessions):
    '''Adds stick and puck dates, times and session notes to StickAndPuckDate model.'''
    model = StickAndPuckDate

    for session in sessions:
        try:
            data = model(session_date=session[0], session_start_time=session[1], session_end_time=session[2], session_notes=session[3])
            data.save()
            new_dates = True
        except IntegrityError:
            new_dates = False
            continue
    return new_dates

def send_stick_and_puck_dates_email():
    '''Sends email to Users letting them know when stick and puck dates are added.'''
    recipients = Profile.objects.filter(stick_and_puck_email=True).select_related('user')

    for recipient in recipients:
        if recipient.user.is_active:
            to_email = [recipient.user.email]
            from_email = 'no-reply@mg.oicwebapps.com'
            subject = 'New Stick and Puck Session(s) Added'

            # Build the plain text message
            text_message = f'Hi {recipient.user.first_name},\n\n'
            text_message += f'New Stick and Puck sessions are now available online. Sign up at the url below.\n\n'
            text_message += f'https://www.oicwebapps.com/web_apps/stickandpuck/\n\n'
            text_message += f'If you no longer wish to receive these emails, log in to your account,\n'
            text_message += f'click on your username and change the email settings in your profile.\n\n'
            text_message += f'Thank you for using OICWebApps.com!\n\n'

            # Build the html message
            html_message = render_to_string(
                'stick_and_puck_dates_email.html',
                {
                    'recipient_name': recipient.user.first_name,
                }
            )

            # Send email to each recipient separately
            try:
                mail = EmailMultiAlternatives(
                    subject, text_message, from_email, to_email
                )
                mail.attach_alternative(html_message, 'text/html')
                mail.send()
            except:
                return


if __name__ == "__main__":
    
    the_date = date.today()
    from_date = the_date
    to_date = the_date + timedelta(days=5)
    from_date = from_date.strftime("%m/%d/%Y")
    to_date = to_date.strftime("%m/%d/%Y")
    send_email = False

    # Every Wednesday request schedule data for following current and following week and parse for Stick n Puck dates
    if the_date.weekday() == 2:
        get_schedule_data(from_date, to_date)

        if len(skate_dates) != 0:
            # for item in skate_dates:
            #     print(item)
            send_email = add_stick_and_puck_dates(skate_dates)

        if send_email:
            # print('New Dates Added')
            send_stick_and_puck_dates_email()
