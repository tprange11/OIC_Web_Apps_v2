import uuid
from datetime import date, timedelta
from django.utils import timezone
from django.db import transaction

from schedule.models import (
    ScheduleIngestRun,
    RinkScheduleSnapshot,
)

from schedule.services.schedulewerks_adapter import fetch_schedulewerks_events
from schedule.services.locker_engine import assign_lockers
from schedule.services.name_normalizer import normalize_event_name
from schedule.services.game_enricher import enrich_game_event_name
from schedule.services.guest_parser import parse_guest_teams


# IMPORTANT:
# This file does NOT import or modify existing scrape scripts.
# We will call them explicitly and safely.


def run_schedule_ingest(
    *,
    triggered_by: str,
    dry_run: bool = False,
    user=None,
    days_ahead: int = 3,
):
    """
    Canonical ingest entry point.
    Safe for manual, scheduled, preview, and rollback runs.
    """

    run = ScheduleIngestRun.objects.create(
        triggered_by=triggered_by,
        dry_run=dry_run,
        created_by=user,
        updated_by=user,
    )

    try:
        events = _collect_events(days_ahead)

        snapshots = []

        for event in events:
            print("DEBUG EVENT (raw):", event)

            # 1️⃣ Normalize base event name
            event["event"] = normalize_event_name(event["event"])

            # 2️⃣ Parse guest teams BEFORE enrichment
            event["guest_teams"] = parse_guest_teams(event["event"], event.get("usg"))
            if event["guest_teams"]:
                print("GUEST PARSED:", event["event"], event["guest_teams"])

            # 3️⃣ Enrich event name using USG only
            event["event"] = enrich_game_event_name(
                event["event"],
                event.get("usg", [])
            )

            # 4️⃣ Locker assignment
            home_lr, visitor_lr, reason, evaluation = assign_lockers(event)

            snapshots.append(
                RinkScheduleSnapshot(
                    run=run,
                    schedule_date=event["schedule_date"],
                    start_time=event["start_time"],
                    end_time=event["end_time"],
                    rink=event["rink"],
                    event=event["event"],
                    home_locker_room=home_lr,
                    visitor_locker_room=visitor_lr,
                    locker_reason=reason,
                    locker_evaluation=evaluation,
                    created_by=user,
                    updated_by=user,
                )
            )

        if not dry_run:
            with transaction.atomic():
                RinkScheduleSnapshot.objects.bulk_create(snapshots)

        run.success = True

    except Exception as exc:
        run.success = False
        run.notes = str(exc)
        raise

    finally:
        run.completed_at = timezone.now()
        run.updated_by = user
        run.save()

    return run


# -------------------------------
# Internal helpers
# -------------------------------


def _collect_events(days_ahead: int):
    """
    Collect real events from ScheduleWerks via scrape_schedule.py.
    """
    return fetch_schedulewerks_events(days_ahead)
