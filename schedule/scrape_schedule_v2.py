#!/usr/bin/env python3
"""
OIC DAILY SCHEDULE SCRAPER — FULL CLEAN REWRITE (2025)

Pulls events from ScheduleWerks
Normalizes names
Merges weekend OCHL + OWHL games
Assigns locker rooms
Writes schedule to RinkSchedule

Author: Todd + ChatGPT (Rewritten for reliability)
"""

# -------------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------------
import os
import sys
import json
import logging
from datetime import datetime, date, timedelta
from time import sleep

import requests
from bs4 import BeautifulSoup

# Django initialization
if os.name == "nt":
    sys.path.append("C:\\Users\\brian\\Documents\\Python\\OIC_Web_Apps\\")
else:
    sys.path.append("/home/OIC/OIC_Web_Apps/")

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "OIC_Web_Apps.settings")

import django
django.setup()

from django.db import IntegrityError
from schedule.models import RinkSchedule


# -------------------------------------------------------------------
# LOGGING SETUP
# -------------------------------------------------------------------
LOG_PATH = "/home/OIC/logs/oic_schedule.log"

logger = logging.getLogger("oic_schedule")
logger.setLevel(logging.INFO)

handler = logging.FileHandler(LOG_PATH)
handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
logger.addHandler(handler)


# -------------------------------------------------------------------
# CONSTANTS
# -------------------------------------------------------------------
SCHEDULE_URL = (
    "https://ozaukeeicecenter.schedulewerks.com/public/ajax/swCalGet"
    "?tid=-1&from={start}&to={end}&Complex=-1"
)

TEAM_URLS = {
    "OCHL": "https://www.ozaukeeicecenter.org/schedule/day/league_instance/222928?subseason=945079",
    "OWHL": "https://www.ozaukeeicecenter.org/schedule/day/league_instance/226296?subseason=953087",
}

NO_LR = {
    "Public Skate",
    "LTS",
    "Open FS",
    "KM Figure Skating Club",
    "Stick & Puck",
}

