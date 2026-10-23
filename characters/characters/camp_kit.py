"""What the game gives It Follows for making its camps (camps.py): the game's definition type, the spawner class and the
statics, looked up at each ask, for a change of map may take them; and the game's enemy list, the kinds a camp can
make. Each lookup goes through called(call, make), which answers (True, what make gave) or (False, why it raised):
camps.Camps._called. The kit's three lookups are the SDK's own searches, no call to the game, and are not written to
the log, 1 494 lines of trial 33's run; the enemy list is a call to the game and is (audit of 16 October 2026).
"""

from itertools import islice
from typing import Any, Callable, NamedTuple

import unrealsdk

SPAWNER_CLASS = "OakSpawner"
DEF_TYPE = "/Script/GbxSpawn.GbxActorDef"
STATICS = "GameplayStatics"
DEFS_LIBRARY = "GbxActorDefBlueprintFunctionLibrary"
# The game's enemy list held 1 371 definitions on 2026-10-05: room to grow, never an endless read.
MAX_DEFINITIONS = 4096


class Kit(NamedTuple):
    """What the game gives for making camps, looked up at each ask: a change of map may take it."""
    kind: Any
    spawner_class: Any
    statics: Any


def look_up(called: Callable[..., tuple[bool, Any]]) -> Kit | str:
    """The kit, or why not: the call that raised, or that gave nothing."""
    found = []
    for call, make in ((f"find_object({DEF_TYPE})", lambda: unrealsdk.find_object("ScriptStruct", DEF_TYPE)),
                       (f"find_class({SPAWNER_CLASS})", lambda: unrealsdk.find_class(SPAWNER_CLASS)),
                       (f"find_class({STATICS})", lambda: unrealsdk.find_class(STATICS).ClassDefaultObject)):
        done, thing = called(call, make)
        if not done or thing is None:
            return thing if not done else f"{call}:none"
        found.append(thing)
    return Kit(*found)


def enemy_list(called: Callable[..., tuple[bool, Any]]) -> set[str] | str:
    """The definitions of the game's enemy list, at most MAX_DEFINITIONS of them, or why not."""
    done, names = called("GetEnemiesActorDefStrings", lambda: unrealsdk.find_class(
        DEFS_LIBRARY).ClassDefaultObject.GetEnemiesActorDefStrings())
    if not done or names is None:
        return names if not done else "GetEnemiesActorDefStrings:none"
    return {str(name) for name in islice(names, MAX_DEFINITIONS)}
