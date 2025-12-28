from collections import defaultdict
from typing import Dict, List

from schedule.models import RinkScheduleSnapshot, ScheduleIngestRun


DIFF_FIELDS = [
    "end_time",
    "event",
    "home_locker_room",
    "visitor_locker_room",
]


def diff_runs(run_a_id, run_b_id):
    """
    Compare two ingest runs.

    Returns:
      {
        "added": [...],
        "removed": [...],
        "changed": [...],
        "unchanged": [...]
      }
    """

    run_a = ScheduleIngestRun.objects.get(id=run_a_id)
    run_b = ScheduleIngestRun.objects.get(id=run_b_id)

    snap_a = _load_snapshots(run_a)
    snap_b = _load_snapshots(run_b)

    keys = set(snap_a.keys()) | set(snap_b.keys())

    result = {
        "added": [],
        "removed": [],
        "changed": [],
        "unchanged": [],
    }

    for key in sorted(keys):
        a = snap_a.get(key)
        b = snap_b.get(key)

        if a and not b:
            result["removed"].append(_serialize(a))
        elif b and not a:
            result["added"].append(_serialize(b))
        elif a and b:
            changes = _compare_snapshots(a, b)
            if changes:
                result["changed"].append({
                    "key": key,
                    "before": _serialize(a),
                    "after": _serialize(b),
                    "changes": changes,
                })
            else:
                result["unchanged"].append(_serialize(b))

    return result


# -----------------------------
# Internal helpers
# -----------------------------

def _load_snapshots(run) -> Dict:
    """
    Return snapshots keyed by (date, time, rink)
    """
    snaps = {}

    for s in RinkScheduleSnapshot.objects.filter(run=run):
        key = (
            s.schedule_date,
            s.start_time,
            s.rink,
        )
        snaps[key] = s

    return snaps


def _compare_snapshots(a, b) -> Dict:
    """
    Compare two snapshots field-by-field.
    Returns dict of changed fields.
    """
    changes = {}

    for field in DIFF_FIELDS:
        if getattr(a, field) != getattr(b, field):
            changes[field] = {
                "before": getattr(a, field),
                "after": getattr(b, field),
            }

    return changes


def _serialize(snap) -> Dict:
    """
    Serialize snapshot to dict for UI / export.
    """
    return {
        "id": snap.id,
        "schedule_date": snap.schedule_date,
        "start_time": snap.start_time,
        "end_time": snap.end_time,
        "rink": snap.rink,
        "event": snap.event,
        "home_locker_room": snap.home_locker_room,
        "visitor_locker_room": snap.visitor_locker_room,
        "locker_reason": snap.locker_reason,
        "created_by": getattr(snap.created_by, "username", None),
        "updated_by": getattr(snap.updated_by, "username", None),
    }
