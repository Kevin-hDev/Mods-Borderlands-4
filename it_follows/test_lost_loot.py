"""Tests the OPTIONS page's Lost Loot row (lost_loot.py, lost_loot_game.py): off at first, last on the OPTIONS page,
switched by the window; on, a refreshed PreAdd bonus of 400 minus the game's limit on the controller, once; off, its
opposite; a loaded save, a new player state without the bonus, gets it again when the game says the character is
ready, through a watch that waits for the player and gives up after WATCH_S; a limit that is no game's left alone; an
add the game refuses and that changed nothing not counted; MAX_ADDS at most; an add function not the trials' never
called, and no error ever escaping; the mod disabled, the hooks gone and the bonus taken back."""

import pathlib
import sys
import threading
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()
sys.modules["unrealsdk"].unreal.WrappedStruct = lambda fn, **fields: types.SimpleNamespace(_fn=fn, **fields)
# The trials' form, a name and the definition's type; the shared stub only knows a name.
sys.modules["unrealsdk"].unreal.FGbxDefPtr = lambda name, kind: types.SimpleNamespace(name=name, def_type=kind)

from it_follows import frame, lost_loot, lost_loot_game as game, menu, options, report  # noqa: E402
from it_follows.characters import game_thread  # noqa: E402

fails: list[str] = []
clock = [1000.0]
frame.time = types.SimpleNamespace(monotonic=lambda: clock[0])


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def prop(name: str, kind: str, enum: dict | None = None) -> types.SimpleNamespace:
    found = types.SimpleNamespace(Name=name, Class=types.SimpleNamespace(Name=kind))
    if enum is not None:
        found.Enum = types.SimpleNamespace(_as_py=lambda: types.SimpleNamespace(**enum))
    return found


def props() -> list:
    return [prop("attribute", "GbxDefPtrProperty"), prop("ContextSource", "ObjectProperty"),
            prop("ModifierType", "EnumProperty", {"ScaleAdd": 0, "PreAdd": 1}), prop("modifiervalue", "FloatProperty"),
            prop("bAutoRefresh", "BoolProperty"), prop("ModifierActionResult", "EnumProperty",
                                                       {"success": 0, "failure": 1}),
            prop("ReturnValue", "StructProperty")]


class Library:
    """The limit is the game's base plus the bonuses its player state holds; outcome and applies script the game."""

    def __init__(self) -> None:
        self.base, self.calls, self.outcome, self.applies, self.signature = 6.0, [], 0, True, props()
        self.bonuses: dict[str, list[float]] = {}

    def GetValueOfAttribute(self, name: str, context: object, default: float) -> float:
        if name != game.LIMIT or context is not state["pc"] or self.base is None:
            return default
        return self.base + sum(self.bonuses.get(context.PlayerState.Name, []))

    def AddModifierToGbxAttribute(self, params: types.SimpleNamespace) -> object:
        self.calls.append(params)
        if self.applies:
            self.bonuses.setdefault(params.ContextSource.PlayerState.Name, []).append(params.modifiervalue)
        return Ellipsis, types.SimpleNamespace(), self.outcome


def fresh() -> Library:
    library = Library()
    state["classes"][game.LIBRARY] = types.SimpleNamespace(
        ClassDefaultObject=library, _find=lambda name: types.SimpleNamespace(
            _properties=lambda: iter(library.signature)) if name == game.ADD else None)
    load("OakPlayerState_1")
    lost_loot._held.update(owner=None, added=0.0, adds=0)
    state["info"].clear()
    state["errors"].clear()
    # Each error is written once a launch (report.error_once); every case here is a launch of its own.
    report._errors.clear()
    return library


def load(name: str) -> None:
    state["pc"] = types.SimpleNamespace(OakCharacter=types.SimpleNamespace(Name="BP_Hunter"),
                                        PlayerState=types.SimpleNamespace(Name=name))


def limit() -> float | None:
    return game.limit(state["pc"])


def run_to(end: float) -> None:
    while clock[0] < end - 1e-9:
        clock[0] = round(clock[0] + 0.1, 6)
        beat = state["hooks"].get(lost_loot.WATCH_ID)
        if beat is not None:
            beat.fn(None)


def noted(event: str) -> list[str]:
    return [line for line in state["info"] if f'"event":"{event}"' in line]


check("off at first, on the OPTIONS page after the bar's rows", options.lost_loot.value is False
      and menu.display.children.index(options.lost_loot) == menu.display.children.index(options.bar_size) + 1)
check("the window's switch reaches the row's work", options.lost_loot.on_change_while_enabled is lost_loot.changed)
check("its English row says the new limit", "400" in options.lost_loot.display_name)

library = fresh()
lost_loot.changed(options.lost_loot, True)
call = library.calls[0]
check("on: a bonus of 400 minus the game's limit, the limit now 400", call.modifiervalue == 394.0 and limit() == 400.0)
check("a refreshed PreAdd on the controller's limit, the trials' way",
      call.ModifierType == 1 and call.bAutoRefresh is True and call.ContextSource is state["pc"]
      and call.attribute.name == "lost_loot_storage_maxsize" and call.attribute.def_type == "GbxAttributeDef"
      and call.ModifierActionResult == 1)
