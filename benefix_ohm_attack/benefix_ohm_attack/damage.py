"""One hit of the beam: the game's own DamageStatics.CauseDamage, called with every parameter it asks for.

Verified in game on 2026-10-01 (docs/attaque-rayon/enquetes/2026-10-01-degats.md): with the game's player skill
damage data, one call is one hit of exactly the amount given, which the game multiplies by the element's bonus and
applies within a quarter second.

The SDK wants every parameter of a call, the outputs included, so the signature is read from the game once and
each parameter not given gets the empty value of its kind. A handle inside an empty struct gets its field's own
type: the SDK refuses a struct whose handle carries another (in game, same day, before any call). A kind with no
known empty value refuses the hit rather than guess: a GbxDefPtr built in Python has crashed the game (2026-09-28).
"""

from itertools import islice
from typing import Any

import unrealsdk
from unrealsdk.unreal import FGameDataHandle

from . import report

LIBRARY, FUNCTION = "DamageStatics", "CauseDamage"
# The game's own "a player's skill hits one target" (a DamageDef under OakPlayerDamageDatas, in the game's data).
DAMAGE_DATA = "damage_player_shared_targeted"
MAX_PARAMETERS = 40
MAX_STRUCT_FIELDS = 200
MAX_STRUCT_DEPTH = 3
# Unreal's property flags: a parameter, the return value.
PARAM, RETURN = 0x80, 0x400
HANDLE_KIND, STRUCT_KIND = "GameDataHandleProperty", "StructProperty"
# The name Unreal gives to "no name": a handle carrying it points at nothing.
EMPTY_NAME = "None"
EMPTY_VALUES = {
    "BoolProperty": bool, "FloatProperty": float, "DoubleProperty": float,
    "IntProperty": int, "ByteProperty": int, "EnumProperty": int,
    "NameProperty": lambda: EMPTY_NAME, "StrProperty": str, "ArrayProperty": list,
    "ObjectProperty": lambda: None, "ClassProperty": lambda: None,
}

# The signature as plain data, read once: no game object is kept.
_rows: list[dict] | None = None
_refused = False


class Refused(Exception):
    """The call is not attempted: the signature is not one this mod knows how to fill."""


def forget() -> None:
    global _rows, _refused
    _rows = None
    _refused = False


def refused() -> bool:
    """Whether the game refused a hit this session: no hit is tried again until the mod is switched on anew."""
    return _refused


def _handles_in(struct: Any, trail: tuple, found: list, seen: list, depth: int) -> None:
    if depth > MAX_STRUCT_DEPTH:
        raise Refused("a struct nests deeper than this mod follows")
    for field in islice(struct._properties(), MAX_STRUCT_FIELDS + 1):
        seen.append(None)
        if len(seen) > MAX_STRUCT_FIELDS:
            raise Refused("a struct holds more fields than this mod follows")
        kind, here = str(field.Class.Name), trail + (str(field.Name),)
        if kind == HANDLE_KIND:
            found.append((here, int(field.TypeHandle)))
        elif kind == STRUCT_KIND:
            _handles_in(field.Struct, here, found, seen, depth + 1)


def describe(function: Any) -> list[dict]:
    """One row per parameter: its name, its kind, and what its empty value needs."""
    props = list(islice(function._properties(), MAX_PARAMETERS + 1))
    if len(props) > MAX_PARAMETERS:
        raise Refused("the function has more parameters than this mod reads")
    rows = []
    for prop in props:
        flags = int(prop.PropertyFlags)
        if not flags & PARAM or flags & RETURN:
            continue
        row: dict = {"name": str(prop.Name), "kind": str(prop.Class.Name)}
        if row["kind"] == STRUCT_KIND:
            row["struct"], row["handles"] = str(prop.Struct._path_name()), []
            _handles_in(prop.Struct, (), row["handles"], [], 1)
        elif row["kind"] == HANDLE_KIND:
            row["handle_type"] = int(prop.TypeHandle)
        elif row["kind"] not in EMPTY_VALUES:
            raise Refused(f"{row['name']}: no empty value known for {row['kind']}")
        rows.append(row)
    return rows


def _empty_struct(row: dict) -> Any:
    try:
        made = unrealsdk.make_struct(row["struct"])
    except Exception:
        # The path is what the game gives; some SDK builds only take the bare name.
        made = unrealsdk.make_struct(row["struct"].rsplit(".", 1)[-1])
    for trail, kind in row["handles"]:
        holder = made
        for step in trail[:-1]:
            holder = getattr(holder, step)
        setattr(holder, trail[-1], FGameDataHandle(kind, EMPTY_NAME))
    return made


def arguments(rows: list[dict], given: dict, handles: dict) -> dict:
    """Every parameter of the call by name: the given ones, the named handles, empty values for the rest."""
    names = {row["name"] for row in rows}
    unknown = sorted((set(given) | set(handles)) - names)
    if unknown:
        raise Refused("not in the signature: " + ", ".join(unknown))
    filled = {}
    for row in rows:
        name, kind = row["name"], row["kind"]
        if name in handles and kind != HANDLE_KIND:
            raise Refused(f"{name}: expected a game data handle, the game says {kind}")
        if name in given:
            filled[name] = given[name]
        elif kind == HANDLE_KIND:
            filled[name] = FGameDataHandle(row["handle_type"], handles.get(name, EMPTY_NAME))
        elif kind == STRUCT_KIND:
            filled[name] = _empty_struct(row)
        else:
            filled[name] = EMPTY_VALUES[kind]()
    return filled


def hit(character: Any, target: Any, where: Any, amount: float, damage_type: str) -> bool:
    """One hit on the target, where a ray met it; with no ray's answer to give (None), the game is handed the
    empty one of its own kind. False, said once, when the game's function is not the one this mod knows."""
    global _rows, _refused
    if _refused:
        return False
    try:
        library = unrealsdk.find_class(LIBRARY)
        if _rows is None:
            _rows = describe(library._find(FUNCTION))
        given = {"DamageCauser": character, "DamageInstigator": character, "DamageTarget": target,
                 "DamageOverride": float(amount)}
        if where is not None:
            given["TargetedHitInfo"] = where
        filled = arguments(_rows, given, {"DamageData": DAMAGE_DATA, "DamageTypeOverride": damage_type})
        getattr(library.ClassDefaultObject, FUNCTION)(**filled)
        return True
    except Exception as error:
        # Never tried again this session: a call the game refuses once would be refused at every hit.
        _refused = True
        report.error_once("damage", f"the beam deals no damage, the game refused the hit: {error!r}")
        return False
