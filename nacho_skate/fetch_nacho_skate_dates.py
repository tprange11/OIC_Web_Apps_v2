#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Nacho Skate Scheduler Script
----------------------------
Fetches Nacho Skate dates, inserts new sessions, processes regular skaters,
and sends notification emails.

Supports flags:
  --force-email         Send emails immediately (ignores weekday/schedule)
  --force-regulars      Add regulars to all future sessions regardless of balance
  --test-email <addr>   Send ONE test email to a single address
  --dry-run             Log actions but do NOT write to DB or send mail
"""

import os
import sys
import json
import pytz
import logging
import requests
import argparse
from datetime import date, datetime, timedelta

# Timezone
CENTRAL = pytz.timezone("America/Chicago")

# Django environment setup
if os.name == "nt":
    sys.path.append("C:\\Users\\brian\\Documents\\Python\\OIC_Web_Apps\\")
else:
    sys.path.append("/home/OIC/OIC_Web_Apps/")

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "OIC_Web_Apps.settings")

import django
django.setup()

# Django imports
from django.db import IntegrityError
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

from nacho_skate.models import NachoSkateDate, NachoSkateSession, NachoSkateRegular
from accounts.models import Profile, UserCredit
from programs.models import Program

# -------------------------------------------------------------------
# LOGGING SETUP
# -------------------------------------------------------------------
LOG_PATH = "/home/OIC/logs/nacho_skate.log"
logger = logging.getLogger("nacho_skate")
logger.setLevel(logging.INFO)

handler = logging.FileHandler(LOG_PATH)
handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
logger.addHandler(handler)

# -------------------------------------------------------------------

def fetch_schedule(from_date, to_date):
    """Pulls OIC schedule data for the given period."""
    url = f"https://ozaukeeicecenter.schedulewerks.com/public/ajax/swCalGet?tid=-1&from={from_date}&to={to_date}&Complex=-1"

    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        logger.info(f"Fetched {len(data)} schedule entries.")
        return data
    except Exception as e:
        logger.error(f"Failed fetching schedule: {e}")
        return []


def extract_nacho_sessions(data):
    """Parse ScheduleWerks JSON for Nacho Skate events."""
    results = []
    for item in data:
        if "Nacho" in item.get("text", ""):
            raw_date = item["start_date"].split(" ")[0]  # MM/DD/YYYY
            clean_date = f"{raw_date[6:]}-{raw_date[:2]}-{raw_date[3:5]}"
            start = item["start_date"][-5:]
            end = item["end_date"][-5:]
            results.append((clean_date, start, end))

    logger.info(f"Found {len(results)} Nacho Skate events.")
    return results


def add_new_dates(sessions, dry_run=False):
    """Insert new Nacho Skate dates into the DB."""
    added = False
    for session in sessions:
        try:
            if not dry_run:
                NachoSkateDate(
                    skate_date=session[0],
                    start_time=session[1],
                    end_time=session[2],
                ).save()

            logger.info(f"Added new Nacho Skate: {session}")
            added = True

        except IntegrityError:
            logger.info(f"Duplicate date skipped: {session}")

    return added


def add_regulars(force=False, dry_run=False):
    """Registers regular skaters if they have credit OR if forced."""
    regulars = NachoSkateRegular.objects.all().select_related("regular")
    sessions = NachoSkateDate.objects.filter(skate_date__gt=date.today())
    price = Program.objects.get(id=15).skater_price

    added = 0

    for session in sessions:
        for regular in regulars:
            try:
                credit = UserCredit.objects.get(user=regular.regular)

                if credit.pk == 870:
                    allowed = True
                elif force:
                    allowed = True
                else:
                    allowed = credit.balance >= price

                if not allowed:
                    continue

                if not dry_run:
                    NachoSkateSession(
                        skater=regular.regular,
                        skate_date=session,
                        paid=True
                    ).save()

                    if credit.pk != 870 and not force:
                        credit.balance -= price
                        credit.paid = credit.balance > 0
                        credit.save()

                added += 1

            except (UserCredit.DoesNotExist, IntegrityError):
                continue

    logger.info(f"Regulars added: {added}")
    return added


def send_emails(dry_run=False, test_email=None):
    """Send Nacho Skate email notifications."""

    if test_email:
        recipients = [{"user": type("obj", (object,), {"email": test_email, "first_name": "Test"})}]
        logger.info(f"Sending TEST email to {test_email}")
    else:
        recipients = Profile.objects.filter(nacho_skate_email=True).select_related("user")
        logger.info(f"Sending emails to {recipients.count()} recipients")

    for r in recipients:
        email = test_email or r.user.email
        fname = test_email and "Test" or r.user.first_name

        subject = "New Nacho Skate Date Added"
        from_email = "no-reply@mg.oicwebapp.com"

        text_message = (
            f"Hi {fname},\n\n"
            "New Nacho Skate dates are now available online.\n\n"
            "https://www.oicwebapp.com/web_apps/nacho_skate/\n\n"
            "If you no longer wish to receive these emails, update your profile.\n\n"
        )

        html_message = render_to_string("nacho_skate_dates_email.html", {
            "recipient_name": fname,
        })

        if dry_run:
            logger.info(f"[DRY RUN] Would send email to {email}")
            continue

        try:
            mail = EmailMultiAlternatives(subject, text_message, from_email, [email])
            mail.attach_alternative(html_message, "text/html")
            mail.send()
            logger.info(f"Email sent to: {email}")
        except Exception as e:
            logger.error(f"Email failed for {email}: {e}")


# -------------------------------------------------------------------
# MAIN
# -------------------------------------------------------------------

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Nacho Skate Scheduler")
    parser.add_argument("--force-email", action="store_true", help="Send emails immediately")
    parser.add_argument("--force-regulars", action="store_true", help="Add regulars regardless of balance")
    parser.add_argument("--test-email", type=str, help="Send a test email to one address")
    parser.add_argument("--dry-run", action="store_true", help="Do not send mail or change DB")

    args = parser.parse_args()

    logger.info("===== Nacho Skate START =====")

    today = datetime.now(CENTRAL).date()
    weekday = today.weekday()

    logger.info(f"Today (Central): {today} — Weekday {weekday}")

    # ---------------------------------------------
    # PRIORITY 1: TEST EMAIL ALWAYS SENDS IMMEDIATELY
    # ---------------------------------------------
    if args.test_email:
        logger.info(f"TEST EMAIL MODE — sending only to {args.test_email}")
        send_emails(dry_run=args.dry_run, test_email=args.test_email)
        logger.info("===== Nacho Skate END =====")
        sys.exit(0)

    # ---------------------------------------------
    # PRIORITY 2: FORCE EMAIL MODE
    # ---------------------------------------------
    if args.force_email:
        logger.info("FORCE EMAIL MODE — sending to all recipients")
        send_emails(dry_run=args.dry_run)
        logger.info("===== Nacho Skate END =====")
        sys.exit(0)

    # ---------------------------------------------
    # NORMAL SUNDAY OPERATION
    # ---------------------------------------------
    if weekday == 6:
        logger.info("Sunday detected — pulling schedule")

        fetch_from = (today + timedelta(days=3)).strftime("%m/%d/%Y")
        data = fetch_schedule(fetch_from, fetch_from)
        sessions = extract_nacho_sessions(data)

        new_dates_added = add_new_dates(sessions, dry_run=args.dry_run)

        if new_dates_added:
            add_regulars(force=args.force_regulars, dry_run=args.dry_run)
            send_emails(dry_run=args.dry_run)

    logger.info("===== Nacho Skate END =====")
