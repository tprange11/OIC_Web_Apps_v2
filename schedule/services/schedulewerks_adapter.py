"""Wraps the legacy scraper so the ingest pipeline gets plain event dicts."""
from datetime import date, timedelta
from datetime import datetime

# Importing the legacy scraper calls django.setup() and edits sys.path (see its header)
import schedule.scrape_schedule as legacy


def fetch_schedulewerks_events(days_ahead: int):
    """
    Fetch today plus days_ahead-1 more days through legacy get_schedule_data() and
    process_data(), and return raw event dicts with no locker fields or enrichment.

    start_time/end_time are the "HH:MM" strings ScheduleWerks returns; the legacy
    league-name shortening in process_data() still applies.
    """

    # Clear legacy globals to avoid bleed-over
    legacy.oic_schedule.clear()
    legacy.team_events.clear()

    today = date.today()
    from_date = today.strftime("%m/%d/%Y")
    to_date = (today + timedelta(days=days_ahead - 1)).strftime("%m/%d/%Y")

    # Fetch ScheduleWerks data
    data = legacy.get_schedule_data(from_date, to_date)

    # Legacy parsing only; locker rooms and team merging are done by the pipeline
    for i in range(days_ahead):
        d = today + timedelta(days=i)
        legacy.process_data(data, d.strftime("%m/%d/%Y"))

    events = []

    for item in legacy.oic_schedule:
        # Legacy item structure:
        # [date, start, end, rink, event, usg]

        usg = item[5]

        # Normalize usg to list
        if isinstance(usg, str):
            usg = [usg]
        elif usg is None:
            usg = []

        events.append({
            "schedule_date": _parse_date(item[0]),
            "start_time": item[1],
            "end_time": item[2],
            "rink": item[3],
            "event": item[4],
            "usg": usg,
        })

    print("RAW EVENTS SAMPLE:", events[6])
    return events


def _parse_date(mmddyyyy: str):
    """Convert the legacy MM/DD/YYYY string to a date."""
    return datetime.strptime(mmddyyyy, "%m/%d/%Y").date()
