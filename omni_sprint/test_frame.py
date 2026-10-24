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
camera.on_frame = lambda now, pc: camera_frames.append(now)
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
camera.on_frame = lambda now, pc: 1 / 0
frame.tick(sdk_stubs.body(state["pc"]), None, None, None)
frame.tick(sdk_stubs.body(state["pc"]), None, None, None)
check("a camera error is written once and the open sprint's copy still runs",
      len([line for line in state["errors"] if "camera check was skipped" in line]) == 1 and len(fallback_ticks) == 4)
camera.on_frame = lambda now, pc: camera_frames.append(now)
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

# The played body remembered (apex_camera_runtime/played_body.py): the other characters' updates ask the game nothing
# while it is recent. The clock is the test's from here.
from apex_camera_runtime.played_body import RECENT_NS  # noqa: E402

clock = [10_000_000_000]
frame.time = types.SimpleNamespace(perf_counter_ns=lambda: clock[0])
questions: list[int] = []


def counted_get_pc(**_kwargs: object) -> object:
    questions.append(1)
    return state["pc"]


def thing(address: int, outer: object = None) -> object:
    return types.SimpleNamespace(_get_address=lambda: address, Outer=outer)


def player_of(live: dict) -> object:
    """A controller whose character's mesh gives live["body"], read at each question."""
    mesh = types.SimpleNamespace(GetAnimInstance=lambda: live["body"])
    return types.SimpleNamespace(OakCharacter=types.SimpleNamespace(Mesh=mesh))


def at(obj: object, now: int) -> None:
    clock[0] = now
    frame.tick(obj, None, None, None)


frame.get_pc = counted_get_pc
seen: list[tuple] = []
camera.on_frame = lambda now, pc: seen.append((now, pc))
fallback_ticks.clear()
sprint_fallback.tick = lambda pc, now: fallback_ticks.append(pc)
report.reset()
frame.reset()
MESH, ENEMY_MESH, NEW_MESH = thing(0x100), thing(0x300), thing(0x500)
played, enemy, same_mesh, new_body = thing(0x10, MESH), thing(0x20, ENEMY_MESH), thing(0x11, MESH), thing(0x50, NEW_MESH)
live = {"body": played}
state["pc"] = player_of(live)
T = clock[0]

at(enemy, T + 1)
at(played, T + 2)
check("the played body ticks the camera with the controller the game gave, and the open sprint's copy",
      seen == [(T + 2, state["pc"])] and fallback_ticks == [state["pc"]])
asked = len(questions)
at(enemy, T + 3)
at(enemy, T + 4)
check("other characters' updates ask the game nothing while the played body is recent",
      len(questions) == asked and len(seen) == 1)
at(played, T + 5)
check("the played body's own update is checked against the game each time",
      len(questions) == asked + 1 and seen[-1] == (T + 5, state["pc"]))
live["body"] = same_mesh
at(same_mesh, T + 6)
check("a new body on the same mesh ticks at once", seen[-1] == (T + 6, state["pc"]))
live["body"] = new_body
at(new_body, T + 7)
check("a body on a new character waits for the window", seen[-1] == (T + 6, state["pc"]))
at(new_body, T + 6 + RECENT_NS)
check("and is found once the window has passed", seen[-1] == (T + 6 + RECENT_NS, state["pc"]))

title = types.SimpleNamespace(OakCharacter=None)
state["pc"] = title
count, fallen = len(seen), len(fallback_ticks)
at(enemy, T + 7 + RECENT_NS)
check("leaving the game waits for the window", len(seen) == count)
at(enemy, T + 6 + 2 * RECENT_NS)
check("then one last tick: the camera gets the controller as the game gives it, the open sprint's copy none",
      seen[count:] == [(T + 6 + 2 * RECENT_NS, title)] and fallback_ticks[fallen:] == [None])
at(enemy, T + 7 + 2 * RECENT_NS)
check("only one last tick", len(seen) == count + 1)

state["pc"] = player_of({"body": played})
at(played, T + 8 + 2 * RECENT_NS)
frame.reset()
asked = len(questions)
at(enemy, T + 9 + 2 * RECENT_NS)
check("reset forgets the played body", len(questions) == asked + 1)

frame.reset()
U = T + 100 * RECENT_NS
live = {"body": played}
state["pc"] = player_of(live)
at(played, U)
live["body"] = new_body
at(played, U + 1)
count = len(seen)
at(new_body, U + 2)
check("a remembered body found no longer played is forgotten: the new character's needs no window",
      seen[count:] == [(U + 2, state["pc"])])
at(new_body, U + 3)
state["pc"] = None
count = len(seen)
at(new_body, U + 4)
check("leaving seen on the played body's own update gives the last tick at once", seen[count:] == [(U + 4, None)])
state["pc"] = player_of({"body": played})
at(played, U + 5)
check("and the next character's body is found without the window", seen[-1] == (U + 5, state["pc"]))

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
