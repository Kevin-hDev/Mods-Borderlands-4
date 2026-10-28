"""Tests the OPTIONS page's saturated colours (colours.py, colours_game.py): a switch off at first and a profile among
three, Profile 2 at first, after the 16:10 row; on, the time of day's saturation and every volume's that sets one
multiplied by the profile's factor, the game's own kept; a profile changed raising from the game's own again; a pass
each second leaving what holds, raising again what the game reset or changed, and what streams in; off, or the mod
disabled, the game's own given back, a value the game changed since left as it is; a profile chosen while off
writing nothing; the game's search only, never find_all; a write that does not hold, a world not loaded, a path
unread, a failure never escaping; the lists and the log lines bounded; the row's words in each language."""

import math
import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

from it_follows import colours, colours_game as game, frame, menu, options, panel_fr, panel_zh, report  # noqa: E402
from it_follows.characters import animation_hook  # noqa: E402

fails: list[str] = []
clock = [1000.0]
frame.time = types.SimpleNamespace(monotonic=lambda: clock[0])


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


class Settings:
    """A PostProcessSettings: whether it sets the saturation, and the saturation; a stubborn one keeps its own."""

    def __init__(self, value: float, on: bool, stubborn: bool) -> None:
        self.bOverride_ColorSaturation, self.stubborn, self.writes = on, stubborn, 0
        self._saturation = types.SimpleNamespace(X=value, Y=value, Z=value, W=1.0)

    @property
    def ColorSaturation(self) -> object:
        return self._saturation

    @ColorSaturation.setter
    def ColorSaturation(self, vector: object) -> None:
        self.writes += 1
        if not self.stubborn:
            self._saturation = vector


class Item:
    """A post process component or volume, named by its path."""

    def __init__(self, path: str, value: float = 1.0, on: bool = True, stubborn: bool = False) -> None:
        self.path, self.Settings = path, Settings(value, on, stubborn)

    def _path_name(self) -> str:
        if self.path is None:
            raise RuntimeError("no path")
        return self.path

    def set(self, value: float) -> None:
        self.Settings._saturation = types.SimpleNamespace(X=value, Y=value, Z=value, W=1.0)

    def value(self) -> float:
        return round(self.Settings.ColorSaturation.X, 4)


world: dict = {"WorldTimeOfDayActor": [], "PostProcessVolume": [], "broken": False, "searches": 0}


def search(WorldContextObject: object, ActorClass: object, OutActors: list) -> tuple:
    if world["broken"]:
        raise RuntimeError("search failed")
    world["searches"] += 1
    return None, list(world[ActorClass.Name])


state["classes"]["GameplayStatics"] = types.SimpleNamespace(
    ClassDefaultObject=types.SimpleNamespace(GetAllActorsOfClass=search))
for name in ("WorldTimeOfDayActor", "PostProcessVolume"):
    state["classes"][name] = types.SimpleNamespace(Name=name)


def fresh(volumes: int = 1) -> tuple:
    """A world: the time of day's post process, volumes that set the saturation, one that does not."""
    colours.stop()
    colours._held.clear()
    colours._state["notes"] = 0
    options.colours.value, options.colour_profile.value = False, options.DEFAULT_COLOUR_PROFILE
    sky = Item("/Game/Map.Map:PersistentLevel.WorldTimeOfDayActor_1.PostProcessComponent")
    near = [Item(f"/Game/Map.Map:PersistentLevel.PostProcessVolume_{n}") for n in range(volumes)]
    plain = Item("/Game/Map.Map:PersistentLevel.PostProcessVolume_Plain", on=False)
    world.update(WorldTimeOfDayActor=[types.SimpleNamespace(PostProcessComponent=sky)],
                 PostProcessVolume=[*near, plain], broken=False, searches=0)
    state["pc"] = types.SimpleNamespace(Name="OakPlayerController_0")
    state["all"].clear()
    state["info"].clear()
    state["errors"].clear()
    report._errors.clear()
    return sky, near[0] if near else None, plain


def noted(event: str) -> int:
    return sum(f'"event":"{event}"' in line for line in state["info"])


def watching() -> bool:
    """Whether the watch's beat is set on the package's one hook on the animation update."""
    return colours.WATCH_ID in animation_hook.beats()


def run_to(end: float) -> None:
    while clock[0] < end - 1e-9:
        clock[0] = round(clock[0] + 0.1, 6)
        beat = animation_hook.beats().get(colours.WATCH_ID)
        if beat is not None:
            beat(None)


check("off at first, Profile 2 at first, after the 16:10 row on the OPTIONS page",
      options.colours.value is False and options.colours.args == () and options.colour_profile.value == "Profile 2"
      and menu.display.children[-2:] == [options.colours, options.colour_profile]
      and menu.display.children.index(options.colours) == menu.display.children.index(options.resolution) + 1)
check("decision 149's three profiles: the photo mode's 140, 170 and 200",
      options.COLOUR_PROFILES == {"Profile 1": 1.4, "Profile 2": 1.7, "Profile 3": 2.0}
      and options.colour_profile.choices == list(options.COLOUR_PROFILES))
check("the window's rows reach the colours' work", options.colours.on_change_while_enabled is colours.switched
      and options.colour_profile.on_change_while_enabled is colours.chosen)
check("a factor for each profile, none when off, the default for a profile unknown",
      colours.factor(False, "Profile 3") is None and colours.factor(True, "Profile 1") == 1.4
      and colours.factor(True, "Profile 9") == 1.7)
check("the game's own times the factor, its W kept, within the engine's bounds",
      colours.scaled((1.0, 0.5, 3.0, 0.7), 2.0) == (2.0, 1.0, 4.0, 0.7))

