"""Reads the game's own key list, and finds in it the keys of the grapple and of the jump.

The keys come from the game's list rather than from fixed names, so the mod follows whatever the
player has set, gamepad included.

The grapple sits on the melee action. Verified in game on 2026-09-20: the mod wrote the game's own
list of 49 actions to the log, and not one of them carries the word "grapple". The game itself picks
between a grapple and a punch on that single button, by whether there is a point in range — which is
what Kevin said before the measure ("la touche du grappin c'est aussi la touche du coup de poing").

A name carrying "grapple" is still preferred when one exists, in case a game update ever adds one.
The whole list is written to the log once at each switch-on, which is how this was settled and how
the next surprise will be.
"""

import re
from typing import Any

from . import report

GRAPPLE_WORD = "grapple"
# The action the grapple really lives on in Borderlands 4, read from the game's own list.
# Action_Melee_1s is left alone: it is the held melee, and blocking a second key would take
# something away without giving anything back.
GRAPPLE_ACTIONS = ("Action_Melee",)
# Verified in Apex Movement, which binds this same action for its own air rules.
JUMP_ACTIONS = ("Action_Jump_HoldToGlide",)
# Bounded: the game lists a few dozen actions. Past this the line is cut, which is a log line's
# business, not a reason to lose the rest.
MAX_LISTED = 200
# Reject the entire snapshot instead of binding an arbitrary prefix that can hide a grapple action.
MAX_MAPPINGS = 1024
MAX_NAME_LENGTH = 256
NAME_PATTERN = re.compile(r"[A-Za-z0-9_]+")

_told = False


def reset() -> None:
    global _told
    _told = False


def _name(value: Any) -> str:
    name = str(value)
    if not 0 < len(name) <= MAX_NAME_LENGTH or NAME_PATTERN.fullmatch(name) is None:
        raise ValueError("invalid input name")
    return name


def snapshot(mappings: Any) -> list[Any]:
    """Validate at most one bounded input snapshot before using or logging any part of it."""
    found: list[Any] = []
    for mapping in mappings:
        if len(found) >= MAX_MAPPINGS:
            raise ValueError("too many input mappings")
        action = getattr(mapping, "Action", None)
        if action is not None:
            _name(action.Name)
            _name(mapping.Key.KeyName)
        found.append(mapping)
    return found


def action_names(mappings: list[Any]) -> list[str]:
    """Every action named in the list, once each, in the order the game gives them."""
    found: list[str] = []
    for mapping in snapshot(mappings):
        action = getattr(mapping, "Action", None)
        if action is None:
            continue
        name = str(action.Name)
        if name not in found:
            found.append(name)
    return found


def keys_for(mappings: list[Any], wanted: tuple[str, ...]) -> set[str]:
    return {str(mapping.Key.KeyName) for mapping in snapshot(mappings)
            if getattr(mapping, "Action", None) is not None and str(mapping.Action.Name) in wanted}


def grapple_actions(mappings: list[Any]) -> tuple[str, ...]:
    """The actions the mod takes over: a real grapple action if the game ever names one, melee otherwise."""
    named = tuple(name for name in action_names(mappings) if GRAPPLE_WORD in name.lower())
    if named:
        return named
    return tuple(name for name in action_names(mappings) if name in GRAPPLE_ACTIONS)


def grapple_keys(mappings: list[Any]) -> set[str]:
    return keys_for(mappings, grapple_actions(mappings))


def jump_keys(mappings: list[Any]) -> set[str]:
    return keys_for(mappings, JUMP_ACTIONS)


def tell_once(mappings: list[Any]) -> None:
    """Writes the game's whole action list to the log, one time, so the search can stop being a search."""
    global _told
    if _told or not mappings:
        return
    _told = True
    names = action_names(mappings)[:MAX_LISTED]
    report.note(f"the game lists {len(names)} actions: {', '.join(names)}")
    found = grapple_actions(mappings)
    if found:
        report.note(f"grapple taken from {', '.join(found)}, on key(s) {', '.join(sorted(grapple_keys(mappings)))}")
    else:
        report.warning("the game's key list names neither a grapple nor a melee action; the grapple has no key")
