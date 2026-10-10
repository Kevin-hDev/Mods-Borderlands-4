"""Tests the omni direction unit: what it asks of its parts from the elected mod's settings, Omni Sprint's own switch
and the view the game shows, the crouch dash and the slides' direction included; its hook on the played body only; a
new body forgotten; the hook off when idle; an error stopping it for the session with everything given back."""

import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from apex_camera_runtime import omni_direction, omni_direction_reads  # noqa: E402
from apex_camera_runtime.sprint_slot import CARRIER, FORWARD, NONE  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def OmniValues(body: bool, full_turn: bool, sprint: bool, dash: bool) -> types.SimpleNamespace:
    """As omni_direction_options.OmniValues, which needs the SDK's option classes to import."""
    return types.SimpleNamespace(body=body, full_turn=full_turn, sprint=sprint, dash=dash)


def obj(address: int, **values) -> types.SimpleNamespace:
    return types.SimpleNamespace(_get_address=lambda: address, **values)


class Hooks:
    Type = types.SimpleNamespace(PRE="PRE", POST="POST")

    def __init__(self) -> None:
        self.installed: dict = {}

    def add_hook(self, path, kind, identifier, callback) -> None:
        self.installed[(path, kind, identifier)] = callback

    def has_hook(self, path, kind, identifier) -> bool:
        return (path, kind, identifier) in self.installed

    def remove_hook(self, path, kind, identifier) -> None:
        del self.installed[(path, kind, identifier)]


class Parts:
    """The unit's parts, recorded: each is tested in its own file."""

    def __init__(self) -> None:
        self.calls: list[tuple] = []
        self.holding = False
        self.anim_id = 0
        self.owner = None
        self.carrier = self
        self.offset = 0.0
        self.original = None

    def update(self, *args) -> None:
        self.calls.append(("update",) + args)

    def acting(self, pc, anim, now_ns) -> bool:
        self.calls.append(("acting",))
        return False

    def step(self, character, anim, pose, acting, full_turn, now_ns) -> bool:
        self.calls.append(("step", full_turn))
        return self.holding

    def release(self, anim, pose) -> None:
        self.calls.append(("release",))
        self.holding = False

    def reset(self) -> None:
        self.calls.append(("reset",))

    def stop(self) -> tuple[int, int]:
        self.calls.append(("stop",))
        return 0, 0


class Recorder:
    """The crouch dash and the slide launch, recorded: each is tested in its own file."""

    def __init__(self, name: str) -> None:
        self.name, self.calls = name, []

    def update(self, *args) -> None:
        self.calls.append(args)

    def stop(self) -> None:
        self.calls.append("stop")

    give_back = stop


hooks, lines = Hooks(), []
anim = obj(10)
character = obj(20, Mesh=types.SimpleNamespace(GetAnimInstance=lambda: anim))
pc = types.SimpleNamespace(OakCharacter=character)
clock = [0]
game = omni_direction.Game(lambda: pc, None, None, lambda value: lambda: value, None, None, hooks, lines.append,
                           lambda: clock[0], None)
unit = omni_direction.OmniDirection(lambda: game)
mode = ["ThirdPerson"]
manager = types.SimpleNamespace(GetActorCameraMode=lambda actor: mode[0])
controller = types.SimpleNamespace(_in_vehicle=False, _desired_mode="ThirdPerson",
                                   climb=types.SimpleNamespace(busy=False),
                                   _lifetime=types.SimpleNamespace(owned=lambda: (character, manager)))
values = [OmniValues(True, True, True, True)]
apex = types.SimpleNamespace(omni_direction=lambda: values[0])
old_mod = types.SimpleNamespace()
omni_switch = [False]
omni = types.SimpleNamespace(sprint_everywhere=lambda: omni_switch[0])
clients = [types.SimpleNamespace(settings=apex), types.SimpleNamespace(settings=omni)]
HOOK = (omni_direction.FRAME, "PRE", omni_direction.IDENTIFIER)

unit._start()
parts = Parts()
unit.keeper = unit.slot = unit.facing = unit.actions = parts
crouch, slides = unit.crouch, unit.slides = Recorder("crouch"), Recorder("slides")
unit.pose = types.SimpleNamespace(original=None)
unit.sync(clients, old_mod, pc, None, 1)
check("an older mod: crouch keys not bound, a dash asked by default, the slides left to the game",
      crouch.calls[-1] == (pc, False, True, 1) and slides.calls[-1] == (False, 1))
check("an elected mod older than the unit asks nothing: no hook, the sprint limit not asked",
      HOOK not in hooks.installed and parts.calls[-1] == ("update", pc, False, 1))
omni_switch[0] = True
unit.sync(clients, old_mod, pc, None, 2)
check("Omni Sprint's own switch opens the sprint whoever is elected, and the hook goes in",
      parts.calls[-1] == ("update", pc, True, 2) and HOOK in hooks.installed)
omni_switch[0] = False
unit.sync(clients, apex, pc, controller, 3)
check("third person with the sprint on: the limit is asked open", parts.calls[-1] == ("update", pc, True, 3)
      and unit.third_person and unit.facing_wanted())
check("the sprint open: the crouch keys bound with the chosen dash, the slides follow the run",
      crouch.calls[-1] == (pc, True, True, 3) and slides.calls[-1] == (True, 3))
