import re
from typing import List, Dict


def parse_guest_teams(event_name: str, usg=None) -> List[Dict]:
    """
    Parse home/guest teams from event name OR usg.
    """

    guests = []

    # -------------------------------------------------
    # Case 1: Already has "Team A vs Team B"
    # -------------------------------------------------
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

    # -------------------------------------------------
    # Case 2: Single-game youth → pull from USG
    # -------------------------------------------------
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
