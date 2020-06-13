from bs4 import BeautifulSoup
import mechanicalsoup
from datetime import date, timedelta
import os, sys

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
from yeti_skate.models import YetiSkateDate
from accounts.models import Profile

skate_dates = []

def scrape_oic_schedule(date):
    '''Scrapes Ozaukee Ice Center schedule website for Yeti Skate dates.'''
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
            if cols[4].get_text().strip() == "Yeti":
                skate_dates.append([date, cols[0].get_text().strip(), cols[1].get_text().strip()])
                break

def add_skate_dates(sessions):
    '''Adds Yeti Skate dates and times AdultSkillsSkateDates model.'''
    model = YetiSkateDate

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
    '''Sends email to Users letting them know when Yeti Skate dates are added.'''
    recipients = Profile.objects.filter(yeti_skate_email=True).select_related('user')

    for recipient in recipients:
        to_email = [recipient.user.email]
        from_email = 'no-reply@mg.oicwebapps.com'
        subject = 'New Yeti Skate Date Added'

        # Build the plain text message
        text_message = f'Hi {recipient.user.first_name},\n\n'
        text_message += f'New Yeti Skate dates are now available online. Sign up at the url below.\n\n'
        text_message += f'https://www.oicwebapps.com/web_apps/yeti_skate/\n\n'
        text_message += f'If you no longer wish to receive these emails, log in to your account,\n'
        text_message += f'click on your username and change the email settings in your profile.\n\n'
        text_message += f'Thank you for using OICWebApps.com!\n\n'

        # Build the html message
        html_message = render_to_string(
            'yeti_skate_dates_email.html',
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
    send_email = False

    # Every day scrape the next four weeks for Saturday Yeti Skate dates
    for x in range(8):
        scrape_date = date.isoformat(the_date)
        if the_date.weekday() == 1 or the_date.weekday() == 4:
            scrape_oic_schedule(scrape_date)

        the_date += timedelta(days=1)

    if len(skate_dates) != 0:
        send_email = add_skate_dates(skate_dates)
               
    # print(skate_dates)
    # print(send_email)
    if send_email:
        send_skate_dates_email()
