"""Extracts home/guest team pairs from an event name or its usg field. The result is
attached to the event dict during ingest but is not stored on the snapshot yet."""
import re
from typing import List, Dict


def parse_guest_teams(event_name: str, usg=None) -> List[Dict]:
    """
    Return [{"home": ..., "guest": ...}, ...] parsed from the event name, or, if the
    name has no "vs", from a "game vs <opponent>" usg entry. TBD guests are dropped.
    """

    guests = []

    # Case 1: the name already reads "Team A vs Team B" (comma-separated for doubles)
    parts = [p.strip() for p in event_name.split(",")]

    for part in parts:
        if " vs " in part.lower():
            home, guest = re.split(r"\bvs\b", part, flags=re.IGNORECASE)
            home = home.strip()
            guest = guest.strip()

            if guest.lower() not in ("tbd", ""):
                guests.append({
                    "home": home,
                    "guest": guest,
                })

    if guests:
        print("GUEST PARSED:", event_name, guests)
        return guests

    # Case 2: single youth game, opponent only present in usg
    if usg:
        if isinstance(usg, list):
            usg = " ".join(usg)

        match = re.search(r"game\s+vs\s+(.*)", usg, re.IGNORECASE)
        if match:
            guest = match.group(1).strip()
            if guest and guest.lower() not in ("tbd",):
                guests.append({
                    "home": event_name,
                    "guest": guest,
                })
                print("GUEST PARSED (USG):", event_name, guests)

    return guests
