## This file is run daily to scrape the OIC online schedule and save the days events for the zamboni
## resurface schedule.  It is also used from views.py scrape_schedule() view to update the schedule if anything
## has been added or removed.

from bs4 import BeautifulSoup
import mechanicalsoup
from datetime import date, datetime
import os, requests, sys

if os.name == 'nt':
    sys.path.append("C:\\Users\\brian\\Documents\\Python\\OIC_Web_Apps\\")
else:
    sys.path.append('/home/OIC/OIC_Web_Apps/')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'OIC_Web_Apps.settings')

import django
django.setup()

from django.db import IntegrityError
from schedule.models import RinkSchedule

months = {"01": "January", "02": "February", "03": "March", "04": "April", "05": "May", 
            "06": "June", "07": "July", "08": "August", "09": "September", "10": "October", "11": "November", "12": "December"}

oic_schedule = []  # list that will hold the day's events
schedule_notes = [] # list that will hold notes if any
team_events = [] # list that will hold OYHA, OCHL and OWHL teams to merge with oic_schedule[]

def scrape_oic_schedule(date):
    '''Scrapes Ozaukee Ice Center schedule website the days events.'''
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
    browser["ctl00_ContentPlaceHolder1_cboFacility_ClientState"] = '{"logEntries":[],"value":"","text":"7 items checked","enabled":true,"checkedIndices":[1,2,3,4,5,6,7],"checkedItemsTextOverflows":true}'
    browser["ctl00$ContentPlaceHolder1$cboFacility"] = '7 items checked'

    response = browser.submit_selected()
    # print(response.text)
    browser.close()

    soup = BeautifulSoup(response.text, 'html.parser')
    try:
        rows = soup.find(class_="clear listTable").find_all('tr')
    except AttributeError:
        return
    
    # print(rows)

    # Get the days events
    for row in rows:
        cols = row.find_all('td')
        if (cols[0].get_text().strip() == "Start Time"):
            continue
        else:
            if len(cols) > 2:
                oic_schedule.append([date, cols[0].get_text().strip(), cols[1].get_text().strip(), cols[3].get_text().strip(), cols[4].get_text().strip()])
                schedule_notes.append("")
            # elif len(cols) == 2:
                # schedule_notes[x-1] = cols[1].get_text().strip()
        # print(schedule_notes)
                
        # print(cols)

    # Replace some long strings in oic_schedule[]
    for item in oic_schedule:
        if "Ozaukee Youth Hockey Association" in item[4]:
            item[4] = "OYHA"
        elif "Ozaukee County Hockey League" in item[4]:
            if "Novice" in item[4]:
                item[4] = "OCHL Novice"
            elif "Intermediate" in item[4]:
                item[4] = "OCHL Intermediate"
            elif "Competitive" in item[4]:
                item[4] = "OCHL Competitive"
        elif "Wisconsin Elite Hockey League" in item[4]:
            item[4] = "WEHL"
        elif "Ozaukee Women's Hockey League" in item[4]:
            item[4] = "OWHL"


    # Add Notes to oic_schedule
    if len(schedule_notes) != 0:
        for x in range(len(oic_schedule)):
            if len(oic_schedule[x]) > 0:
                oic_schedule[x].append(schedule_notes[x].strip("Schedule Notes: "))
            else:
                oic_schedule[x].append(schedule_notes[x])


def add_schedule_to_model(schedule):
    '''Adds OIC daily schedule to RinkSchedule model.'''
    model = RinkSchedule

    # First, clear yesterday's schedule from the model
    RinkSchedule.objects.all().delete()

    for item in schedule:
        try:
            data = model(schedule_date=item[0], start_time=datetime.strptime(item[1], '%I:%M %p'), end_time=datetime.strptime(item[2], '%I:%M %p'), rink=item[3], event=item[4], notes=item[5])
            data.save()
        except IntegrityError:
            continue
    return


