from bs4 import BeautifulSoup
import mechanicalsoup
from datetime import date, timedelta
import os, sys

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
# from django.contrib.auth import get_user_model
# User = get_user_model()

stick_and_puck = []  # list that will hold stick and puck dates
stick_and_puck_notes = [] # list that will hold stick and puck session notes

def scrape_oic_schedule(date):
    '''Scrapes Ozaukee Ice Center schedule website for stick and puck session dates.'''
    xx_xx_xxxx = f"{date[5:7]}/{date[8:]}/{date[0:4]}"
    xxxx_xx_xx = f"{date[0:4]},{date[5:7]},{date[8:]}"
    today_with_time = date + "-00-00-00"

    # Used for testing purposes
    # print(xx_xx_xxxx)
    # print(xxxx_xx_xx)
    # print(today_with_time)

    browser = mechanicalsoup.StatefulBrowser()

    browser.open("https://ozaukeeicecenter.maxgalaxy.net/ScheduleList.aspx?ID=2")

    browser.get_current_page()
    # print(page)
    browser.select_form('form[action="./ScheduleList.aspx?ID=2"]')
    # browser.get_current_form().print_summary()

    browser["ctl00_ContentPlaceHolder1_txtFromDate_dateInput_ClientState"] = '{"enabled":true,"emptyMessage":"","validationText":"'+today_with_time+'","valueAsString":"'+today_with_time+'","minDateStr":"1980-01-01-00-00-00","maxDateStr":"2099-12-31-00-00-00","lastSetTextBoxValue":"'+xx_xx_xxxx+'"}'
    browser["ctl00_ContentPlaceHolder1_txtThroughDate_dateInput_ClientState"] = '{"enabled":true,"emptyMessage":"","validationText":"'+today_with_time+'","valueAsString":"'+today_with_time+'","minDateStr":"1980-01-01-00-00-00","maxDateStr":"2099-12-31-00-00-00","lastSetTextBoxValue":"'+xx_xx_xxxx+'"}'
    browser["ctl00_ContentPlaceHolder1_cboSortBy_ClientState"] = '{"logEntries":[],"value":"2","text":"Start Time","enabled":true,"checkedIndices":[],"checkedItemsTextOverflows":false}'
    browser["ctl00$ContentPlaceHolder1$txtFromDate"] = date
    browser["ctl00$ContentPlaceHolder1$txtFromDate$dateInput"] = xx_xx_xxxx
    browser["ctl00_ContentPlaceHolder1_txtFromDate_calendar_AD"] = '[[1980,1,1],[2099,12,30],['+xxxx_xx_xx+']]'
    browser["ctl00_ContentPlaceHolder1_txtFromDate_calendar_SD"] = '[['+xxxx_xx_xx+']]'
    browser["ctl00$ContentPlaceHolder1$txtThroughDate"] = date
    browser["ctl00$ContentPlaceHolder1$txtThroughDate$dateInput"] = xx_xx_xxxx
    browser["ctl00_ContentPlaceHolder1_txtThroughDate_calendar_AD"] = '[[1980,1,1],[2099,12,30],['+xxxx_xx_xx+']]'
    browser["ctl00_ContentPlaceHolder1_txtThroughDate_calendar_SD"] = '[['+xxxx_xx_xx+']]'
    browser["ctl00_ContentPlaceHolder1_cboFacility_ClientState"] = '{"logEntries":[],"value":"","text":"All items checked","enabled":true,"checkedIndices":[0,1,2,3,4,5,6,7],"checkedItemsTextOverflows":false}'
    browser["ctl00$ContentPlaceHolder1$cboFacility"] = 'All items checked'

    response = browser.submit_selected()
    # print(response.text)
    browser.close()

    soup = BeautifulSoup(response.text, 'html.parser')
    try:
        rows = soup.find(class_="clear listTable").find_all('tr')
    except AttributeError:
        return

    for row in rows:
        cols = row.find_all('td')

        if len(cols) > 2:
            if cols[4].get_text().strip() == "Stick and Puck":
                stick_and_puck.append([date, cols[0].get_text().strip(), cols[1].get_text().strip()])
        if len(cols) == 2:
            stick_and_puck_notes.append(cols[1].get_text().strip())

    # print(stick_and_puck)
    # print(stick_and_puck_notes)

    # Add Stick and Puck age range to Stick and Puck dates list if there is one
    if len(stick_and_puck_notes) != 0:
        for x in range(len(stick_and_puck)):
            if "14 and Under" in stick_and_puck[x] and "14 and Over" in stick_and_puck[x]:
                stick_and_puck[x].append(stick_and_puck_notes[x].strip("Schedule Notes: "))
            else:
                stick_and_puck[x].append("All Ages")
    else:
        for x in range(len(stick_and_puck)):
            stick_and_puck[x].append("All Ages")

    # print(stick_and_puck)

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
    # the_date = "2019-09-14"

    # Every day scrape seven days in the future for stick and puck session dates and times
    for x in range(7):
        scrape_date = date.isoformat(the_date)
        scrape_oic_schedule(scrape_date)
        
        if len(stick_and_puck) != 0:
            send_email = add_stick_and_puck_dates(stick_and_puck)
        else:
            send_email = False

        the_date += timedelta(days=1)
        stick_and_puck.clear()
        stick_and_puck_notes.clear()
    # print(send_email)
    if send_email:
        # print('New Dates Added')
        send_stick_and_puck_dates_email()
    else:
        # print('No SnP Dates Added')
        send_stick_and_puck_dates_email()
