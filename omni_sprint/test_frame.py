"""Tests Omni Sprint's clock: only the played body's updates tick the camera runtime, one last tick when the player
leaves, its own copy of the open sprint ticked beside it, and an error written once while the game goes on."""

import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


state = sdk_stubs.install()

from omni_sprint import camera, frame, report, sprint_fallback  # noqa: E402

camera_frames: list[int] = []
fallback_ticks: list[object] = []
camera.on_frame = lambda now: camera_frames.append(now)
sprint_fallback.tick = lambda pc, now: fallback_ticks.append(pc)

frame.reset()
frame.tick(object(), None, None, None)
check("without a player nothing is ticked", camera_frames == [] and fallback_ticks == [])
state["pc"] = sdk_stubs.player(sdk_stubs.BASE + 0x1000)
frame.tick(types.SimpleNamespace(_get_address=lambda: 1), None, None, None)
check("an enemy's update ticks nothing", camera_frames == [])
frame.tick(sdk_stubs.body(state["pc"]), None, None, None)
check("the played body's update ticks the camera runtime, then the open sprint's own copy, with the player",
      len(camera_frames) == 1 and fallback_ticks == [state["pc"]])
state["pc"] = None
frame.tick(object(), None, None, None)
frame.tick(object(), None, None, None)
check("the player gone, one last tick lets the runtime give everything back",
      len(camera_frames) == 2 and fallback_ticks[-1] is None)

state["pc"] = sdk_stubs.player(sdk_stubs.BASE + 0x1000)
camera.on_frame = lambda now: 1 / 0
frame.tick(sdk_stubs.body(state["pc"]), None, None, None)
frame.tick(sdk_stubs.body(state["pc"]), None, None, None)
check("a camera error is written once and the open sprint's copy still runs",
      len([line for line in state["errors"] if "camera check was skipped" in line]) == 1 and len(fallback_ticks) == 4)
camera.on_frame = lambda now: camera_frames.append(now)
stops: list[bool] = []
sprint_fallback.tick = lambda pc, now: 1 / 0
sprint_fallback.stop = lambda: stops.append(True)
frame.tick(sdk_stubs.body(state["pc"]), None, None, None)
check("an error in the open sprint's copy is written once and that copy stops",
      stops == [True] and any("own copy stopped" in line for line in state["errors"]))


class Broken:
    @property
    def OakCharacter(self) -> object:
        raise RuntimeError("controller gone")


state["pc"] = Broken()
report.reset()
frame.tick(object(), None, None, None)
frame.tick(object(), None, None, None)
check("an unreadable player is written once and the game goes on",
      len([line for line in state["errors"] if "a frame was skipped" in line]) == 1)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
