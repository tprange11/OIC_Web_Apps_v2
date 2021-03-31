## This file is run daily to scrape the OIC online schedule and save the days events for the zamboni
## resurface schedule.  It is also used from views.py scrape_schedule() view to update the schedule if anything
## has been added or removed.

from bs4 import BeautifulSoup
import mechanicalsoup
from datetime import date, datetime, timedelta
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
north_locker_rooms = [[1, 3], [2, 4]]  # Locker room numbers in North
south_locker_rooms = [[6, 9], [5, 8], 7]  # Locker room numbers in South


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
    html = response.text.replace('</br>', '').replace('<br>', '')
    browser.close()

    soup = BeautifulSoup(html, 'html.parser')
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
                oic_schedule.append([date, cols[0].get_text().strip(), cols[1].get_text().strip(), cols[3].get_text().strip(), cols[4].get_text().strip(), cols[5].get_text().strip()])
                # schedule_notes.append("")
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

# def scrape_owhl_teams(the_date):
#     '''Scrapes OIC Rink League Schedule website for OWHL teams.'''

#     today_split = the_date.split("-")
#     today_string = f"{months[today_split[1]]} {today_split[2].lstrip('0')}, {today_split[0]}"

#     url = "https://ozaukeeicecenter.maxgalaxy.net/LeagueScheduleList.aspx?ID=17"
#     response = requests.get(url)

#     # Request the web page
#     soup = BeautifulSoup(response.text, "html.parser")
#     # Get all div's with class = "activityGroupName"
#     dates = soup.find_all(class_="activityGroupName")

#     # Loop through and find today's date then find the next table with the days events
#     table = None
#     for each in dates:
#         if today_string in each.get_text():
#             table = each.find_next("table")

#     # Get all rows from the table
#     rows = table.find_all("tr")

#     # Collect pertinent data from the rows
#     for row in rows:
#         cols = row.find_all("td")
#         # If it's the header row, skip the row
#         if cols[0].get_text().strip() == "Start Time":
#             continue
#         else:
#             team_events.append([cols[0].get_text().strip(), cols[6].get_text().strip(), cols[4].get_text().strip(), cols[3].get_text().strip()])

def scrape_ochl_teams():
    '''Scrapes OCHL Schedule website for teams.'''

    url = "https://www.ozaukeeicecenter.org/schedule/day/league_instance/128332?subseason=714101"
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
        team_events.append([cols[5].find("span").get_text().strip(" CST").strip(" CDT"), cols[2].find("a").get_text(), cols[0].find("a").get_text(), cols[4].find("div").get_text().strip()])


# def scrape_oyha_teams(the_date):
#     '''Scrapes OIC Rink League Schedule website for OYHA and Opponent teams.'''

#     today_split = the_date.split("-")
#     today_string = f"{months[today_split[1]]} {today_split[2].lstrip('0')}, {today_split[0]}"

#     url = "https://ozaukeeicecenter.maxgalaxy.net/LeagueScheduleList.aspx?ID=13"
#     response = requests.get(url)

#     # Request the web page
#     soup = BeautifulSoup(response.text, "html.parser")
#     # Get all div's with class = "activityGroupName"
#     dates = soup.find_all(class_="activityGroupName")

#     # Loop through and find today's date then find the next table with the days events
#     table = []
#     for each in dates:
#         if today_string in each.get_text():
#             table = each.find_next("table")

#     # Get all rows from the table
#     if len(table) == 0:
#         return
#     else:
#         rows = table.find_all("tr")

#     # Collect pertinent data from the rows
#     for row in rows:
#         cols = row.find_all("td")
#         # If it's the header row skip it
#         if cols[0].get_text().strip() == "Start Time":
#             continue
#         else:
#             team_events.append([cols[0].get_text().strip(), cols[6].get_text().strip(), cols[4].get_text().strip(), cols[3].get_text().strip()])

#     for event in team_events:
#         if event[1] == '':
#             event[1] = 'OYHA'

