"""Partial native results acknowledge only the settings actually rendered."""
from .generated_ads import (FRAMING_APPLIED, FRAMING_POSITION_APPLIED_ZOOM_UNAVAILABLE,
                            FRAMING_ZOOM_APPLIED_POSITION_UNAVAILABLE)

START_FAILURE = "Camera framing initialization failed; historical framing retained."

PARTIAL_REASONS = {
    FRAMING_POSITION_APPLIED_ZOOM_UNAVAILABLE: "zoom_unavailable",
    FRAMING_ZOOM_APPLIED_POSITION_UNAVAILABLE: "position_unavailable",
}
MESSAGES = {
    "unavailable": "Camera framing unavailable; historical framing retained.",
    "zoom_unavailable": "Camera position applied; extra aiming zoom unavailable.",
    "position_unavailable": "Extra aiming zoom applied; camera position unavailable.",
}


def confirmation(status, values, previous):
    if status == FRAMING_APPLIED:
        return True
    if status == FRAMING_POSITION_APPLIED_ZOOM_UNAVAILABLE:
        return values[0] == 0 or (previous is not None and values[0] == previous[0])
    if status == FRAMING_ZOOM_APPLIED_POSITION_UNAVAILABLE:
        return previous is not None and values[1:] == previous[1:]
    return False if status > 1 else None
