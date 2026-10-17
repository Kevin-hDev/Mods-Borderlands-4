"""The normal mode's rewards (decision 119, spec-mode-normal.md, section 9): the experience of the enemies the player
kills, and the ammo and money they pick up, raised by the level's share (levels.py), never missions, sales or vending
machines.

Through the game's own multipliers, each read 1 on the hunter (trial 57): a PostAdd modifier of +1 on them doubled the
experience of each kill, each pile of money and each ammo pack picked up, and left sales and vending machines as they
were (trial 58, verified in game). Neither remover of the attribute library takes such a modifier off, though both
answer success; a modifier of the opposite sign does (trial 59, verified in game). So the share is added once on the
character the game is played with, and taken back by adding its opposite; what was added is kept here, never read
back from the game, whose gear moves the same multipliers (the money's read some 1.10 in September). The game drops
them all at its next launch (trial 58).

The character is the one play.py holds: a character gone (a new map, the main menu) ends that play, and the next one
adds the shares on the next character. Whether a character gone takes its modifiers with it is not verified.

The definition pointer is built with the parameter's own type, never without one: an untyped one passed to the game
crashed it (2026-09-28). Each call is written down before it is made.
"""

from typing import Any, Callable

import unrealsdk
from unrealsdk.unreal import FGbxDefPtr

LIBRARY = "/Script/GbxEngine.GbxAttributeBlueprintLibrary"
ADDER = "AddModifierToGbxAttribute"
KINDS = "EGbxAttributeModifierType"
OUTCOMES = "EGbxAttributeModifierActionExecOutput"
# The game's multiplier, and the level's field that holds its share.
ATTRIBUTES = (("Att_CombatXP_Multiplier", "xp"), ("att_pickupammo_multiplier", "ammo"),
              ("Att_PickupCash_Multiplier", "cash"))
UNREAD = -1.0


class Rewards:
    """level: levels.Level; announce(call, **fields): written before each call to the game."""

    def __init__(self, level: Any, announce: Callable[..., None]) -> None:
        self.shares = {name: float(getattr(level, field)) for name, field in ATTRIBUTES if getattr(level, field)}
        self.announce = announce
        self.added: dict[str, float] = {}

    def start(self, player: Any) -> dict:
        """Each share added on the player: what each multiplier reads after, or why it was not added."""
        found = _library()
        if isinstance(found, str):
            return {"refused": found}
        reads = {}
        for name, share in self.shares.items():
            done, reads[name] = self._add(found, player, name, share)
            if done:
                self.added[name] = share
        return {"shares": self.shares, "reads": reads}

    def put_back(self, player: Any) -> dict | str:
        """Each share added taken back by its opposite: what each reads after; "gone" with the player."""
        if not self.added:
            return "none"
        added, self.added = self.added, {}
        if player is None:
            return "gone"
        found = _library()
        if isinstance(found, str):
            return found
        return {name: self._add(found, player, name, -share)[1] for name, share in added.items()}

    def _add(self, found: tuple, player: Any, name: str, value: float) -> tuple[bool, float | str]:
        """A PostAdd of value on name: whether it was added, and what it reads after, "unread" if that read fails, or
        why the add failed."""
        library, kind = found
        self.announce(ADDER, attribute=name, value=value)
        try:
            library.AddModifierToGbxAttribute(FGbxDefPtr(name, kind), player, unrealsdk.find_enum(KINDS).PostAdd,
                                              value, True, next(iter(unrealsdk.find_enum(OUTCOMES))))
        except Exception as error:
            return False, f"failed:{type(error).__name__}"
        try:
            return True, round(float(library.GetValueOfAttribute(name, player, UNREAD)), 4)
        except Exception:
            return True, "unread"


def _library() -> tuple | str:
    """The attribute library and the adder's definition type, or why they cannot be had."""
    try:
        cls = unrealsdk.find_class(LIBRARY)
        kind = getattr(cls._find(ADDER)._find("attribute"), "Struct", None)
    except Exception as error:
        return f"no_library:{type(error).__name__}"
    if kind is None:
        return "untyped"
    return cls.ClassDefaultObject, kind
