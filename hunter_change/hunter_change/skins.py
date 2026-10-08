"""Which skins the player owns, as the game says it: the game's own always, the prison's once the prison prologue is
done, the premium one with the Ornate Order Pack (docs/reverse-and-change-hunters/enquetes/2026-10-07-skins-premium.md,
both facts read in game on 2026-10-07). The window offers no other: a skin not unlocked leaves the character without a
body (essai 22).

Each fact is read by FactsBlueprintLibrary.ReadFact, the game's own reader, whose parameters are checked once per
session against those read in game; a reader that differs, or a fact that cannot be read, offers the game's own only.
"""

from itertools import islice
from typing import Any

import unrealsdk
from mods_base import get_pc

from . import hunters, report

FUNCTION = "/Script/GbxGame.FactsBlueprintLibrary:ReadFact"
LIBRARY = "FactsBlueprintLibrary"
# Name, kind, offset, size and whether it is an output, as the game showed them on 2026-10-04 and 2026-10-07.
PARAMETERS = (
    ("OwnerContext", "ObjectProperty", 0, 8, False),
    ("AddressString", "StrProperty", 8, 16, False),
    ("AsName", "NameProperty", 24, 8, True),
    ("AsInt", "IntProperty", 32, 4, True),
    ("AsBool", "BoolProperty", 36, 1, True),
)
OUT_PARM = 0x100
OUTPUTS = ("None", 0, False)
FACTS = {hunters.PRISON: "transient.prologue_completed", hunters.PREMIUM: "entitlement.premium.enabled"}

# The library's object once its ReadFact is checked; False once it was refused, for the whole session.
_reader: Any = None


def _check(function: Any) -> None:
    fields = tuple(islice(function._properties(), len(PARAMETERS) + 1))
    measured = tuple((str(prop.Name), str(prop.Class.Name), prop.Offset_Internal, prop.ElementSize,
                      bool(int(prop.PropertyFlags) & OUT_PARM)) for prop in fields)
    if measured != PARAMETERS:
        raise ValueError("ReadFact differs from the one read in game")


def _library() -> Any:
    global _reader
    if _reader is None:
        try:
            _check(unrealsdk.find_object("Function", FUNCTION))
            _reader = unrealsdk.find_class(LIBRARY).ClassDefaultObject
        except (ValueError, AttributeError, TypeError) as error:
            report.error_once("skins:reader", f"the game's fact reader is not the one known ({error}), "
                                              "only the hunters' own skins are offered")
            _reader = False
    return _reader or None


def _true(result: Any) -> bool:
    """ReadFact's bool; pyunrealsdk puts the missing return value first."""
    return type(result) is tuple and len(result) == 4 and result[3] is True


def owned() -> tuple[str, ...]:
    """The skins the player owns, in the window's order; the game's own alone outside a game or when unsure."""
    library, pc = _library(), get_pc()
    if library is None or pc is None:
        return (hunters.DEFAULT,)
    found = [hunters.DEFAULT]
    for skin in hunters.SKINS[1:]:
        try:
            result = library.ReadFact(pc, FACTS[skin], *OUTPUTS)
        except (RuntimeError, ValueError, TypeError) as error:
            report.error_once(f"skins:{skin}", f"whether the {skin} skin is owned could not be read ({error}), "
                                               "it is not offered")
            continue
        if _true(result):
            found.append(skin)
    return tuple(found)
