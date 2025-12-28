from datetime import date, datetime
import os
import sys
import requests
import logging

# ---------------------------------------------------
# Django Setup
# ---------------------------------------------------
if os.name == "nt":
    sys.path.append(r"C:\Users\brian\Documents\Python\OIC_Web_Apps")
else:
    sys.path.append("/home/OIC/OIC_Web_Apps/")

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "OIC_Web_Apps.settings")

import django
django.setup()

from django.db import IntegrityError
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.contrib.auth import get_user_model

from yeti_skate.models import YetiSkateDate, YetiSkateSession
from accounts.models import Profile

User = get_user_model()

# ---------------------------------------------------
# Logging
# ---------------------------------------------------
LOG_PATH = "/home/OIC/logs/yeti_skate.log"
logger = logging.getLogger("nacho_skate")
logger.setLevel(logging.INFO)

handler = logging.FileHandler(LOG_PATH)
handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
logger.addHandler(handler)

# ---------------------------------------------------
# Helpers
# ---------------------------------------------------
def convert_time(t):
    """
    Convert ScheduleWerks time strings like '6:00 AM' / '9:15 PM'
    into MySQL TIME format '06:00:00'.
    """
    try:
        return datetime.strptime(t, "%I:%M %p").strftime("%H:%M:%S")
    except Exception as e:
        logger.error(f"Time parsing failed for '{t}': {e}")
        return None


def convert_date(mdy):
    """
    Convert 'MM/DD/YYYY' → 'YYYY-MM-DD'.
    """
    try:
        return datetime.strptime(mdy, "%m/%d/%Y").strftime("%Y-%m-%d")
    except Exception as e:
        logger.error(f"Date parsing failed for '{mdy}': {e}")
        return None


# ---------------------------------------------------
# Fetch schedule data
# ---------------------------------------------------
def get_schedule_data(from_date, to_date):
    """
    Pull schedule data from ScheduleWerks and extract Yeti Skate entries.
    Returns: List of [YYYY-MM-DD, HH:MM:SS, HH:MM:SS]
    """
    url = (
        "https://ozaukeeicecenter.schedulewerks.com/public/ajax/swCalGet"
        f"?tid=-1&from={from_date}&to={to_date}&Complex=-1"
    )

    logger.info("Fetching ScheduleWerks data...")
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        logger.error(f"Failed to fetch schedule data: {e}")
        return []

    sessions = []

    for item in data:
        if "Yeti" not in item.get("text", ""):
            continue

        # Extract date
        raw_mdy = item["start_date"].split(" ")[0]   # "09/03/2024"
        parsed_date = convert_date(raw_mdy)
        if not parsed_date:
            continue

        # Extract time
        raw_start = item["st"].replace("P", " PM").replace("A", " AM")
        raw_end   = item["et"].replace("P", " PM").replace("A", " AM")

        start_time = convert_time(raw_start)
        end_time   = convert_time(raw_end)

        if not start_time or not end_time:
            continue

        sessions.append([parsed_date, start_time, end_time])

    logger.info(f"Found {len(sessions)} Yeti sessions.")
    return sessions


# ---------------------------------------------------
# Insert schedule into database
# ---------------------------------------------------
def add_skate_dates(sessions):
    """
    Inserts YetiSkateDate rows.
    Returns True if any NEW dates were added.
    """
    new_added = False

    for session in sessions:
        skate_date, start_time, end_time = session

        try:
            obj = YetiSkateDate(
                skate_date=skate_date,
                start_time=start_time,
                end_time=end_time,
            )
            obj.save()
            new_added = True
            logger.info(f"Inserted: {session}")
        except IntegrityError:
            # Already exists — skip
            continue
        except Exception as e:
            logger.error(f"DB insert error for {session}: {e}")

    return new_added


# ---------------------------------------------------
# Auto-add Nick to all future sessions
# ---------------------------------------------------
def add_nick_to_skate():
    try:
        user = User.objects.get(pk=359)
    except User.DoesNotExist:
        logger.error("Nick (pk=359) not found.")
        return

    future_dates = YetiSkateDate.objects.filter(skate_date__gt=date.today())

    for sd in future_dates:
        try:
            YetiSkateSession(skater=user, skate_date=sd, paid=True).save()
        except IntegrityError:
            pass
        except Exception as e:
            logger.error(f"Failed adding Nick to {sd}: {e}")


# ---------------------------------------------------
# Send notification emails
# ---------------------------------------------------
def send_skate_dates_email():
    recipients = Profile.objects.filter(yeti_skate_email=True).select_related("user")

    for profile in recipients:
        user = profile.user

        if not user.is_active or not user.email:
            continue

        subject = "New Yeti Skate Date Added"
        from_email = "no-reply@mg.oicwebapp.com"
        to_email = [user.email]

        text_message = (
            f"Hi {user.first_name},\n\n"
            "New Yeti Skate dates have been added.\n"
            "Sign up at:\n"
            "https://www.oicwebapp.com/web_apps/yeti_skate/\n\n"
            "If you wish to opt out, update your profile settings.\n\n"
            "Thank you for using OICWebApps.com!\n"
        )

        html_message = render_to_string(
            "yeti_skate_dates_email.html",
            {"recipient_name": user.first_name},
        )

        try:
            msg = EmailMultiAlternatives(subject, text_message, from_email, to_email)
            msg.attach_alternative(html_message, "text/html")
            msg.send()
            logger.info(f"Email sent to {user.email}")
        except Exception as e:
            logger.error(f"Email failed to {user.email}: {e}")


# ---------------------------------------------------
# MAIN EXECUTION
# ---------------------------------------------------
if __name__ == "__main__":

    today = date.today()

    from_date = today.strftime("%m/%d/%Y")
    to_date = from_date

    logger.info("=== YETI SKATE CRON START ===")

    # Only pull new dates on Sunday
    if today.weekday() == 6:   # Sunday
        sessions = get_schedule_data(from_date, to_date)
    else:
        sessions = []

    new_dates_added = False
    if sessions:
        new_dates_added = add_skate_dates(sessions)

    if new_dates_added:
        add_nick_to_skate()
        send_skate_dates_email()
        logger.info("New dates detected → emails sent.")
    else:
        logger.info("No new Yeti Skate dates added.")

    logger.info("=== YETI SKATE CRON END ===")