def add_locker_rooms_to_schedule():
    '''Add locker room assignments to oic_schedule list'''

    south_lr_flag = 0
    north_lr_flag = 0
    x = 0  # index of rink list for appending locker room numbers
    no_locker_room = ("Public Skate", "Learn to Skate", "Open Figure Skating", "Kettle Moraine Figure Skating Club")
    need_game_locker_rooms = ("Cedarburg Hockey", "Homestead Hockey", "Lakeshore Lightning",
                              "Concordia ACHA", "Concordia University Men", "Concordia University Women")
    short_name = {
        "Concordia University Men": "CUW Men",
        "Concordia University Women": "CUW Women",
        "Kettle Moraine Figure Skating Club": "KM Figure Skating Club",
    }

    # Replace long customer name with short name
    for item in oic_schedule:
        if item[4] in short_name:
            item[4] = short_name[item[4]]

    for (_, _, _, rink, customer, event_type) in oic_schedule:
        # if 'Practice' in event_type or customer in no_locker_room: # Used for Covid-19
        if customer in no_locker_room:
            oic_schedule[x].append("")
            oic_schedule[x].append("")
            x += 1
            continue
        elif 'North' in rink:
            # if 'Game' in event_type:
            #     oic_schedule[x].append("") # Home team doesn't need a locker room
            #     oic_schedule[x].append(north_locker_rooms[north_lr_flag][0])
            # else:
            oic_schedule[x].append(north_locker_rooms[north_lr_flag][1])
            oic_schedule[x].append(north_locker_rooms[north_lr_flag][0])
            if north_lr_flag == 0:
                north_lr_flag = 1
            else:
                north_lr_flag = 0
        elif 'South' in rink:
            if 'Game' in event_type and customer in need_game_locker_rooms:
                if 'Concordia ACHA' in customer:
                    oic_schedule[x].append('7') # Concordia ACHA Locker Room
                else:
                    oic_schedule[x].append("") # Home team doesn't need a locker room
                oic_schedule[x].append(south_locker_rooms[south_lr_flag][0])
            else:
                oic_schedule[x].append(south_locker_rooms[south_lr_flag][1])
                oic_schedule[x].append(south_locker_rooms[south_lr_flag][0])
            if south_lr_flag == 0:
                south_lr_flag = 1
            else:
                south_lr_flag = 0
        x += 1


def add_schedule_to_model(schedule, data_removed):
    '''Adds OIC daily schedule to RinkSchedule model.'''
    model = RinkSchedule

    # First, clear the database table once if data_removed = False
    if not data_removed:
        RinkSchedule.objects.all().delete()

    for item in schedule:
        try:
            data = model(
                schedule_date=item[0], 
                start_time=datetime.strptime(item[1], '%I:%M %p'), 
                end_time=datetime.strptime(item[2], '%I:%M %p'), 
                rink=item[3], 
                event=item[4],
                home_locker_room=item[6],
                visitor_locker_room=item[7],
                notes=""
                )
            data.save()
        except IntegrityError:
            continue
    return

if __name__ == "__main__":
    
    the_date = date.today()
    # the_date = "2019-10-26"
    scrape_date = date.isoformat(the_date)
    data_removed = False # used to check if the database table has been cleared once


    def swap_team_names():
        ''' Replace schedule event with team names if they match times'''
        if len(team_events) != 0:
            for item in team_events:
                for oic in oic_schedule:
                    if item[0] == oic[1] and item[3] == oic[3]:
                        if item[2] == "":
                            oic[4] = f"{item[1]}"
                        else:
                            oic[4] = f"{item[1]} vs {item[2]}"

    # If it's not Saturday or Sunday, scrape oic schedule
    if date.weekday(date.today()) not in [5, 6]:
        scrape_oic_schedule(scrape_date)
        # swap_team_names()
        add_locker_rooms_to_schedule()
        add_schedule_to_model(oic_schedule, data_removed)
        data_removed = True
        oic_schedule.clear()
        # team_events.clear()

        # If it is Friday, scrape Saturday and Sunday too
        if date.weekday(date.today()) == 4:
            saturday = date.isoformat(date.today() + timedelta(days=1))
            scrape_oic_schedule(saturday)
            # swap_team_names()
            add_locker_rooms_to_schedule()
            add_schedule_to_model(oic_schedule, data_removed)
            oic_schedule.clear()
            # team_events.clear()

            sunday = date.isoformat(date.today() + timedelta(days=2))
            # oic_schedule.clear()
            scrape_oic_schedule(sunday)
            # try:
            #     scrape_ochl_teams()
            # except Exception as e:
            #     print(f"{e}, scrape_ochl_teams()")
            # swap_team_names()
            add_locker_rooms_to_schedule()
            add_schedule_to_model(oic_schedule, data_removed)
            oic_schedule.clear()
            team_events.clear()
