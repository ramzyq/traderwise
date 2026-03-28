HARD_VIOLATION_PHRASES = ("i recommend", "you must")


def post_process_response(text: str) -> str:
    updated = text.replace("you should", "one thing to consider")
    # Strip markdown — WhatsApp renders plain text only
    updated = updated.replace("**", "").replace("__", "").replace("##", "").replace("# ", "")
    updated = updated.strip()
    if not updated.endswith("?"):
        updated = f"{updated}?"
    return updated


def has_hard_violation(text: str) -> bool:
    lowered = text.lower()
    return any(phrase in lowered for phrase in HARD_VIOLATION_PHRASES)
