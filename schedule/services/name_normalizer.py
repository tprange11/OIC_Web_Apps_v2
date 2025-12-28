from schedule.models import NameNormalizationRule


def normalize_event_name(event_name: str) -> str:
    if not event_name:
        return event_name

    rules = NameNormalizationRule.objects.filter(active=True)

    result = event_name

    for rule in rules:
        if rule.match_text.lower() in result.lower():
            result = result.replace(rule.match_text, rule.replace_with)

    # normalize whitespace
    result = " ".join(result.split())

    return result