sky, near, plain = fresh()
colours.switched(options.colours, True)
check("on: the time of day and the volume that sets the saturation times 1.7, the other left, said once",
      sky.value() == 1.7 and near.value() == 1.7 and plain.Settings.writes == 0 and noted("colours_written") == 1
      and watching() and world["searches"] == 2)
options.colours.value = True
colours.chosen(options.colour_profile, "Profile 3")
check("another profile: raised from the game's own, not from what was written", sky.value() == 2.0
      and near.value() == 2.0)
options.colour_profile.value = "Profile 3"
writes = sky.Settings.writes
run_to(clock[0] + 3.0)
check("the passes leave what holds", sky.Settings.writes == writes and noted("colours_written") == 2)
sky.set(1.0)
run_to(clock[0] + 1.0)
check("the game reset it: raised again", sky.value() == 2.0)
sky.set(0.8)
run_to(clock[0] + 1.0)
check("the game changed it: its new value taken as its own", sky.value() == 1.6)
streamed = Item("/Game/Map.Map:Streamed.PostProcessVolume_9", value=1.2)
world["PostProcessVolume"] = [near, plain, streamed]
run_to(clock[0] + 1.0)
check("a volume streamed in is raised", streamed.value() == 2.4 and len(colours._held) == 3)
world["PostProcessVolume"] = [plain, streamed]
run_to(clock[0] + 1.0)
check("one streamed out is forgotten", len(colours._held) == 2)
world["PostProcessVolume"] = [near, plain, streamed]
streamed.set(1.5)
colours.switched(options.colours, False)
check("off: the game's own back, a value the game changed since left as it is, the pass stopped",
      sky.value() == 0.8 and near.value() == 2.0 and streamed.value() == 1.5 and colours._held == {}
      and not watching())

sky, near, plain = fresh()
colours.switched(options.colours, False)
check("off with nothing held: nothing written", sky.Settings.writes == 0 and near.Settings.writes == 0)
colours.chosen(options.colour_profile, "Profile 1")
check("a profile chosen with the switch off: nothing written, no pass", sky.Settings.writes == 0
      and not watching())
options.colours.value = True
colours.chosen(options.colour_profile, "Profile 9")
check("a profile unknown, the switch on: the default's factor", sky.value() == 1.7)
colours.stop()
check("the mod disabled: the game's own back, no pass", sky.value() == 1.0 and not watching())
colours.start()
check("the mod enabled with the switch on: raised at once, then each second", sky.value() == 1.7
      and watching())

sky, near, plain = fresh()
stubborn = Item("/Game/Map.Map:PersistentLevel.PostProcessVolume_Stubborn", stubborn=True)
world["PostProcessVolume"] = [stubborn]
colours.apply(1.7)
check("a write that does not hold is counted, not kept", stubborn.Settings.writes == 1
      and list(colours._held) == [sky.path] and '"refused":1' in state["info"][-1])
sky, near, plain = fresh()
world["broken"] = True
state["all"]["PostProcessVolume"] = [near]
check("the game's search failing: nothing found, find_all never used, said once",
      colours.apply(1.7) == "no_search" and colours.apply(1.7) == "no_search" and near.Settings.writes == 0
      and len(state["errors"]) == 1)
sky, near, plain = fresh()
state["pc"] = None
check("no world loaded: nothing done", colours.apply(1.7) == "no_world" and sky.Settings.writes == 0)
sky, near, plain = fresh()
near.path = None
colours.apply(1.7)
check("a path unread: left alone", near.Settings.writes == 0 and sky.value() == 1.7)
sky, near, plain = fresh()
sky.set(math.nan)
check("a saturation that is no number: left alone, never written as 0, said once, the others raised",
      colours.apply(1.7) == "raised" and colours.apply(1.7) == "raised" and sky.Settings.writes == 0
      and len(state["errors"]) == 1 and near.value() == 1.7)
check("only saturations within the engine's bounds", game.valid((1.0, 1.0, 1.0, 1.0))
      and not game.valid((4.5, 1.0, 1.0, 1.0)) and not game.valid((1, 1.0, 1.0, 1.0)) and not game.valid((1.0,)))

sky, near, plain = fresh(volumes=game.MAX_FOUND + 5)
check("what is found bounded", len(game.found(state["pc"])) == game.MAX_FOUND)
late = Item("/Game/Map.Map:PersistentLevel.PostProcessVolume_Late")
world["PostProcessVolume"] = [Item(f"/Game/Plain_{n}", on=False) for n in range(game.MAX_FOUND)] + [late]
check("the search read no further than MAX_FOUND actors a class", late not in game.found(state["pc"]))
try:
    game.write(sky, (4.5, 1.0, 1.0, 1.0))
    refused = False
except ValueError:
    refused = True
check("a saturation out of the engine's bounds is refused before anything is set", refused
      and sky.Settings.writes == 0)
sky, near, plain = fresh()
for n in range(colours.MAX_NOTES + 5):
    sky.set(1.0 + n * 0.01)
    colours.apply(1.7)
check("the lines a launch bounded, the last said so", noted("colours_written") == colours.MAX_NOTES
      and '"last":true' in state["info"][-1])

check("the row's name and one help sentence (Kevin), the profiles as the game names a preset",
      (options.colours.display_name, options.colours.description)
      == ("Color profile", "Brighter colors over the whole game.")
      and panel_fr.OPTIONS["saturated_colours"] == ("Profil de couleurs", "Des couleurs plus vives dans tout le jeu.")
      and panel_fr.CHOICES["colour_profile:Profile 2"] == "Profil 2"
      and panel_zh.OPTIONS["saturated_colours"] == ("颜色预设", "整个游戏的颜色更鲜艳。")
      and panel_zh.CHOICES["colour_profile:Profile 3"] == "预设 3")
colours.stop()

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
