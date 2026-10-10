"""A settings file saved before an option existed keeps what the player had (Kevin, 2026-10-09: "on ne doit pas
modifier les réglages des joueurs qui utilisent nos mods et ont déjà une config à eux").

Auto sprint in third person: before Apex Movement 1.2.14 auto sprint ran in every view; 1.2.14 turned it off in third
person, and its own switch came after. A file that has auto sprint on and no such switch is a player's own setup from
before: auto sprint stays on in third person. A new install, with no file, gets the switch's default, off.
"""

import json
from pathlib import Path
from typing import Any

GROUP, SWITCH, OPTION = "auto_sprint_menu", "auto_sprint", "auto_sprint_third_person"


def keeps_third_person(saved: Any) -> bool:
    """Whether a saved file from before the third-person switch had auto sprint on."""
    options = saved.get("options") if isinstance(saved, dict) else None
    group = options.get(GROUP) if isinstance(options, dict) else None
    return isinstance(group, dict) and OPTION not in group and group.get(SWITCH) is True


def apply(path: Path | None, option: Any) -> bool:
    """Turns the third-person switch on for such a file; an unreadable file is left to the mod's own loading."""
    if path is None or not path.exists():
        return False
    try:
        saved = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False
    if not keeps_third_person(saved):
        return False
    option.value = True
    return True