def scrape_owhl_teams(the_date):
    '''Scrapes OIC Rink League Schedule website for OWHL teams.'''

    today_split = the_date.split("-")
    today_string = f"{months[today_split[1]]} {today_split[2].lstrip('0')}, {today_split[0]}"

    url = "https://ozaukeeicecenter.maxgalaxy.net/LeagueScheduleList.aspx?ID=4"
    response = requests.get(url)

    # Request the web page
    soup = BeautifulSoup(response.text, "html.parser")
    # Get all div's with class = "activityGroupName"
    dates = soup.find_all(class_="activityGroupName")

    # Loop through and find today's date then find the next table with the days events
    for each in dates:
        if today_string in each.get_text():
            table = each.find_next("table")

    # Get all rows from the table
    rows = table.find_all("tr")

    # Collect pertinent data from the rows
    for row in rows:
        cols = row.find_all("td")
        # If it's the header row, skip the row
        if cols[0].get_text().strip() == "Start Time":
            continue
        else:
            team_events.append([cols[0].get_text().strip(), cols[6].get_text().strip(), cols[4].get_text().strip(), cols[3].get_text().strip()])

def scrape_ochl_teams():
    '''Scrapes OCHL Schedule website for teams.'''

    url = "https://www.ozaukeeicecenter.org/schedule/day/league_instance/102447?subseason=633604"
    response = requests.get(url)

    soup = BeautifulSoup(response.text, "html.parser")
    # Get game schedule table
    table = soup.find(class_="statTable")
    # Get table body which contains game or practice rows
    tbody = table.find_next("tbody")

    # Get the rows
    rows = tbody.find_all("tr")

    # Get the data from the pertinent table cells: home, visitor, rink, start time
    for row in rows:
        cols = row.find_all("td")
        team_events.append([cols[5].find("span").get_text().strip(" CST"), cols[2].find("a").get_text(), cols[0].find("a").get_text(), cols[4].find("div").get_text().strip()])


def scrape_oyha_teams(the_date):
    '''Scrapes OIC Rink League Schedule website for OYHA and Opponent teams.'''

    today_split = the_date.split("-")
    today_string = f"{months[today_split[1]]} {today_split[2].lstrip('0')}, {today_split[0]}"

    url = "https://ozaukeeicecenter.maxgalaxy.net/LeagueScheduleList.aspx?ID=13"
    response = requests.get(url)

    # Request the web page
    soup = BeautifulSoup(response.text, "html.parser")
    # Get all div's with class = "activityGroupName"
    dates = soup.find_all(class_="activityGroupName")

    # Loop through and find today's date then find the next table with the days events
    table = []
    for each in dates:
        if today_string in each.get_text():
            table = each.find_next("table")

    # Get all rows from the table
    if len(table) == 0:
        return
    else:
        rows = table.find_all("tr")

    # Collect pertinent data from the rows
    for row in rows:
        cols = row.find_all("td")
        # If it's the header row skip it
        if cols[0].get_text().strip() == "Start Time":
            continue
        else:
            team_events.append([cols[0].get_text().strip(), cols[6].get_text().strip(), cols[4].get_text().strip(), cols[3].get_text().strip()])


if __name__ == "__main__":
    
    the_date = date.today()
    # the_date = "2019-10-26"

    scrape_date = date.isoformat(the_date)
    scrape_oic_schedule(scrape_date)
    ### UNCOMMENT DURING HOCKEY SEASON ###
    # Scrape OYHA teams daily
    try:
        scrape_oyha_teams(scrape_date)
    except Exception as e:
        print(f"{e}, scrape_oyha_teams()")

    # If it is Friday, scrape OWHL teams
    # if date.weekday(date.today()) == 4:
    #     try:
    #         scrape_owhl_teams(scrape_date)
    #     except Exception as e:
    #         print(f"{e}, scrape_owhl_teams()")

    # If it is Sunday, scrape OCHL teams
    # if date.weekday(date.today()) == 6:
    #     try:
    #         scrape_ochl_teams()
    #     except Exception as e:
    #         print(f"{e}, scrape_ochl_teams()")

    if len(team_events) != 0:
        for item in team_events:
            for oic in oic_schedule:
                if item[0] == oic[1] and item[3] == oic[3]:
                    if item[2] == "":
                        oic[4] = f"{item[1]}"
                    else:
                        oic[4] = f"{item[1]} vs {item[2]}"

    # If anything ends at midnight, change to 11:59 PM
    # for item in oic_schedule:
    #     if item[2] == "12:00 AM":
    #         item[2] = "11:59 PM"

    # Insert data into Django model
    add_schedule_to_model(oic_schedule)
