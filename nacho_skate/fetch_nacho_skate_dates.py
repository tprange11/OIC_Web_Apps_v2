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
from nacho_skate.models import NachoSkateDate, NachoSkateSession, NachoSkateRegular
from accounts.models import Profile, UserCredit
from programs.models import Program

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
        if "Nacho" in item["text"]:
            skate_date = item["start_date"].split(" ")[0]
            skate_date = f"{skate_date[6:]}-{skate_date[:2]}-{skate_date[3:5]}"
            start_time = item["start_date"][-5:] # Last 5 characters HH:MM
            end_time = item["end_date"][-5:] # Last 5 characters HH:MM

            skate_dates.append([skate_date, start_time, end_time])
    return

def add_skate_dates(sessions):
    '''Adds Nacho Skate dates and times to the NachoSkateDate model.'''
    model = NachoSkateDate
    new_dates = False

    for session in sessions:
        try:
            data = model(skate_date=session[0], start_time=session[1], end_time=session[2])
            data.save()
            new_dates = True
        except IntegrityError:
            continue
    # print(new_dates)
    return new_dates

def add_regulars():
    '''Adds regulars to the session if they have enough credit balance to cover the price of the skate.'''
    regulars = NachoSkateRegular.objects.all().select_related('regular')
    skate_dates = NachoSkateDate.objects.filter(skate_date__gt=date.today())
    price = Program.objects.get(id=15).skater_price

    for skate_date in skate_dates:
        for regular in regulars:
            try:
                user_credit = UserCredit.objects.get(user=regular.regular)
                if user_credit.pk == 870 or user_credit.balance >= price:
                    data = NachoSkateSession(skater=regular.regular, skate_date=skate_date, paid=True)
                    data.save()  # Will raise IntegrityError if duplicate
                    
                    if user_credit.pk != 870:  # Skip credit deduction for special account
                        user_credit.balance -= price
                        if user_credit.balance == 0:
                            user_credit.paid = False
                        user_credit.save()
            except UserCredit.DoesNotExist:
                continue  # Skip if no credit record
            except IntegrityError:
                continue  # Skip duplicates

def send_skate_dates_email():
    '''Sends email to Users who opted in letting them know when Nacho Skate dates are added.'''
    recipients = Profile.objects.filter(nacho_skate_email=True).select_related('user')

    for recipient in recipients:
        if recipient.user.is_active:
            to_email = [recipient.user.email]
            from_email = 'no-reply@mg.oicwebapps.com'
            subject = 'New Nacho Skate Date Added'

            # Build the plain text message
            text_message = f'Hi {recipient.user.first_name},\n\n'
            text_message += f'New Nacho Skate dates are now available online. Sign up at the url below.\n\n'
            text_message += f'https://www.oicwebapps.com/web_apps/nacho_skate/\n\n'
            text_message += f'If you no longer wish to receive these emails, log in to your account,\n'
            text_message += f'click on your username and change the email settings in your profile.\n\n'
            text_message += f'Thank you for using OICWebApps.com!\n\n'

            # Build the html message
            html_message = render_to_string(
                'nacho_skate_dates_email.html',
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
    
    from_date = date.today() + timedelta(days=3)
    from_date = from_date.strftime("%m/%d/%Y")
    send_email = False

    # Every Sunday request schedule data and parse for Nacho Skate dates
    if date.today().weekday() == 6:
        get_schedule_data(from_date, from_date)

        if len(skate_dates) > 0:
            send_email = add_skate_dates(skate_dates)
        
        if send_email:
            add_regulars()
            send_skate_dates_email()
