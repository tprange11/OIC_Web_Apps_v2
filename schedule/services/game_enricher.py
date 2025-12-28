import re

DISABLED_USG_PREFIXES = {
    "open hockey",
    "cross ice game",
    "practice",
    "public skate",
    "house game vs",
}


def enrich_game_event_name(event_name: str, usg) -> str:
    """
    Enhance event name ONLY for true games with real opponents.
    Explicitly skip operational / non-opponent event types.

    usg may be:
      - str
      - list[str]
    """

    if not event_name or not usg:
        return event_name

    # Normalize usg → list[str]
    if isinstance(usg, str):
        usg_list = [usg]
    else:
        usg_list = list(usg)

    usg_clean_list = [u.strip().lower() for u in usg_list if u]

    # Hard stop: do NOT enhance these categories
    for u in usg_clean_list:
        for prefix in DISABLED_USG_PREFIXES:
            if u.startswith(prefix):
                return event_name

    # Only proceed if at least one USG indicates a game
    if not any("game" in u for u in usg_clean_list):
        return event_name

    # Avoid double-appending
    if " vs " in event_name.lower():
        return event_name

    # Try to extract opponent from any USG entry
    for raw_usg in usg_list:
        match = re.search(r"\bvs\.?\s+(.*)", raw_usg, re.IGNORECASE)
        if not match:
            continue

        opponent = match.group(1).strip()

        # Ignore empty / TBD opponents
        if not opponent or opponent.lower() in ("tbd",):
            continue

        return f"{event_name} vs {opponent}"

    return event_name
