"""A setting moved to another line of the menu keeps the value the player saved.

mods_base saves each setting under its menu line and reads it back from there alone: a setting moved to another line
would come back at its default. "Show the rope" moved from the shot's line to the look's after 1.0.9 (Kevin,
2026-10-14), and Kevin's own file had it off. The value is taken from its old line once, when its new line does not
hold it yet; the next save writes it at its new place. Read tolerantly: a file that cannot be read leaves the values
mods_base loaded, said in the log; keep_in_bounds checks what is taken, as every loaded value.
"""

import json
from typing import Any

from . import report

# Bounded: the settings file is a few kilobytes; anything far larger is not ours to read.
MAX_BYTES = 1_000_000


def adopt(mod: Any, moved: tuple) -> list[str]:
    """For each (option, old line, new line) of `moved`, the value saved under the old line when the new one has none;
    returns the identifiers taken."""
    path = getattr(mod, "settings_file", None)
    if path is None or not path.is_file():
        return []
    try:
        if path.stat().st_size > MAX_BYTES:
            raise ValueError("settings file too large")
        saved = json.loads(path.read_text(encoding="utf-8")).get("options", {})
        if not isinstance(saved, dict):
            raise ValueError("settings file options are not a table")
    except (OSError, ValueError, AttributeError) as error:
        report.warning(f"moved settings not read: {type(error).__name__}")
        return []
    taken = []
    for option, old_line, new_line in moved:
        new, old = saved.get(new_line), saved.get(old_line)
        if isinstance(new, dict) and option.identifier in new:
            continue
        if isinstance(old, dict) and option.identifier in old:
            option.value = old[option.identifier]
            taken.append(option.identifier)
    if taken:
        report.note(f"settings kept from their former menu line: {', '.join(taken)}")
    return taken
