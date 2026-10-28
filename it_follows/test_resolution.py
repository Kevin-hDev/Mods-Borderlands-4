"""Tests the OPTIONS page's 16:10 resolution row (resolution.py, resolution_game.py): a switch, off at first, after
the Lost Loot on the OPTIONS page, under a name trial 113's saved "Off" cannot switch on; on, the 16:10 of the
screen's height in the game's Fullscreen, never saved, the player's own resolution and mode kept the first time and
given back at Off and when the mod is disabled, even after a relaunch; a screen narrower than 16:10 left as it is; the
row applied again at launch; a failure never escaping; its name in each language."""

import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

from it_follows import menu, options, panel_fr, panel_zh, report, resolution  # noqa: E402
from it_follows import resolution_game as game  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


class Settings:
    """The engine's GameUserSettings: what is set and applied; SaveSettings counted, never expected."""

    def __init__(self, screen: tuple[int, int]) -> None:
        self.resolution, self.mode, self.screen = (2048, 1152), 2, screen
        self.applied: list[tuple] = []
        self.saved, self.broken = 0, False

    def GetScreenResolution(self) -> object:
        return types.SimpleNamespace(X=self.resolution[0], Y=self.resolution[1])

    def GetDesktopResolution(self) -> object:
        if self.broken:
            raise RuntimeError("no screen")
        return types.SimpleNamespace(X=self.screen[0], Y=self.screen[1])

    def GetFullscreenMode(self) -> int:
        return self.mode

    def SetScreenResolution(self, point: object) -> None:
        self.resolution = (point.X, point.Y)

    def SetFullscreenMode(self, mode: int) -> None:
        self.mode = mode

    def ApplyResolutionSettings(self, check_command_line: bool) -> None:
        self.applied.append((*self.resolution, self.mode, check_command_line))

    def SaveSettings(self) -> None:
        self.saved += 1


def fresh(screen: tuple[int, int] = (2560, 1440), own: str = "") -> Settings:
    settings = Settings(screen)
    state["classes"]["GameUserSettings"] = types.SimpleNamespace(
        ClassDefaultObject=types.SimpleNamespace(GetGameUserSettings=lambda: settings))
    options.resolution_own.value = own
    options.resolution.value = False
    state["info"].clear()
    state["errors"].clear()
    report._errors.clear()
    return settings


def noted(event: str) -> int:
    return sum(f'"event":"{event}"' in line for line in state["info"])


check("off at first, on the OPTIONS page after the Lost Loot, a switch without arrows",
      options.resolution.value is False and options.resolution.default_value is False and options.resolution.args == ()
      and menu.display.children.index(options.resolution) == menu.display.children.index(options.lost_loot) + 1
      and "stretch_1610" not in menu.ARROWS
      and options.resolution_own in options.ALL and options.resolution_own.is_hidden is True)
check("a name of its own: trial 113's saved Off is not read by the switch",
      options.resolution.identifier == "stretch_1610")
check("the window's switch reaches the row's work", options.resolution.on_change_while_enabled is resolution.changed)

check("the 16:10 of the screen's height: 2304x1440 on 1440p, 1728x1080 on 1080p",
      resolution.sixteen_ten((2560, 1440)) == (2304, 1440) and resolution.sixteen_ten((1920, 1080)) == (1728, 1080))
check("a width that would be odd is rounded to an even one", resolution.sixteen_ten((1366, 768)) == (1228, 768)
      and resolution.sixteen_ten((1700, 1001)) == (1602, 1001))
check("a 16:10 screen keeps its own size, an ultrawide one is stretched",
      resolution.sixteen_ten((1920, 1200)) == (1920, 1200) and resolution.sixteen_ten((3440, 1440)) == (2304, 1440))
check("a screen narrower than 16:10 has none", resolution.sixteen_ten((1600, 1200)) is None
      and resolution.sixteen_ten((1280, 1024)) is None)

