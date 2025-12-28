from datetime import datetime, timedelta
from typing import Dict, Tuple, List
from schedule.models import LockerRoomRule


# ---------------- CONFIG ----------------
ROTATION_RESET_GAP = timedelta(hours=2)

DEFAULT_LOCKERS = {
    "North": [(1, 3), (2, 4)],
    "South": [(5, 8), (6, 9)],
}

# Runtime state (per ingest run)
_LAST_ASSIGNMENT = {}


# ---------------- PUBLIC API ----------------
def assign_lockers(event: Dict) -> Tuple[str, str, str, List[Dict]]:
    evaluations: List[Dict] = []

    # 1️⃣ RULES (absolute priority)
    rules = LockerRoomRule.objects.filter(active=True).order_by("priority")
    for rule in rules:
        if _rule_matches(rule, event):
            home, visitor = rule.home_locker_room, rule.visitor_locker_room
            return home, visitor, f"Matched rule #{rule.id}", evaluations

    # 2️⃣ SEQUENTIAL ROTATION
    home, visitor, reason = _rotate_sequentially(event)
    return home, visitor, reason, evaluations


# ---------------- RULE MATCH ----------------
def _rule_matches(rule: LockerRoomRule, event: Dict) -> bool:
    print("RULE CHECK:", rule.id, rule.event_type, event.get("usg"))
    if rule.rink and rule.rink.lower() not in event["rink"].lower():
        return False
    if rule.team_contains and rule.team_contains.lower() not in event["event"].lower():
        return False
    return True


# ---------------- ROTATION ENGINE ----------------
def _rotate_sequentially(event: Dict) -> Tuple[str, str, str]:
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