SHORT_NAME = {
    "Concordia Men CUW": "Concordia Men",
    "Concordia Women CUW": "Concordia Women",
    "Concordia ACHA CUW": "Concordia ACHA",
    "Team Wisconsin Girls 14U TWG": "Team Wisconsin Girls 14U",
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

# Locker room rotation
NORTH_LR = [[1, 3], [2, 4]]
SOUTH_LR = [[6, 9], [5, 8]]
ACHA_LR = "7"
LKL_LR = "9"


# -------------------------------------------------------------------
# UTILITIES
# -------------------------------------------------------------------
def http_get(url, attempts=3):
    for i in range(attempts):
        try:
            r = requests.get(url, timeout=10)
            r.raise_for_status()
            return r.text
        except Exception as e:
            logger.error(f"[HTTP ERROR] {e} attempt {i+1}/{attempts}")
            sleep(2)
    logger.error(f"[HTTP FAILURE] URL failed: {url}")
    return None


def parse_time(raw):
    if not raw:
        return None

    t = raw.strip().upper().replace("\u200B", "").replace("\xA0", "")
    t = " ".join(t.split())

    for tz in (" CST", " CDT", " CT"):
        if t.endswith(tz):
            t = t[:-len(tz)]

    formats = ["%I:%M %p", "%I:%M%p", "%H:%M"]
    for f in formats:
        try:
            return datetime.strptime(t, f).time()
        except ValueError:
            pass

    logger.error(f"[TIME PARSE ERROR] Cannot parse: {raw}")
    return None


def clean_text(raw):
    decoded = raw.encode().decode("unicode_escape")
    cleaned = BeautifulSoup(decoded, "html.parser").get_text()
    cleaned = cleaned.replace("🖨️", "").replace("\u200b", "").replace("\xa0", " ").strip()
    return cleaned


# -------------------------------------------------------------------
# SCHEDULEWERKS PARSING
# -------------------------------------------------------------------
def fetch_schedule(start, end):
    url = SCHEDULE_URL.format(start=start, end=end)
    raw = http_get(url)
    return json.loads(raw) if raw else []


def extract_schedule(raw, target_date):
    events = []

    for item in raw:
        d = item["start_date"].split(" ")[0]
        if d != target_date:
            continue

        start = parse_time(" ".join(item["start_date"].split(" ")[1:]))
        end = parse_time(" ".join(item["end_date"].split(" ")[1:]))

        text = clean_text(item["text"])
        rink = "North Rink" if "North Rink" in text else "South Rink" if "South Rink" in text else None
        if not rink:
            continue

        event = text.split("Rink", 1)[-1].replace("(", "").replace(")", "").replace("OYHA", "").strip()
        usg = item["usg"]

        events.append([target_date, start, end, rink, event, usg])

    return events


# -------------------------------------------------------------------
# TEAM SCRAPING (OCHL + OWHL)
# -------------------------------------------------------------------
def convert_to_24(raw):
    try:
        r = raw.strip().upper().replace(" AM", "").replace(" PM", "")
        h, m = map(int, r.split(":"))
        if "PM" in raw.upper() and h < 12:
            h += 12
        return f"{h:02d}:{m:02d}"
    except:
        return None


def fetch_team_games(league):
    url = TEAM_URLS[league]
    html = http_get(url)
    if not html:
        return []

    soup = BeautifulSoup(html, "html.parser")
    tbody = soup.find(class_="statTable").find_next("tbody")

    results = []
    for row in tbody.find_all("tr"):
        cols = row.find_all("td")
        start = convert_to_24(cols[5].find("span").get_text())
        visitor = cols[2].find("a").get_text()
        home = cols[0].find("a").get_text()
        rink = cols[4].find("div").get_text().strip()
        results.append([start, home, visitor, rink])

    return results


def merge_team_events(oic, league_data):
    for t in league_data:
        for event in oic:
            start_time = event[1]
            if not start_time:
                continue

            h, m = start_time.hour, start_time.minute
            t_h, t_m = map(int, t[0].split(":"))

            same_time = (h == t_h and m == t_m)
            same_rink = t[3] in event[3]

            if same_time and same_rink:
                event[4] = f"{t[1]} vs {t[2]}" if t[2] else t[1]


# -------------------------------------------------------------------
# LOCKER ROOM ASSIGNMENT (FULLY REWRITTEN)
# -------------------------------------------------------------------
def assign_locker_rooms(oic):
    logger.info("---- ASSIGN LOCKER ROOMS ----")

    north_flag = 0
    south_flag = 0

    for i, event in enumerate(oic):
        sched_date, start, end, rink, customer, usg = event

        # Normalize name first
        if customer in SHORT_NAME:
            customer = SHORT_NAME[customer]
            oic[i][4] = customer

        # No locker room events
        if customer in NO_LR:
            oic[i].extend(["", ""])
            continue

        # Hard-coded LR rules
        if "Concordia ACHA" in customer:
            oic[i].extend([ACHA_LR, ""])
            continue

        if "Lakeshore Lightning" in customer:
            oic[i].extend([LKL_LR, ""])
            continue

        # Game detection
        is_game = ("vs" in customer) or ("vs" in usg.lower())

        # NORTH RINK RULES
        if "North" in rink:
            if is_game:
                oic[i].extend(["", str(NORTH_LR[north_flag][0])])
            else:
                home = NORTH_LR[north_flag][1]
                away = NORTH_LR[north_flag][0]
                oic[i].extend([str(home), str(away)])

            north_flag ^= 1
            continue

        # SOUTH RINK RULES
        if "South" in rink:
            if is_game:
                oic[i].extend(["", str(SOUTH_LR[south_flag][0])])
            else:
                home = SOUTH_LR[south_flag][1]
                away = SOUTH_LR[south_flag][0]
                oic[i].extend([str(home), str(away)])

            south_flag ^= 1
            continue

        # fallback
        oic[i].extend(["", ""])


# -------------------------------------------------------------------
# DATABASE WRITE
# -------------------------------------------------------------------
def write_to_db(oic):
    RinkSchedule.objects.filter(
        schedule_date__lte=date.today() - timedelta(days=15)
    ).delete()

    for event in oic:
        try:
            obj = RinkSchedule(
                schedule_date=datetime.strptime(event[0], "%m/%d/%Y").date(),
                start_time=event[1],
                end_time=event[2],
                rink=event[3],
                event=event[4],
                home_locker_room=event[6],
                visitor_locker_room=event[7],
                notes="",
            )
#            obj.save()
            logger.info(f"[DB] WROTE: {obj}")

        except Exception as e:
            logger.error(f"[DB ERROR] {e} :: {event}")


# -------------------------------------------------------------------
# MAIN
# -------------------------------------------------------------------
def run():
    logger.info("===== SCRAPER START =====")

    today = date.today()

    from_date = today.strftime("%m/%d/%Y")
    next1 = (today + timedelta(days=1)).strftime("%m/%d/%Y")
    next2 = (today + timedelta(days=2)).strftime("%m/%d/%Y")

    raw = fetch_schedule(from_date, next2)
    if not raw:
        logger.error("No raw schedule returned.")
        return

    combined = []
    for target in (from_date, next1, next2):
        combined.extend(extract_schedule(raw, target))

    # Weekend league games
    if today.weekday() == 4:
        merge_team_events(combined, fetch_team_games("OWHL"))
        merge_team_events(combined, fetch_team_games("OCHL"))

    assign_locker_rooms(combined)
    write_to_db(combined)

    logger.info("===== SCRAPER FINISHED =====")


if __name__ == "__main__":
    run()
