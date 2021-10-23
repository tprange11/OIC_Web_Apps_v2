## This file is run daily to request the OIC online schedule and save the days events for the zamboni
## resurface schedule.  It is also used from views.py scrape_schedule() view to update the schedule if anything
## has been added or removed.

from bs4 import BeautifulSoup
from datetime import date, timedelta
import os, requests, sys
import json

if os.name == 'nt':
    sys.path.append("C:\\Users\\brian\\Documents\\Python\\OIC_Web_Apps\\")
else:
    sys.path.append('/home/OIC/OIC_Web_Apps/')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'OIC_Web_Apps.settings')

import django
django.setup()

from django.db import IntegrityError
from schedule.models import RinkSchedule

oic_schedule = []  # list that will hold the day's events
schedule_notes = [] # list that will hold notes if any
team_events = [] # list that will hold OYHA, OCHL and OWHL teams to merge with oic_schedule[]
north_locker_rooms = [[1, 3], [2, 4]]  # Locker room numbers in North
south_locker_rooms = [[6, 9], [5, 8], 7]  # Locker room numbers in South


def get_schedule_data(from_date, to_date):
    '''Request schedule data from Schedule Werks for the specified period.'''
    
    url = f"https://ozaukeeicecenter.schedulewerks.com/public/ajax/swCalGet?tid=-1&from={from_date}&to={to_date}&Complex=-1"
    
    try:
        response = requests.get(url)
        data = json.loads(response.text)
        process_data(data, from_date)
        return data
    except requests.exceptions.RequestException as e:
        print(e)
        return ""

def process_data(data, from_date):
    for item in data:
        if item["start_date"].split(" ")[0] == from_date:
            schedule_date = item["start_date"].split(" ")[0]
            start_time = item["start_date"].split(" ")[1]
            end_time = item["end_date"].split(" ")[1]
            if "South Rink" in item["text"]:
                rink = "South Rink"
                event = item["text"][30:].strip().replace("(", "").replace(")", "")
            else:
                rink = "North Rink"
                event = item["text"][30:].strip().replace("(", "").replace(")", "")
            event_type = item["usg"]

            oic_schedule.append(
                [
                    schedule_date, start_time, end_time, rink, event, event_type
                ]
                )

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

    return


def scrape_ochl_teams():
    '''Scrapes OCHL Schedule website for teams.'''

    url = "https://www.ozaukeeicecenter.org/schedule/day/league_instance/150944?subseason=773253"
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
    
    # Convert start time to 24 hour time to match oic_schedule time format
    for row in team_events:
        time = row[0].strip(" PM")
        time = time.split(":")
        time[0] = str(int(time[0]) + 12)
        time = ":".join(time)
        row[0] = time


def scrape_owhl_teams():
    '''Scrapes OCHL Schedule website for teams.'''

    url = "https://www.ozaukeeicecenter.org/schedule/day/league_instance/153383?subseason=781038"
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
    
    # Convert start time to 24 hour time to match oic_schedule time format
    for row in team_events:
        time = row[0].strip(" PM")
        time = time.split(":")
        time[0] = str(int(time[0]) + 12)
        time = ":".join(time)
        row[0] = time
    

