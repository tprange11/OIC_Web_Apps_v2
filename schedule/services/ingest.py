"""Snapshot-based schedule ingest: fetch, normalize, enrich, assign lockers, and store
one RinkScheduleSnapshot per event under a ScheduleIngestRun."""
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


# The legacy scraper is reached only through schedulewerks_adapter, which wraps its
# module-level state; nothing here writes to RinkSchedule.


def run_schedule_ingest(
    *,
    triggered_by: str,
    dry_run: bool = False,
    user=None,
    days_ahead: int = 3,
):
    """
    Entry point for the management command and trigger_ingest view.

    Always creates a ScheduleIngestRun and marks it completed in the finally block,
    even on failure (the exception is re-raised after being recorded in run.notes).
    With dry_run=True the snapshots are built but not saved.
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

            # 1. Apply NameNormalizationRule replacements
            event["event"] = normalize_event_name(event["event"])

            # 2. Parse guest teams before the name gains a " vs " from enrichment
            event["guest_teams"] = parse_guest_teams(event["event"], event.get("usg"))
            if event["guest_teams"]:
                print("GUEST PARSED:", event["event"], event["guest_teams"])

            # 3. Append the opponent from usg for real games
            event["event"] = enrich_game_event_name(
                event["event"],
                event.get("usg", [])
            )

            # 4. Locker rooms: admin rules first, then rotation
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
    """Fetch raw events from ScheduleWerks via the legacy scraper adapter."""
    return fetch_schedulewerks_events(days_ahead)
