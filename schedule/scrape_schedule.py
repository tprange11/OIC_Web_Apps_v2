# Legacy daily scraper for the Zamboni resurface schedule.
#
# Run as a script from cron: pulls today's (and on Fridays, the weekend's) events from
# ScheduleWerks, shortens customer names, merges OCHL/OWHL team names, assigns locker
# rooms and writes RinkSchedule rows. Its functions are also imported by
# schedule/views.py (the "Update Schedule" button) and by
# schedule/services/schedulewerks_adapter.py (the new ingest pipeline), so importing
# this module has side effects: it touches sys.path and calls django.setup().
#
# State is kept in the module-level lists below; callers must clear them between uses.

from bs4 import BeautifulSoup
from datetime import date, timedelta
from html import unescape
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

oic_schedule = []  # rows of [date, start, end, rink, event, usg, (home_lr, visitor_lr)]
schedule_notes = [] # never populated any more; process_data() still checks it
team_events = [] # [start, home, visitor, rink] rows scraped from the OCHL/OWHL league pages
north_locker_rooms = [[1, 3], [2, 4]]  # North rink pairs, alternated event by event
south_locker_rooms = [[6, 9], [5, 8], 7]  # South rink pairs; 7 is reserved for Concordia ACHA


def get_schedule_data(from_date, to_date):
    '''Request schedule data from Schedule Werks for the specified period.'''

    url = f"https://ozaukeeicecenter.schedulewerks.com/public/ajax/swCalGet?tid=-1&from={from_date}&to={to_date}&Complex=-1"

    try:
        response = requests.get(url)
        data = json.loads(response.text)
        return data
    except requests.exceptions.RequestException as e:
        return ""

def process_data(data, from_date):
    '''Appends the North/South rink events for one date (MM/DD/YYYY) to oic_schedule.

    The ScheduleWerks "text" field is HTML with the rink name in a fixed 30-character
    prefix; the customer name is whatever follows it. Long league names are shortened.
    '''
    for item in data:
        if item["start_date"].split(" ")[0] == from_date:
            schedule_date = item["start_date"].split(" ")[0]
            start_time = item["start_date"].split(" ")[1]
            end_time = item["end_date"].split(" ")[1]

            # Decode unicode escapes, strip HTML tags, remove printer emoji
            text_clean = BeautifulSoup(item["text"].encode().decode('unicode_escape'), "html.parser").get_text()
            text_clean = text_clean.replace("🖨️", "")

            if "South Rink" in text_clean:
                rink = "South Rink"
                event = text_clean[30:].strip().replace("(", "").replace(")", "")
                if " OYHA" in event:
                    event = event[:-5]
            elif "North Rink" in text_clean:
                rink = "North Rink"
                event = text_clean[30:].strip().replace("(", "").replace(")", "")
                if " OYHA" in event:
                    event = event[:-5]
            else:
                continue
            event_type = item["usg"]

            oic_schedule.append(
                [
                    schedule_date, start_time, end_time, rink, event, event_type
                ]
                )

    # Shorten league names (every call re-scans the whole list, which is harmless)
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


    # Notes support from the old schedule source; schedule_notes is never filled now
    if len(schedule_notes) != 0:
        for x in range(len(oic_schedule)):
            if len(oic_schedule[x]) > 0:
                oic_schedule[x].append(schedule_notes[x].strip("Schedule Notes: "))
            else:
                oic_schedule[x].append(schedule_notes[x])

    return

def scrape_teams(league):
    '''Scrapes the OCHL or OWHL league page into team_events as [start, home, visitor, rink].
    The league_instance/subseason ids in the URLs change every season.'''

    if league == 'OCHL':
        url = "https://www.ozaukeeicecenter.org/schedule/day/league_instance/222928?subseason=945079"
    elif league == 'OWHL':
        url = "https://www.ozaukeeicecenter.org/schedule/day/league_instance/226296?subseason=953087"
    else:
        return

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

    # Convert to 24-hour time to match oic_schedule; assumes every league game is PM
    for row in team_events:
        time = row[0].strip(" PM")
        time = time.split(":")
        time[0] = str(int(time[0]) + 12)
        time = ":".join(time)
        row[0] = time

