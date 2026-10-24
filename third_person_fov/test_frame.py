"""Only the played body clocks the camera, with one final update when gameplay ends; the other characters' updates
ask the game nothing while the played body is recent."""

import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
RUNTIME = HERE.parent.parent / "camera_runtime" / "source"
sys.path[:0] = [str(HERE), str(RUNTIME)]

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()
state["settings_exists"] = True

from third_person_fov import frame  # noqa: E402
from apex_camera_runtime.played_body import RECENT_NS  # noqa: E402


def thing(address, outer=None):
    return types.SimpleNamespace(_get_address=lambda: address, Outer=outer)


def player(live):
    """A controller whose character's mesh gives live["body"], read at each question."""
    mesh = types.SimpleNamespace(GetAnimInstance=lambda: live["body"])
    return types.SimpleNamespace(OakCharacter=types.SimpleNamespace(Mesh=mesh))


MESH, ENEMY_MESH, NEW_MESH = thing(100), thing(300), thing(500)
played, enemy, other = thing(10, MESH), thing(20, ENEMY_MESH), thing(30, ENEMY_MESH)
same_mesh, new_body = thing(11, MESH), thing(50, NEW_MESH)
live = {"body": played}
state["pc"] = player(live)

seen, questions = [], []
frame.camera.on_frame = lambda now, pc: seen.append((now, pc))


def counted_get_pc(**_kwargs):
    questions.append(1)
    return state["pc"]


frame.get_pc = counted_get_pc
failures = []


def check(name, condition):
    if not condition:
        failures.append(name)


T = 10_000_000_000
frame.on_frame(enemy, T + 1)
frame.on_frame(other, T + 2)
check("no body found yet: every update asks the game", len(questions) == 2 and seen == [])

frame.on_frame(played, T + 3)
check("the played body clocks the camera with the controller read", seen == [(T + 3, state["pc"])])

asked = len(questions)
frame.on_frame(enemy, T + 4)
frame.on_frame(other, T + 5)
check("other characters' updates ask nothing while the played body is recent", len(questions) == asked)
check("and never clock the camera", len(seen) == 1)

frame.on_frame(played, T + 6)
check("the played body's own update is checked against the game each time",
      len(questions) == asked + 1 and seen[-1] == (T + 6, state["pc"]))

live["body"] = same_mesh
frame.on_frame(same_mesh, T + 7)
check("a new body on the same mesh clocks the camera at once", seen[-1] == (T + 7, state["pc"]))
frame.on_frame(played, T + 8)
check("the old body no longer clocks it", seen[-1] == (T + 7, state["pc"]))

live["body"] = new_body
frame.on_frame(new_body, T + 9)
check("a body on a new character waits for the window", seen[-1] == (T + 7, state["pc"]))
frame.on_frame(new_body, T + 7 + RECENT_NS)
check("and is found once the window has passed", seen[-1] == (T + 7 + RECENT_NS, state["pc"]))

state["pc"] = None
count = len(seen)
frame.on_frame(other, T + 8 + RECENT_NS)
check("leaving the game waits for the window", len(seen) == count)
frame.on_frame(other, T + 7 + 2 * RECENT_NS)
check("then one final update, with no controller", seen[count:] == [(T + 7 + 2 * RECENT_NS, None)])
frame.on_frame(other, T + 8 + 2 * RECENT_NS)
check("only one final update", len(seen) == count + 1)

state["pc"] = player({"body": played})
frame.on_frame(played, T + 9 + 2 * RECENT_NS)
frame.reset()
asked = len(questions)
frame.on_frame(enemy, T + 10 + 2 * RECENT_NS)
check("reset forgets the played body", len(questions) == asked + 1)

frame.reset()
U = T + 100 * RECENT_NS
live = {"body": played}
state["pc"] = player(live)
frame.on_frame(played, U)
live["body"] = new_body
frame.on_frame(played, U + 1)
count = len(seen)
frame.on_frame(new_body, U + 2)
check("a remembered body found no longer played is forgotten: the new character's needs no window",
      seen[count:] == [(U + 2, state["pc"])])

frame.on_frame(new_body, U + 3)
state["pc"] = None
count = len(seen)
frame.on_frame(new_body, U + 4)
check("leaving the game seen on the played body's own update gives the final update at once",
      seen[count:] == [(U + 4, None)])
state["pc"] = player({"body": played})
frame.on_frame(played, U + 5)
check("and the next character's body is found without the window", seen[-1] == (U + 5, state["pc"]))

title = types.SimpleNamespace(OakCharacter=None)
frame.on_frame(played, U + 6)
state["pc"] = title
frame.on_frame(played, U + 7)
check("at the title screen the final update hands on the controller as the game gives it (review, 2026-10-24)",
      seen[-1] == (U + 7, title))

for name in failures:
    print("ECHEC:", name)
print("RESULTAT:", "TOUS LES TESTS PASSENT" if not failures else f"{len(failures)} ECHEC(S)")
raise SystemExit(1 if failures else 0)