for name, change in (("at the wheel", ("_in_vehicle", True)), ("in Orbit", ("_desired_mode", "Orbit")),
                     ("climbing", ("climb", types.SimpleNamespace(busy=True)))):
    before = getattr(controller, change[0])
    setattr(controller, *change)
    check(f"{name}, it is not third person", omni_direction_reads.in_third_person(controller) is False)
    setattr(controller, change[0], before)
mode[0] = "Default"
check("the first-person view is not third person", omni_direction_reads.in_third_person(controller) is False)
mode[0] = "ThirdPerson"

frame = hooks.installed[HOOK]
parts.calls.clear()
frame(obj(99), None, None, None)
check("another animation's update does nothing", parts.calls == [])
frame(anim, None, None, None)
check("the body's first update forgets any old hold", parts.calls[0] == ("reset",) and unit.body_id == 10)
parts.holding = True
clock[0] = 50
frame(anim, None, None, None)
check("the played body's update: actions, then a step at 360 degrees, then the forward sprint in the slot",
      parts.calls[-3:] == [("acting",), ("step", True), ("update", character, anim, 10, FORWARD, 50)])
parts.holding = False
values[0] = OmniValues(True, False, True, True)
unit.sync(clients, apex, pc, controller, 4)
frame(anim, None, None, None)
check("let go with the sprint open: the carrier's turn, and the angle read at 180",
      ("step", False) in parts.calls and parts.calls[-1][4] == CARRIER)
values[0] = OmniValues(False, True, False, True)
unit.sync(clients, apex, pc, controller, 5)
check("the body and the sprint off: no crouch keys, the slides back to the aim",
      crouch.calls[-1] == (pc, False, True, 5) and slides.calls[-1] == (False, 5))
values[0] = OmniValues(True, True, False, False)
unit.sync(clients, apex, pc, controller, 5)
check("the body on, the sprint off: the slides still follow the run; slide chosen reaches the crouch",
      crouch.calls[-1] == (pc, False, False, 5) and slides.calls[-1] == (True, 5))
values[0] = OmniValues(False, True, False, True)
unit.sync(clients, apex, pc, controller, 5)
parts.holding = True
parts.calls.clear()
frame(anim, None, None, None)
check("the body switched off while held: released at once, no step", ("release",) in parts.calls
      and ("step", True) not in parts.calls and parts.calls[-1][4] == NONE)

new_anim = obj(11)
character.Mesh = types.SimpleNamespace(GetAnimInstance=lambda: new_anim)
parts.holding, parts.offset = True, 30.0
values[0] = OmniValues(True, True, True, True)
unit.sync(clients, apex, pc, controller, 6)
frame(new_anim, None, None, None)
check("a new body: the old hold is forgotten and the actions start afresh",
      ("reset",) in parts.calls and unit.body_id == 11)

values[0] = OmniValues(False, True, False, True)
parts.holding = False
unit.sync(clients, apex, pc, controller, 7)
check("nothing asked and nothing held: the hook comes off", HOOK not in hooks.installed)
values[0] = OmniValues(True, True, True, True)
unit.sync(clients, apex, pc, controller, 8)
check("asked again: the hook goes back in", HOOK in hooks.installed)

parts.step = lambda *args: 1 / 0
parts.calls.clear()
frame(new_anim, None, None, None)
check("an error stops the unit for the session, said once, everything given back and the hook off",
      unit.failed and lines[-1] == "omni direction stopped for the session after an error: ZeroDivisionError"
      and ("stop",) in parts.calls and HOOK not in hooks.installed
      and crouch.calls[-1] == "stop" and slides.calls[-1] == "stop")
count = len(parts.calls)
unit.sync(clients, apex, pc, controller, 9)
frame(new_anim, None, None, None)
check("stopped, it does nothing more", len(parts.calls) == count)

failing = omni_direction.OmniDirection(lambda: game)
failing._start()
failing.keeper = failing.slot = failing.facing = failing.actions = Parts()
failing.crouch, failing.slides = Recorder("crouch"), Recorder("slides")
failing.pose = types.SimpleNamespace(original=None)
failing.slot.stop = lambda: 1 / 0
failing._fail(ValueError())
check("giving back that fails too is said, never raised into the game's hook",
      failing.failed and lines[-1] == "omni direction could not give everything back: ZeroDivisionError")
stopping = omni_direction.OmniDirection(lambda: game)
stopping._start()
stopping.keeper = types.SimpleNamespace(stop=lambda: (1, 1))
stopping.crouch, stopping.slides = Recorder("crouch"), Recorder("slides")
stopping.stop()
check("stopping says what it put back of the sprint limit",
      lines[-1] == "stopped, game sprint limit put back in 1 movement definition(s), 1 left alone: no longer "
                   "recognised in memory")
broken = omni_direction.OmniDirection(lambda: game)
broken.sync(clients, types.SimpleNamespace(omni_direction=lambda: 1 / 0), pc, controller, 0)
check("an error while syncing stops it too", broken.failed)
unstarted = omni_direction.OmniDirection(lambda: 1 / 0)
unstarted.stop()
check("stopping a unit never started does nothing", unstarted.game is None)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
