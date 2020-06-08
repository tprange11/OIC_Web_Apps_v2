import os, sys
from datetime import date

if os.name == 'nt':
    sys.path.append("C:\\Users\\brian\\Documents\\Python\\OIC_Web_Apps\\")
else:
    sys.path.append("/home/OIC/OIC_Web_Apps/")
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'OIC_Web_Apps.settings')

import django
django.setup()

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from accounts.models import Profile


def send_mail():
    '''Sends email to Users letting them know open hockey dates for the week are posted'''
    recipients = Profile.objects.filter(open_hockey_email=True).select_related('user')

    for recipient in recipients:
        to_email = [recipient.user.email]
        from_email = 'no-reply@mg.oicwebapps.com'
        subject = 'Yeti Skate Dates Now Available'

        # Build the plain text message
        text_message = f'Hi {recipient.user.first_name},\n\n'
        text_message += f'Yeti Skate dates are now available online. Sign up at the url below.\n\n'
        text_message += f'https://www.oicwebapps.com/web_apps/open_hockey/\n\n'
        text_message += f'If you no longer wish to receive these emails, log in to your account,\n'
        text_message += f'click on your username and change the email settings in your profile.\n\n'
        text_message += f'Thank you for using OICWebApps.com!\n\n'

        # Build the html message
        html_message = render_to_string(
            'open_hockey_dates_email.html',
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


if __name__ == '__main__':
    # Only send open hockey dates email on Monday(0)
    if date.today().weekday() == 0:
        send_mail()
