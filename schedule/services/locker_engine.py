"""Locker room assignment for the ingest pipeline: admin LockerRoomRule rows take
precedence, then each rink alternates between two locker room pairs."""
from datetime import datetime, timedelta
from typing import Dict, Tuple, List
from schedule.models import LockerRoomRule


# ---------------- CONFIG ----------------
# A gap of this long or more between events restarts the rotation at the first pair
ROTATION_RESET_GAP = timedelta(hours=3)

DEFAULT_LOCKERS = {
    "North": [(1, 3), (2, 4)],
    "South": [(5, 8), (6, 9)],
}

# Last (idx, time) assigned per rink. Module-level, so it persists across runs in the
# same process and is never reset; events must arrive in chronological order.
_LAST_ASSIGNMENT = {}


# ---------------- PUBLIC API ----------------
def assign_lockers(event: Dict) -> Tuple[str, str, str, List[Dict]]:
    '''Returns (home_lr, visitor_lr, reason, evaluations). `evaluations` is always
    empty for now; it is stored on the snapshot for a future rule-trace UI.'''
    evaluations: List[Dict] = []

    # 1. Admin rules, lowest priority number wins
    rules = LockerRoomRule.objects.filter(active=True).order_by("priority")
    for rule in rules:
        if _rule_matches(rule, event):
            home, visitor = rule.home_locker_room, rule.visitor_locker_room
            return home, visitor, f"Matched rule #{rule.id}", evaluations

    # 2. Fall back to alternating pairs
    home, visitor, reason = _rotate_sequentially(event)
    return home, visitor, reason, evaluations


# ---------------- RULE MATCH ----------------
def _rule_matches(rule: LockerRoomRule, event: Dict) -> bool:
    '''All of the rule's non-blank criteria must match (rink is a substring match, "Any" matches all).'''
    # Rink check
    if rule.rink and rule.rink.lower() != "any":
        if rule.rink.lower() not in event["rink"].lower():
            return False

    # Team / event name check
    if rule.team_contains:
        if rule.team_contains.lower() not in event["event"].lower():
            return False

    # Event type check (Game / Practice / etc.)
    if rule.event_type:
        usg = event.get("usg", [])
        if isinstance(usg, str):
            usg = [usg]

        if not any(rule.event_type.lower() in u.lower() for u in usg):
            return False

    return True


# ---------------- ROTATION ENGINE ----------------
def _rotate_sequentially(event: Dict) -> Tuple[str, str, str]:
    '''Alternate between the rink's two pairs, restarting after a long gap.'''
    rink = _normalize_rink(event["rink"])
    pairs = DEFAULT_LOCKERS.get(rink)

    if not pairs:
        return "", "", "No locker configuration"

    start_dt = _event_datetime(event)
    last = _LAST_ASSIGNMENT.get(rink)

    # Reset rotation if large gap
    if not last or start_dt - last["time"] >= ROTATION_RESET_GAP:
        idx = 0
        reason = f"Rotated locker assignment for {rink} rink (reset)"
    else:
        idx = (last["idx"] + 1) % len(pairs)
        reason = f"Rotated locker assignment for {rink} rink"

    home, visitor = pairs[idx]

    _LAST_ASSIGNMENT[rink] = {
        "idx": idx,
        "time": start_dt,
    }

    return str(home), str(visitor), reason


# ---------------- HELPERS ----------------
def _event_datetime(event: Dict) -> datetime:
    # Relies on str() of the date and "HH:MM" start_time strings from the adapter
    return datetime.strptime(
        f"{event['schedule_date']} {event['start_time']}",
        "%Y-%m-%d %H:%M",
    )


def _normalize_rink(rink: str) -> str:
    r = rink.lower()
    if "north" in r:
        return "North"
    if "south" in r:
        return "South"
    return ""
