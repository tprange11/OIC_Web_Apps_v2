from datetime import date, timedelta
import os, sys, json, requests

if os.name == 'nt':
    sys.path.append("C:\\Users\\brian\\Documents\\Python\\OIC_Web_Apps\\")
else:
    # sys.path.append("/home/BrianC68/oicdev/OIC_Web_Apps/") # Uncomment in development
    sys.path.append("/home/OIC/OIC_Web_Apps/") # Uncomment in production
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'OIC_Web_Apps.settings')

import django
django.setup()

from django.db import IntegrityError
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from figure_skating.models import FigureSkatingDate
from accounts.models import Profile

skate_dates = []

def get_schedule_data(from_date, to_date):
    '''Request schedule data from Schedule Werks for the specified period.'''
    
    url = f"https://ozaukeeicecenter.schedulewerks.com/public/ajax/swCalGet?tid=-1&from={from_date}&to={to_date}&Complex=-1"
    response = requests.get(url)
    data = json.loads(response.text)

    for item in data:
        if "Open Figure" in item["usg"]:
            skate_date = item["start_date"].split(" ")[0]
            skate_date = f"{skate_date[6:]}-{skate_date[:2]}-{skate_date[3:5]}"
            start_time = item["st"].replace("P", " PM").replace("A", " AM")
            end_time = item["et"].replace("P", " PM").replace("A", " AM")

            skate_dates.append([skate_date, start_time, end_time])
    return


def add_skate_dates(sessions):
    '''Adds Figure Skating skate dates and times SkateDates model.'''
    model = FigureSkatingDate
    new_dates = ''
    for session in sessions:
        try:
            data = model(skate_date=session[0], start_time=session[1], end_time=session[2], available_spots=15)
            data.save()
            new_dates = True
        except IntegrityError:
            new_dates = False
            continue

    return new_dates

def send_skate_dates_email():
    '''Sends email to Users letting them know when Figure skating dates are added.'''
    recipients = Profile.objects.filter(figure_skating_email=True).select_related('user')

    for recipient in recipients:
        if recipient.user.is_active:
            to_email = [recipient.user.email]
            from_email = 'no-reply@mg.oicwebapps.com'
            subject = 'New Figure Skating Dates Added'

            # Build the plain text message
            text_message = f'Hi {recipient.user.first_name},\n\n'
            text_message += f'New Figure Skating dates are now available online. Sign up at the url below.\n\n'
            text_message += f'https://www.oicwebapps.com/web_apps/figure_skating/\n\n'
            text_message += f'If you no longer wish to receive these emails, log in to your account,\n'
            text_message += f'click on your username and change the email settings in your profile.\n\n'
            text_message += f'Thank you for using OICWebApps.com!\n\n'

            # Build the html message
            html_message = render_to_string(
                'figure_skating_dates_email.html',
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

    # the_date = date.today()
    send_email = False

    get_schedule_data("08/07/2023", "08/31/2023")

    if len(skate_dates) != 0:
        # send_email = add_skate_dates(skate_dates)
        add_skate_dates(skate_dates)

    # if send_email:
    #     send_skate_dates_email()
