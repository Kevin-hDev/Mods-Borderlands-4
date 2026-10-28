"""The game's side of the bigger Lost Loot (lost_loot.py): the machine's limit read, and a bonus added to it.

The limit is the attribute lost_loot_storage_maxsize, read on the player controller (trial 106, vérifié en jeu). The
game's eight SDU upgrades each add a PreAdd modifier of 1 to it (progress_graph, Lost_Loot_01 to 08, source unique);
this adds one the same way, through GbxAttributeBlueprintLibrary.AddModifierToGbxAttribute. With bAutoRefresh on the
machine's real count follows and it fills past the game's limit (trial 109, 80 items of 400); off, only the shown
limit moved (trial 108). A modifier cannot be removed: its handle is a struct the SDK cannot copy (enemy research,
27 September 2026), so the bonus is taken back by adding its opposite. A loaded save starts with no bonus (trial 108).
The add function's parameters are checked before each call, by name and kind, as the trials checked them.
"""

import math
from typing import Any

import unrealsdk

LIBRARY = "GbxAttributeBlueprintLibrary"
READ = "GetValueOfAttribute"
ADD = "AddModifierToGbxAttribute"
LIMIT = "lost_loot_storage_maxsize"
DEF_TYPE = "GbxAttributeDef"
UNREAD = -1.0
SIGNATURE = (("attribute", "GbxDefPtrProperty"), ("ContextSource", "ObjectProperty"),
             ("ModifierType", "EnumProperty"), ("modifiervalue", "FloatProperty"), ("bAutoRefresh", "BoolProperty"),
             ("ModifierActionResult", "EnumProperty"), ("ReturnValue", "StructProperty"))
SUCCESS = 0


def owner(pc: Any) -> str | None:
    """The name of the player state a bonus belongs to: a loaded save brings a new one, without the bonus."""
    try:
        name = str(pc.PlayerState.Name)
    except Exception:
        return None
    return name or None


def limit(pc: Any) -> float | None:
    """The machine's limit as the game resolves it now; None when it cannot be read."""
    try:
        library = unrealsdk.find_class(LIBRARY).ClassDefaultObject
        value = float(getattr(library, READ)(LIMIT, pc, UNREAD))
    except Exception:
        return None
    return round(value, 4) if math.isfinite(value) and value != UNREAD else None


def _checked(library: Any) -> tuple[Any, Any, Any]:
    fn = library._find(ADD)
    props = list(fn._properties())
    found = tuple((str(prop.Name), str(prop.Class.Name)) for prop in props)
    if found != SIGNATURE:
        raise ValueError(f"unexpected {ADD} parameters")
    kind, outcome = props[2].Enum._as_py(), props[5].Enum._as_py()
    if (int(kind.PreAdd), int(outcome.success)) != (1, SUCCESS):
        raise ValueError(f"unexpected {ADD} enums")
    return fn, kind, outcome


def add(pc: Any, delta: float) -> int | None:
    """Adds a PreAdd bonus of delta to the limit, refreshed; the game's outcome (0 success), None when it gave none.
    Raises before the call when the function is not the one the trials used."""
    library = unrealsdk.find_class(LIBRARY)
    fn, kind, outcome = _checked(library)
    params = unrealsdk.unreal.WrappedStruct(fn, attribute=unrealsdk.unreal.FGbxDefPtr(LIMIT, DEF_TYPE),
                                            ContextSource=pc, ModifierType=kind.PreAdd, modifiervalue=delta,
                                            bAutoRefresh=True, ModifierActionResult=outcome.failure)
    returned = getattr(library.ClassDefaultObject, ADD)(params)
    # Trials 109 and 110: three values, the outcome last.
    try:
        return int(returned[-1]) if type(returned) is tuple and returned else None
    except (TypeError, ValueError):
        return None
