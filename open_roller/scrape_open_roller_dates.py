from datetime import date, timedelta
import os, sys, requests, json

if os.name == 'nt':
    sys.path.append("C:\\Users\\brian\\Documents\\Python\\OIC_Web_Apps\\")
else:
    sys.path.append("/home/OIC/OIC_Web_Apps/") # Uncomment on production server
    # sys.path.append("/home/BrianC68/oicdev/OIC_Web_Apps/") # Uncomment on development server
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'OIC_Web_Apps.settings')

import django
django.setup()

from django.db import IntegrityError
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from open_roller.models import OpenRollerSkateDate
from accounts.models import Profile

skate_dates = []

def get_schedule_data(from_date, to_date):
    '''Fetch Ozaukee Ice Center schedule data and parse for open roller hockey session dates.'''

    url = f"https://ozaukeeicecenter.schedulewerks.com/public/ajax/swCalGet?tid=-1&from={from_date}&to={to_date}&Complex=-1"

    try:
        response = requests.get(url)
        data = json.loads(response.text)
    except requests.exceptions.RequestException as e:
        # print(e)
        return

    for item in data:
        if "Open Roll" in item["text"]:
            skate_date = item["start_date"].split(" ")[0]
            skate_date = f"{skate_date[6:]}-{skate_date[:2]}-{skate_date[3:5]}"
            start_time = item["st"].replace("P", " PM").replace("A", " AM")
            end_time = item["et"].replace("P", " PM").replace("A", " AM")

            skate_dates.append([skate_date, start_time, end_time])

    return

def add_skate_dates(sessions):
    '''Adds Open Roller Hockey skate dates and times to OpenRollerSkateDate model.'''
    model = OpenRollerSkateDate

    for session in sessions:
        try:
            data = model(skate_date=session[0], start_time=session[1], end_time=session[2])
            data.save()
            new_dates = True
        except IntegrityError:
            new_dates = False
            continue
    # print(new_dates)
    return new_dates

def send_skate_dates_email():
    '''Sends email to Users letting them know when Open Roller Hockey skate dates are added.'''
    recipients = Profile.objects.filter(open_roller_email=True).select_related('user')

    for recipient in recipients:
        if recipient.user.is_active:
            to_email = [recipient.user.email]
            from_email = 'no-reply@mg.oicwebapps.com'
            subject = 'New Open Roller Hockey Date Added'

            # Build the plain text message
            text_message = f'Hi {recipient.user.first_name},\n\n'
            text_message += f'New Open Roller Hockey skate dates are now available online. Sign up at the url below.\n\n'
            text_message += f'https://www.oicwebapps.com/web_apps/open_roller/\n\n'
            text_message += f'If you no longer wish to receive these emails, log in to your account,\n'
            text_message += f'click on your username and change the email settings in your profile.\n\n'
            text_message += f'Thank you for using OICWebApps.com!\n\n'

            # Build the html message
            html_message = render_to_string(
                'open_roller_skate_dates_email.html',
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
    from_date = the_date  + timedelta(days=5)
    from_date = from_date.strftime("%m/%d/%Y")
    send_email = False

    # Fetch next week for Open Roller Hockey every Wednesday
    
    if the_date.weekday() == 2: # If it's Wednesday
        get_schedule_data(from_date, from_date)

    if len(skate_dates) != 0:
        send_email = add_skate_dates(skate_dates)

    if send_email:
        send_skate_dates_email()
