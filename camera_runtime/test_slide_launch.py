"""Tests the slide launch: slides follow the run while asked, twice a second, the game's direction given back only over
what the unit wrote, an asset not loaded left alone, and Apex Movement's own momentum slides never undone by it."""

import enum
import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from apex_camera_runtime.slide_launch import CHECK_NS, SLIDE_ASSET, SlideLaunch  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


Direction = enum.Enum("ERelativeDirection", ["ParentAimDirection2D", "ParentVelocity2D"])
AIM, MOMENTUM = Direction.ParentAimDirection2D, Direction.ParentVelocity2D


class Asset:
    """Move_Slide: its LaunchDirection handed out as a copy, as the SDK may, so only a whole assignment counts."""

    def __init__(self) -> None:
        self.held = AIM

    @property
    def LaunchDirection(self) -> types.SimpleNamespace:
        return types.SimpleNamespace(RelativeDirection=self.held)

    @LaunchDirection.setter
    def LaunchDirection(self, launch: types.SimpleNamespace) -> None:
        self.held = launch.RelativeDirection


asset = Asset()
loaded = [True]
asked: list[tuple] = []


def find(*name):
    asked.append(name)
    if not loaded[0]:
        raise ValueError("not found")
    return asset


lines: list[str] = []
unit = SlideLaunch(find, lines.append)

unit.update(False, 0)
check("not asked, nothing written", asset.held == AIM and lines == [])
unit.update(True, 1)
check("still within the half second: nothing read", asset.held == AIM and asked == [])
unit.update(True, CHECK_NS)
check("asked: the slides follow the run, written whole, said", asset.held == MOMENTUM and asked == [SLIDE_ASSET]
      and lines[-1] == "slides follow the run (was ParentAimDirection2D)")
unit.update(True, 2 * CHECK_NS)
check("already following the run: nothing written again", len(lines) == 1)
unit.update(False, 3 * CHECK_NS)
check("no longer asked: the game's direction back, said", asset.held == AIM
      and lines[-1] == "slides start toward the aim again (ParentAimDirection2D)")
unit.update(False, 4 * CHECK_NS)
check("given back twice, the second does nothing", len(lines) == 2)

asset.held = MOMENTUM
unit.update(True, 5 * CHECK_NS)
unit.update(False, 6 * CHECK_NS)
check("Apex Movement's momentum slides found in place: never given back by this unit", asset.held == MOMENTUM
      and len(lines) == 2)
asset.held = AIM
unit.update(True, 7 * CHECK_NS)
asset.held = AIM
unit.update(True, 8 * CHECK_NS)
check("put back by another hand while asked: written again at the next check", asset.held == MOMENTUM)
asset.held = AIM
said = len(lines)
unit.next_ns = 0
unit.update(False, 8 * CHECK_NS)
check("already back to the aim when no longer asked: nothing written, nothing said", len(lines) == said)
unit.next_ns = 0
unit.update(True, 8 * CHECK_NS)

loaded[0] = False
said = len(lines)
unit.update(False, 9 * CHECK_NS)
check("unloaded when given back: nothing to write, the next load has the game's value", len(lines) == said)
loaded[0] = True
asset.held = AIM
unit.update(False, 10 * CHECK_NS)
check("and nothing is given back later over the game's own value", asset.held == AIM)
loaded[0] = False
unit.update(True, 11 * CHECK_NS)
check("asked while unloaded: waits for the next load", asset.held == AIM)
loaded[0] = True
unit.update(True, 12 * CHECK_NS)
check("loaded again: written", asset.held == MOMENTUM)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
