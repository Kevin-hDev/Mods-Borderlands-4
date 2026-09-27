"""Keep Orbit refusal feedback generic and emitted only at state boundaries."""

ORBIT_REFUSAL = "Orbit Camera unavailable; Third Person remains active."
ORBIT_SAVE_FAILURE = "Orbit Camera setting could not be saved."


def note_refusal(settings):
    note = getattr(settings, "note", None)
    if callable(note):
        note(ORBIT_REFUSAL)


def note_save_failure(settings):
    note = getattr(settings, "note", None)
    if callable(note):
        note(ORBIT_SAVE_FAILURE)