def add_locker_rooms_to_schedule():
    '''Add locker room assignments to oic_schedule list'''

    south_lr_flag = 0
    north_lr_flag = 0
    x = 0  # index of rink list for appending locker room numbers
    no_locker_room = ("Public Skate", "LTS", "Open FS", "Kettle Moraine Figure Skating Club", "GRIT Hockey Club")
    need_game_locker_rooms = ("Cedarburg Hockey", "Homestead Hockey", "Lakeshore Lightning",
                              "Concordia ACHA", "Concordia University Men", "Concordia University Women")
    short_name = {
        "Concordia Men CUW": "Concordia Men",
        "Concordia Women CUW": "Concordia Women",
        "Concordia ACHA CUW": "Concordia ACHA",
        "Team Wisconsin Girls 14U TWG":"Team Wisconsin Girls 14U",
        "Yeti Yeti": "Yeti",
        "Lady Hawks Lady Hawks": "Lady Hawks",
        "Open Figure Open FS": "Open FS",
        "Kettle Moraine Figure Skating Club": "KM Figure Skating Club",
    }

    for (_, _, _, rink, customer, event_type) in oic_schedule:
        # if 'Practice' in event_type or customer in no_locker_room: # Used for Covid-19
        if customer in no_locker_room:
            oic_schedule[x].append("")
            oic_schedule[x].append("")
            x += 1
            continue
        elif 'MKE Power' in customer:
            oic_schedule[x].append(south_locker_rooms[1][1])
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
                    oic_schedule[x].append(south_locker_rooms[2]) # Concordia ACHA Locker Room ##### Dono said only locker room 7
                    oic_schedule[x].append("") # Visiting team doesn't need a locker room
                else:
                    # oic_schedule[x].append(south_locker_rooms[south_lr_flag][1])
                    oic_schedule[x].append("") # Home Team does not need a locker room assigned
                    oic_schedule[x].append(south_locker_rooms[south_lr_flag][0])
            else:
                if 'Concordia ACHA' in customer:
                    oic_schedule[x].append(south_locker_rooms[2]) # Concordia ACHA Locker Room
                    oic_schedule[x].append("")
                    # oic_schedule[x].append(south_locker_rooms[south_lr_flag][0])
                # elif 'Yeti' in customer:
                #     oic_schedule[x].append('Jaden 8')
                #     oic_schedule[x].append('5 & 6')
                elif customer in need_game_locker_rooms:
                    oic_schedule[x].append('')
                    oic_schedule[x].append('')
                else:
                    oic_schedule[x].append(south_locker_rooms[south_lr_flag][1])
                    oic_schedule[x].append(south_locker_rooms[south_lr_flag][0])
            if south_lr_flag == 0:
                south_lr_flag = 1
            else:
                south_lr_flag = 0
        x += 1

    # Replace long customer name with short name
    for item in oic_schedule:
        if item[4] in short_name:
            item[4] = short_name[item[4]]
        elif " OYHA" in item[4]:
            item[4] = item[4].strip(" OYHA ")

def add_schedule_to_model(schedule, data_removed):
    '''Adds OIC daily schedule to RinkSchedule model.'''
    model = RinkSchedule

    # First, clear objects older than 14 days if data_removed = False
    if not data_removed:
        RinkSchedule.objects.filter(schedule_date__lte=date.today() + timedelta(days=-15)).delete()

    for item in schedule:
        try:
            data = model(
                schedule_date=f"{item[0][6:]}-{item[0][0:2]}-{item[0][3:5]}", # Date formatted to YYYY-MM-DD
                start_time=item[1], 
                end_time=item[2], 
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
    
    # todays_date = date.today()
    from_date = date.today().strftime("%m/%d/%Y")
    to_date = (date.today() + timedelta(days=2)).strftime("%m/%d/%Y")
    # print(todays_date.strftime("%m-%d-%Y"))
    # formatted_date = date.isoformat(todays_date)
    # start_date = f"{formatted_date[5:7]}/{formatted_date[8:]}/{formatted_date[0:4]}"
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
        data = get_schedule_data(from_date, to_date)

        if date.weekday(date.today()) == 4:
            try:
                scrape_owhl_teams()
            except Exception as e:
                print(f"{e}, scrape_owhl_teams()")

            swap_team_names()

        add_locker_rooms_to_schedule()
        add_schedule_to_model(oic_schedule, data_removed)
        data_removed = True
        oic_schedule.clear()
        team_events.clear()

        # If it is Friday, process Saturday and Sunday too
        if date.weekday(date.today()) == 4:
            saturday = (date.today() + timedelta(days=1)).strftime("%m/%d/%Y")
            # print(saturday)
            process_data(data, saturday)
            sunday = (date.today() + timedelta(days=2)).strftime("%m/%d/%Y")
            # print(sunday)
            process_data(data, sunday)

            try:
                scrape_ochl_teams()
            except Exception as e:
                print(f"{e}, scrape_ochl_teams()")

            swap_team_names()
            add_locker_rooms_to_schedule()
            add_schedule_to_model(oic_schedule, data_removed)
            oic_schedule.clear()
            team_events.clear()
