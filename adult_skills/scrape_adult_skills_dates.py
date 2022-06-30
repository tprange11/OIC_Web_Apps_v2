from datetime import date, timedelta
import os, sys, requests, json

if os.name == 'nt':
    sys.path.append("C:\\Users\\brian\\Documents\\Python\\OIC_Web_Apps\\")
else:
    sys.path.append("/home/OIC/OIC_Web_Apps/")
    # sys.path.append("/home/BrianC68/oicdev/OIC_Web_Apps/") # Uncomment on development server
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'OIC_Web_Apps.settings')

import django
django.setup()

from django.db import IntegrityError
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from adult_skills.models import AdultSkillsSkateDate
from accounts.models import Profile

skate_dates = []


def get_schedule_data(from_date, to_date):
    '''Request schedule data from Schedule Werks for the specified period.'''
    
    url = f"https://ozaukeeicecenter.schedulewerks.com/public/ajax/swCalGet?tid=-1&from={from_date}&to={to_date}&Complex=-1"

    try:
        response = requests.get(url)
        data = json.loads(response.text)
    except requests.exceptions.RequestException as e:
        # print(e)
        return

    for item in data:
        if "Adlt Skill" in item["text"]:
            skate_date = item["start_date"].split(" ")[0]
            skate_date = f"{skate_date[6:]}-{skate_date[:2]}-{skate_date[3:5]}"
            start_time = item["st"].replace("P", " PM").replace("A", " AM")
            end_time = item["et"].replace("P", " PM").replace("A", " AM")

            skate_dates.append([skate_date, start_time, end_time])
    return

def add_skate_dates(sessions):
    '''Adds Adult Skills skate dates and times AdultSkillsSkateDates model.'''
    model = AdultSkillsSkateDate

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
    '''Sends email to Users letting them know when Adult Skills skate dates are added.'''
    recipients = Profile.objects.filter(adult_skills_email=True).select_related('user')

    for recipient in recipients:
        if recipient.user.is_active:
            to_email = [recipient.user.email]
            from_email = 'no-reply@mg.oicwebapps.com'
            subject = 'New Adult Skills Skate Date Added'

            # Build the plain text message
            text_message = f'Hi {recipient.user.first_name},\n\n'
            text_message += f'New Adult Skills skate dates are now available online. Sign up at the url below.\n\n'
            text_message += f'https://www.oicwebapps.com/web_apps/adult_skills/\n\n'
            text_message += f'If you no longer wish to receive these emails, log in to your account,\n'
            text_message += f'click on your username and change the email settings in your profile.\n\n'
            text_message += f'Thank you for using OICWebApps.com!\n\n'

            # Build the html message
            html_message = render_to_string(
                'adult_skills_skate_dates_email.html',
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
    
    from_date = date.today().strftime("%m/%d/%Y")
    # from_date = "2019-09-14"
    to_date = (date.today() + timedelta(days=7)).strftime("%m/%d/%Y")
    send_email = False
    # print(f'From: {from_date} to {to_date}')

    # Every Thursday request two weeks of schedule data and parse for Adult Skills dates
    if date.today().weekday() == 3:
        get_schedule_data(from_date, to_date)

    if len(skate_dates) != 0:
        send_email = add_skate_dates(skate_dates)
               
    if send_email:
        send_skate_dates_email()
