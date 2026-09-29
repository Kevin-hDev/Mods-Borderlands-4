"""Turns the game's depth of field off while the heirloom is shown, and gives the player's own value back when it
goes: the one place the mod changes it.

Why, 2026-09-29 (cosmetics/heirloom/docs/heirloom.md, section 18, "Essai de la hache en textures virtuelles"): the
game's materials draw a first-person object as if it stood at 16 % of its distance to the eye ("Scale In Depth"); the
axe held at rest came so near that the game's depth of field blurred the parts closest to the eye, and
r.DepthOfFieldQuality 0 typed in the console made them sharp (Kevin, 2:15). Kevin chose that the mod turns the depth
of field off while an heirloom is shown, rather than moving the axe away from the eye: it holds for every heirloom and
for every animation that brings one near the face. Hidden by a weapon, a climb or the camera, the heirloom gives the
value back. The value is read before it is changed and given back as it was read. A value set so lasts until the game
closes (the console's own setting, never written to the player's settings files; not yet seen in game): a game that
stops while the heirloom is shown starts again with the player's own. While it is off, a graphics setting the player
changes does not reach the depth of field until the game restarts.
"""

import types
from typing import Any, Callable

import unrealsdk
from mods_base import get_pc

Say = Callable[[str], None]
VARIABLE = "r.DepthOfFieldQuality"
OFF = 0
LIBRARY = "KismetSystemLibrary"

# The player's value while ours is set, None while the game has its own; who says what happens.
STATE = types.SimpleNamespace(kept=None, say=None)


def _run(command: str, say: Say) -> bool:
    pc = get_pc()
    if pc is None:
        say(f"depth of field: no player controller, {command!r} not sent")
        return False
    say(f"depth of field: ExecuteConsoleCommand {command!r}")
    unrealsdk.find_class(LIBRARY).ClassDefaultObject.ExecuteConsoleCommand(pc, command, pc)
    return True


def follow(shown: bool, say: Say) -> None:
    """Off while the heirloom is `shown`, the player's value back once it is not; an engine call that fails is said
    and leaves the heirloom's showing alone."""
    try:
        if shown and STATE.kept is None:
            kept = unrealsdk.find_class(LIBRARY).ClassDefaultObject.GetConsoleVariableIntValue(VARIABLE)
            if _run(f"{VARIABLE} {OFF}", say):
                STATE.kept, STATE.say = kept, say
                say(f"depth of field off while the heirloom is shown (the player's value: {kept})")
        elif not shown:
            give_back()
    except Exception as exc:
        say(f"depth of field could not be changed: {exc!r}")


def give_back() -> None:
    """The player's value back, if ours is set."""
    if STATE.kept is None:
        return
    kept, say = STATE.kept, STATE.say
    try:
        if _run(f"{VARIABLE} {kept}", say):
            STATE.kept = None
            say(f"depth of field back to the player's value, {kept}")
    except Exception as exc:
        say(f"depth of field could not be given back: {exc!r}")