check("each add written to the log before the call, and its outcome after",
      len(noted("lost_loot_adding")) == 1 and '"outcome":0' in noted("lost_loot_added")[0])
lost_loot.changed(options.lost_loot, True)
check("on again: nothing more added", len(library.calls) == 1)
lost_loot.changed(options.lost_loot, False)
check("off: its opposite, the game's limit back", library.calls[-1].modifiervalue == -394.0 and limit() == 6.0)
lost_loot.changed(options.lost_loot, False)
check("off again: nothing more added", len(library.calls) == 2)

library = fresh()
library.base = 8.0
lost_loot.changed(options.lost_loot, True)
check("with SDU upgrades bought, still 400", library.calls[0].modifiervalue == 392.0 and limit() == 400.0)

library = fresh()
options.lost_loot.value = True
lost_loot.start()
run_to(clock[0] + 1.1)
check("enabled with the row on: the bonus added at the watch's first second, the watch then gone",
      limit() == 400.0 and lost_loot.WATCH_ID not in state["hooks"] and lost_loot.READY_ID in state["hooks"])
load("OakPlayerState_2")
state["pc"].OakCharacter = None
state["hooks"][lost_loot.READY_ID].fn(None)
run_to(clock[0] + 3.0)
check("a loaded save: the watch waits for the player", lost_loot.WATCH_ID in state["hooks"] and len(library.calls) == 1)
state["pc"].OakCharacter = types.SimpleNamespace(Name="BP_Hunter")
run_to(clock[0] + 1.1)
check("then adds the bonus to the new player state, from its own limit",
      limit() == 400.0 and library.calls[-1].modifiervalue == 394.0 and lost_loot.WATCH_ID not in state["hooks"])
load("OakPlayerState_3")
state["pc"].OakCharacter = None
state["hooks"][lost_loot.READY_ID].fn(None)
run_to(clock[0] + lost_loot.WATCH_S + 2.0)
check("a player never loaded: given up after WATCH_S, said in the log",
      lost_loot.WATCH_ID not in state["hooks"] and len(noted("lost_loot_gave_up")) == 1 and len(library.calls) == 2)
options.lost_loot.value = False
load("OakPlayerState_4")
state["hooks"][lost_loot.READY_ID].fn(None)
check("the row off: a loaded save is left as the game made it",
      lost_loot.WATCH_ID not in state["hooks"] and len(library.calls) == 2)
load("OakPlayerState_2")
lost_loot._held.update(owner="OakPlayerState_2", added=394.0)
lost_loot.stop()
check("the mod disabled: hooks gone, the bonus taken back",
      lost_loot.READY_ID not in state["hooks"] and limit() == 6.0 and library.calls[-1].modifiervalue == -394.0)

library = fresh()
library.base = 150.0
lost_loot.changed(options.lost_loot, True)
check("a limit that is no game's is left alone, and said", library.calls == [] and len(noted("lost_loot_left")) == 1)
library = fresh()
library.base = None
check("an unread limit: nothing added", lost_loot.apply(True) == "limit_unread" and library.calls == [])

library = fresh()
library.outcome, library.applies = 1, False
lost_loot.changed(options.lost_loot, True)
lost_loot.changed(options.lost_loot, True)
check("an add the game refuses and that changed nothing is not counted: tried again",
      len(library.calls) == 2 and lost_loot._held["added"] == 0.0)
library = fresh()
library.outcome = 1
lost_loot.changed(options.lost_loot, True)
lost_loot.changed(options.lost_loot, False)
check("one the game says refused but that changed the limit is counted, and taken back",
      [c.modifiervalue for c in library.calls] == [394.0, -394.0] and limit() == 6.0)

library = fresh()
for turn in range(lost_loot.MAX_ADDS + 6):
    lost_loot.changed(options.lost_loot, turn % 2 == 0)
check("MAX_ADDS adds at most in a launch", len(library.calls) == lost_loot.MAX_ADDS
      and lost_loot.apply(True) == "too_many_adds")

for label, signature in (("a missing parameter", props()[:-1]),
                         ("a parameter of another kind", props()[:3] + [prop("modifiervalue", "IntProperty")]
                          + props()[4:]),
                         ("a PreAdd that is no longer 1", props()[:2] + [prop("ModifierType", "EnumProperty",
                                                                              {"PreAdd": 2})] + props()[3:])):
    library = fresh()
    library.signature = signature
    outcome = lost_loot.apply(True)
    check(f"an add function with {label}: never called, no error escaping, said once",
          outcome == "failed" and library.calls == [] and len(state["errors"]) == 1 and limit() == 6.0)

for known in (None, threading.get_native_id()):
    lost_loot.stop()
    library = fresh()
    options.lost_loot.value = True
    game_thread._game[0] = known
    loader = threading.Thread(target=lost_loot.start)
    loader.start()
    loader.join(5)
    run_to(clock[0] + 1.1)
    check(f"started on the mod's load thread, the game's thread {'known' if known else 'unknown'} (trial 207): "
          "the watch adds the bonus on the game's", limit() == 400.0 and lost_loot.WATCH_ID not in state["hooks"])
lost_loot.stop()
options.lost_loot.value = False

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