settings = fresh()
resolution.changed(options.resolution, True)
check("on: the screen's 16:10 applied in the game's Fullscreen, the player's own kept, nothing saved",
      settings.applied == [(2304, 1440, 0, False)] and options.resolution_own.value == "2048x1152:2"
      and settings.saved == 0 and noted("resolution_applying") == 1)
resolution.changed(options.resolution, True)
check("on again: applied, the player's own still the first one kept",
      settings.applied[-1] == (2304, 1440, 0, False) and options.resolution_own.value == "2048x1152:2")
resolution.changed(options.resolution, False)
check("off: the player's own resolution and display mode back, no longer kept",
      settings.applied[-1] == (2048, 1152, 2, False) and options.resolution_own.value == "" and settings.saved == 0)
check("off again: nothing to give back", resolution.apply(False) == "nothing_held" and len(settings.applied) == 3)

settings = fresh((1920, 1080))
resolution.apply(True)
check("a 1080p screen: 1728x1080", settings.applied == [(1728, 1080, 0, False)])
settings = fresh((1600, 1200))
check("a 4:3 screen is left as it is, and said", resolution.apply(True) == "screen_narrow"
      and settings.applied == [] and options.resolution_own.value == "" and noted("resolution_screen_narrow") == 1)
settings = fresh()
check("a value that is no switch is off", resolution.apply("Off") == "nothing_held" and settings.applied == []
      and resolution.apply(1) == "nothing_held")

settings = fresh(own="2560x1440:0")
settings.resolution, settings.mode = (2304, 1440), 0
options.resolution.value = True
resolution.start()
check("at launch: the row applied again, the player's own kept from before",
      settings.applied == [(2304, 1440, 0, False)] and options.resolution_own.value == "2560x1440:0")
resolution.stop()
check("the mod disabled: the player's own back", settings.applied[-1] == (2560, 1440, 0, False)
      and options.resolution_own.value == "")
settings = fresh()
resolution.start()
check("at launch with the row off: nothing touched", settings.applied == [])
settings = fresh(own="2560x1440:1")
resolution.start()
check("at launch with the row off and the player's own still kept: given back",
      settings.applied == [(2560, 1440, 1, False)] and options.resolution_own.value == "")
settings = fresh(own="1920x1080:7")
check("a kept value with a mode the engine has not is none", resolution.apply(False) == "nothing_held"
      and settings.applied == [] and state["errors"] == [])

settings = fresh(own="garbage")
check("a hand-edited own value is none: off gives nothing back", resolution.apply(False) == "nothing_held"
      and settings.applied == [])
resolution.apply(True)
check("and on keeps the player's own anew", options.resolution_own.value == "2048x1152:2")

settings = fresh(own="9999x9999:1")
check("an own value out of bounds is refused, not applied, said once",
      resolution.apply(False) == "failed" and settings.applied == [] and len(state["errors"]) == 1
      and options.resolution_own.value == "9999x9999:1")
settings = fresh()
settings.broken = True
check("a screen unread: nothing applied, no error escaping", resolution.apply(True) == "failed"
      and settings.applied == [] and options.resolution_own.value == "")
settings = fresh()
state["classes"]["GameUserSettings"] = types.SimpleNamespace(ClassDefaultObject=types.SimpleNamespace())
check("settings unreachable: no error escaping", resolution.apply(True) == "failed")
check("valid sizes and modes only", game.valid(1728, 1080, 0) and not game.valid(1728, 1080, 3)
      and not game.valid(100, 1080, 0) and not game.valid(1728.0, 1080, 0))

check("its name and help in French and Chinese",
      panel_fr.OPTIONS["stretch_1610"][0] == "Résolution 16:10" and "2304×1440" in panel_fr.OPTIONS["stretch_1610"][1]
      and panel_zh.OPTIONS["stretch_1610"][0] == "16：10 分辨率" and "2304×1440" in panel_zh.OPTIONS["stretch_1610"][1])

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
