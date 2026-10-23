"""Tests the team's wardrobe (companions/wardrobe.py, decision 65): its own hook on the camera's modifiers' update; a
hunter handed to it waits for that update, is started there and said, kept only when his upper body was given;
taken further at a later update, never in the one that started him; said and forgotten when done; a step that fails
gives him up; an update from another thread than the game's does nothing; those the update never comes for within
START_WAIT_S said and forgotten, the others kept; MOST of each kept, the latest; the stop gives up those being
dressed and removes the hook, even when giving one up fails."""

import json
import pathlib
import sys
import threading

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

import companion_fixture as fake  # noqa: E402
from it_follows.companions import team as team_module, wardrobe  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def notes(event: str) -> list[dict]:
    found = [json.loads(text.removeprefix("[It Follows] ")) for text in state["info"]
             if text.startswith("[It Follows] {")]
    return [line for line in found if line["event"] == event]


class Dressing:
    """dress.Dressing as the wardrobe drives it: start() answers `start` (or raises it), step() answers the next of
    `steps` (or raises it); give_up() counted, or raises when told."""

    def __init__(self, start: object = None, steps: list | None = None, give_up_fails: bool = False) -> None:
        self.start_answer = {"done": "swapped", "hunter": "Rafa"} if start is None else start
        self.steps_left = list(steps if steps is not None else [None, {"done": "worn", "hunter": "Rafa"}])
        self.started = self.stepped = self.gave_up = 0
        self.give_up_fails = give_up_fails

    def start(self) -> object:
        self.started += 1
        if isinstance(self.start_answer, Exception):
            raise self.start_answer
        return self.start_answer

    def step(self) -> object:
        self.stepped += 1
        answer = self.steps_left.pop(0)
        if isinstance(answer, Exception):
            raise answer
        return answer

    def give_up(self) -> None:
        self.gave_up += 1
        if self.give_up_fails:
            raise RuntimeError("cannot show him")


def camera() -> None:
    state["hooks"][wardrobe.IDENTIFIER].fn()


check("its own hook, on the camera's modifiers' update, apart from the team's", wardrobe.HOOK
      == "/Script/Engine.CameraModifier:BlueprintModifyCamera" and wardrobe.IDENTIFIER != team_module.IDENTIFIER)
clock = fake.Clock()
clock.now = 100.0
room = wardrobe.Wardrobe(clock, 3)
room.start()
check("hooked as the team starts", wardrobe.IDENTIFIER in state["hooks"]
      and state["hooks"][wardrobe.IDENTIFIER].enabled)
rafa = Dressing()
check("a hunter handed to it: waits for the camera's update, nothing done yet", room.add("Lemmy_1", "Rafa", rafa)
      == "queued" and rafa.started == 0 and len(room.waiting) == 1)
camera()
check("started at the update, said, kept to be finished, not taken further in that update", rafa.started == 1
      and rafa.stepped == 0 and notes("companion_dressing")[-1] == {
          "event": "companion_dressing", "run": 0, "character": "Lemmy_1", "companion": "Rafa", "done": "swapped",
          "hunter": "Rafa"} and len(room.dressing) == 1 and room.waiting == [])
camera()
check("not drawn yet: kept", rafa.stepped == 1 and len(room.dressing) == 1)
camera()
check("done: said, forgotten", rafa.stepped == 2 and room.dressing == [] and notes("companion_dressed")[-1] == {
      "event": "companion_dressed", "run": 0, "character": "Lemmy_1", "companion": "Rafa", "done": "worn",
      "hunter": "Rafa"})
for name, start, done in [("Vex", {"done": "not_loaded", "parts": ["X"]}, "not_loaded"),
                          ("Amon", ZeroDivisionError("no"), "failed:ZeroDivisionError:no")]:
    other = Dressing(start)
    room.add(f"Lemmy_{name}", name, other)
    camera()
    check(f"a start that gives {done}: said, not kept", notes("companion_dressing")[-1]["done"] == done
          and notes("companion_dressing")[-1]["companion"] == name and room.dressing == [])
broken = Dressing(steps=[RuntimeError("bad")])
room.add("Lemmy_2", "Harlowe", broken)
camera()
camera()
check("a step that fails: given up (shown again), said, forgotten", broken.gave_up == 1 and room.dressing == []
      and notes("companion_dressed")[-1]["done"] == "failed:RuntimeError:bad")

late = Dressing()
room.add("Lemmy_3", "C4SH", late)
worker = threading.Thread(target=camera)
worker.start()
worker.join(5)
check("an update from another thread than the game's: nothing started", late.started == 0 and len(room.waiting) == 1)
camera()
check("the next on the game's thread: started", late.started == 1)
room.dressing = []

clock.now = 200.0
room.add("Lemmy_4", "Vex", Dressing())
clock.now = 200.0 + wardrobe.START_WAIT_S - 0.5
room.add("Lemmy_5", "Amon", Dressing())
clock.now = 200.0 + wardrobe.START_WAIT_S + 0.25
room.overdue()
check("the camera's update never came within START_WAIT_S: said, forgotten; the later one kept", [
      held[0] for held in room.waiting] == ["Lemmy_5"] and notes("companion_dressing")[-1] == {
      "event": "companion_dressing", "run": 0, "character": "Lemmy_4", "companion": "Vex",
      "done": "camera_never_came", "waited_s": 5.25})
room.waiting = []
for number in range(5):
    room.add(f"Lemmy_{10 + number}", "Rafa", Dressing())
check("waiting: most kept, the latest", [held[0] for held in room.waiting] == ["Lemmy_12", "Lemmy_13", "Lemmy_14"])
camera()
room.add("Lemmy_15", "Rafa", Dressing())
room.add("Lemmy_16", "Rafa", Dressing())
camera()
check("being dressed: most kept, the latest, over two updates", [held[0] for held in room.dressing] == [
      "Lemmy_14", "Lemmy_15", "Lemmy_16"])
held = [one[2] for one in room.dressing]
held[0].give_up_fails = True
try:
    room.stop()
    raised = False
except RuntimeError:
    raised = True
check("the stop: each being dressed given up, a give-up that fails left to its own, all forgotten, unhooked",
      not raised and all(one.gave_up == 1 for one in held) and room.dressing == [] and room.waiting == []
      and wardrobe.IDENTIFIER not in state["hooks"] and room.hook is None)
room.add("Lemmy_20", "Rafa", Dressing())
room.frame()
check("a last call after the stop: nothing started", room.waiting[0][2].started == 0)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