def add_locker_rooms_to_schedule():
    '''Appends (home_lr, visitor_lr) to every row in oic_schedule.

    Rules, in order:
      - no_locker_room customers get none.
      - Each rink alternates between two locker room pairs from event to event.
      - need_game_locker_rooms teams have their own rooms: for a Game only the
        visitor gets a rotated room; otherwise nobody does. In the South, Concordia
        ACHA always gets room 7 and Lakeshore Lightning always gets room 9 (plus a
        visitor room for games).
    Must be called exactly once per batch: it appends rather than assigns.
    '''

    south_lr_flag = 0
    north_lr_flag = 0
    x = 0  # index of rink list for appending locker room numbers
    no_locker_room = ("Public Skate", "LTS", "Open FS", "Kettle Moraine Figure Skating Club")
    need_game_locker_rooms = (
        "Lakeshore Lightning",
        "Concordia ACHA",
        "Concordia Men",
        "Concordia Women"
        )

    short_name = {
        "Concordia Men CUW": "Concordia Men",
        "Concordia Women CUW": "Concordia Women",
        "Concordia ACHA CUW": "Concordia ACHA",
        "Team Wisconsin Girls 14U TWG":"Team Wisconsin Girls 14U",
        "Yeti Yeti": "Yeti Skate",
        "Lady Hawks Lady Hawks": "Lady Hawks",
        "Open Figure Open FS": "Open FS",
        "Kranich Kranich": "Kranich",
        "Cedarburg CHS": "Cedarburg",
        "Homestead HHS": "Homestead",
        "Lakeshore Lightning LSL": "Lakeshore Lightning",
        "Kettle Moraine Figure Skating Club": "KM Figure Skating Club",
        "Womens Open Hockey Women Open": "Womens Open Hockey",
        "Stick&Puck": "Stick & Puck",
        "Public": "Public Skate",
        "PC": "Playerz Choice",
        "Nacho": "Nacho Skate",
    }

    # Replace long customer name with short name
    for item in oic_schedule:
        if item[4] in short_name:
            item[4] = short_name[item[4]]

    for (_, _, _, rink, customer, event_type) in oic_schedule:
        if customer in no_locker_room:
            oic_schedule[x].append("")
            oic_schedule[x].append("")
            x += 1
            continue
        elif 'North' in rink:
            if 'Game' in event_type and customer in need_game_locker_rooms:
                oic_schedule[x].append("") # Home team doesn't need a locker room
                oic_schedule[x].append(north_locker_rooms[north_lr_flag][0])
            elif customer in need_game_locker_rooms:
                oic_schedule[x].append('')
                oic_schedule[x].append('')
            else:
                oic_schedule[x].append(north_locker_rooms[north_lr_flag][1])
                oic_schedule[x].append(north_locker_rooms[north_lr_flag][0])
            if north_lr_flag == 0:
                north_lr_flag = 1
            else:
                north_lr_flag = 0
        elif 'South' in rink:
            if 'Game' in event_type and customer in need_game_locker_rooms:
                if 'Concordia ACHA' in customer:
                    oic_schedule[x].append(south_locker_rooms[2]) # Concordia ACHA always gets 7 (per Dono)
                    oic_schedule[x].append("") # Visiting team doesn't need a locker room
                elif 'Lakeshore Lightning' in customer:
                    oic_schedule[x].append('9')
                    oic_schedule[x].append(south_locker_rooms[0][0])
                    if south_lr_flag == 1:
                        south_lr_flag = 0
                else:
                    oic_schedule[x].append("") # Home Team does not need a locker room assigned
                    oic_schedule[x].append(south_locker_rooms[south_lr_flag][0])
            else:
                if 'Concordia ACHA' in customer:
                    oic_schedule[x].append(south_locker_rooms[2]) # Concordia ACHA always gets 7
                    oic_schedule[x].append("")
                elif 'Lakeshore Lightning' in customer:
                    oic_schedule[x].append('9')
                    oic_schedule[x].append('')
                    if south_lr_flag == 1:
                        south_lr_flag = 0
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

    # Append the opponent for OYHA games: the usg field reads "Game vs <opponent>",
    # so slicing off the first four characters leaves " vs <opponent>".
    for item in oic_schedule:
        if "Game" in item[5] and "vs" not in item[4]:
            item[4] = item[4] + item[5][4:]



def add_schedule_to_model(schedule, data_removed):
    '''Inserts the schedule rows; duplicates (same date, times and rink) are skipped,
    so an existing row is never updated. Purges rows older than two weeks on the
    first call of a run (data_removed=False).'''
    model = RinkSchedule

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

    from_date = date.today().strftime("%m/%d/%Y")
    to_date = (date.today() + timedelta(days=2)).strftime("%m/%d/%Y")
    data_removed = False # add_schedule_to_model() purges old rows only on its first call


    def swap_team_names():
        '''Replaces the event name with "Home vs Visitor" where a scraped league game
        has the same start time and rink.'''
        if len(team_events) != 0:
            for item in team_events:
                for oic in oic_schedule:
                    if item[0] == oic[1] and oic[3] in item[3]:
                        if item[2] == "":
                            oic[4] = f"{item[1]}"
                        else:
                            oic[4] = f"{item[1]} vs {item[2]}"

    # Weekends are skipped; Friday's run also covers Saturday and Sunday
    if date.weekday(date.today()) not in [5, 6]:
        data = get_schedule_data(from_date, to_date)
        process_data(data, from_date)

        # OWHL plays Friday nights, OCHL plays on the weekend
        if date.weekday(date.today()) == 4:
            try:
                scrape_teams("OWHL")
            except Exception as e:
                print(f"{e}, scrape_owhl_teams()")

            swap_team_names()

        add_locker_rooms_to_schedule()
        add_schedule_to_model(oic_schedule, data_removed)
        data_removed = True
        oic_schedule.clear()
        team_events.clear()

        if date.weekday(date.today()) == 4:
            saturday = (date.today() + timedelta(days=1)).strftime("%m/%d/%Y")
            process_data(data, saturday)
            sunday = (date.today() + timedelta(days=2)).strftime("%m/%d/%Y")
            process_data(data, sunday)

            try:
                scrape_teams("OCHL")
            except Exception as e:
                print(f"{e}, scrape_ochl_teams()")

            swap_team_names()
            add_locker_rooms_to_schedule()
            add_schedule_to_model(oic_schedule, data_removed)
            oic_schedule.clear()
            team_events.clear()
