"""The player's weapon keys, listened to while the holster keeps the weapons restricted after a vehicle ride
(restriction.py): a press there is told at once, before the game reads it.

Why, 2026-09-26 (cosmetics/heirloom/docs/enquetes/2026-09-26-arme-bloquee-apres-vehicule.md): the restriction stays
until the camera, flying back after the exit, is in the eyes again, and a draw asked for during those 1.2 s was lost
(Kevin: "l'appui est perdu"). The game draws a weapon with no call a mod sees, but the SDK hands a key to a keybind
before the game (Apex Grapple blocks its presses so, verified in game). The keys are the game's own for its weapon
actions, read from the player's key list as Apex Grapple reads it (its input_list.py, verified in game on 2026-09-20):
they follow what the player set, controller included. Firing does not draw a weapon (verified in game on 2026-09-25).

A key is never blocked: the game keeps it.
"""

import re
from typing import Any, Callable

from mods_base import get_pc, keybind

from . import report

# The game's weapon actions, from its own list of 49 (releves/apex_grapple/2026-09-24-crash-2358/unrealsdk.log).
WEAPON_ACTIONS = ("Action_Weapon1", "Action_Weapon2", "Action_Weapon3", "Action_Weapon4", "Action_NextWeapon",
                  "Action_PrevWeapon", "Action_WeaponWheel")
PRESSED = "IE_Pressed"
# The game lists about a hundred keys; a list past this is read no further.
MAX_MAPPINGS = 1024
KEY_NAME = re.compile(r"[A-Za-z0-9_]{1,64}")

_binds: list[Any] = []


def keys(mappings: Any) -> set[str]:
    """The keys the player gave the game's weapon actions, among the first MAX_MAPPINGS of `mappings`."""
    found: set[str] = set()
    for index, mapping in enumerate(mappings):
        if index >= MAX_MAPPINGS:
            break
        action = getattr(mapping, "Action", None)
        if action is None or str(action.Name) not in WEAPON_ACTIONS:
            continue
        key = str(mapping.Key.KeyName)
        if KEY_NAME.fullmatch(key):
            found.add(key)
    return found


def _on(asked: Callable[[], None]) -> Callable[[Any], None]:
    def callback(event: Any) -> None:
        try:
            if getattr(event, "name", str(event)) == PRESSED:
                asked()
        except Exception as exc:
            report.error_once("draw_keys:press", f"weapon key press not followed after an error: {exc!r}")
        return None

    return callback


def listen(asked: Callable[[], None]) -> None:
    """Calls `asked` at each press of a weapon key the player has, until stop(). A key the SDK refuses lets every key
    go and raises."""
    stop()
    pc = get_pc(possibly_loading=True)
    mappings = getattr(getattr(pc, "PlayerInput", None), "EnhancedActionMappings", ()) if pc is not None else ()
    found = sorted(keys(mappings))
    try:
        for key in found:
            bind = keybind(f"{__package__}:draw:{key}", key, _on(asked), is_hidden=True, event_filter=None)
            _binds.append(bind)
            bind.enable()
    except Exception:
        stop()
        raise
    if found:
        report.note(f"weapon keys listened until the weapons are back: {', '.join(found)}")


def listening() -> bool:
    return bool(_binds)


def stop() -> None:
    """Lets every weapon key go. Never from inside a key's own callback: the SDK may still be running it."""
    while _binds:
        bind = _binds.pop()
        try:
            bind.disable()
        except Exception as exc:
            # Still bound, a key only tells a press no restriction waits for: restriction.asked then does nothing.
            report.error_once("draw_keys:stop", f"a weapon key could not be let go: {exc!r}")
