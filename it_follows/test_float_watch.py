"""Tests the float watch (decision 72): each sample the next PER_SAMPLE walking enemies of the horde in turn, flyers
never; each traced under from its centre down to DOWN_M, its kind keying the half height; one whose feet stand more
than ABOVE_M above the ground met, or above nothing, floats, counted and named up to SHOWN with its mode, its height
and how long ago the catch-up moved it; one on a character or a projectile counted apart; one in water, falling,
flying, gone or unplaced is no floater; a status line's gauge forgets what it said; a failed trace stops the watch,
said. With ground.py's own trace on the catch-up's fake library, so that the frontier between them is the real one."""

import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

import catch_up_fixture as fixture  # noqa: E402
from it_follows import float_watch, ground  # noqa: E402

fixture.keep_struct_names()
fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


class Trace:
    """ground.py's trace: what each kind's trace says, the ground under the enemy at 0 by default."""

    def __init__(self) -> None:
        self.asked: list[tuple] = []
        self.says: dict[str, tuple] = {}

    def ground(self, name: str, mover: object, point: tuple, up_cm: float, down_cm: float) -> tuple:
        self.asked.append((name, mover, point, up_cm, down_cm))
        return self.says.get(name, ("found", (point[0], point[1], 60.0 + ground.CLEARANCE_CM), "Landscape"))


class Body:
    """An enemy of the game: its centre and its movement mode as the game writes it."""

    def __init__(self, z: float = 60.0, mode: str = "MOVE_Walking") -> None:
        self.z = z
        self.CharacterMovement = types.SimpleNamespace(MovementMode=f"EMovementMode.{mode}")
        self.CapsuleComponent = types.SimpleNamespace(GetScaledCapsuleHalfHeight=lambda: 60.0)

    def K2_GetActorLocation(self) -> object:
        return types.SimpleNamespace(X=0.0, Y=0.0, Z=self.z)


def chaser(name: str, body: object, kind: str = "Char_BeastBasic", walks: bool = True) -> object:
    return types.SimpleNamespace(name=name, kind=kind, walks=walks, actor=lambda: body)


moved = {"w2": 990.0}

try:
    check("four a second, higher than 1.5 m, down to 30 m, five named, falling and flying left alone",
          (float_watch.PER_SAMPLE, float_watch.ABOVE_M, float_watch.DOWN_M, float_watch.SHOWN, float_watch.AIRBORNE)
          == (4, 1.5, 30.0, 5, ("MOVE_Falling", "MOVE_Flying")))

    trace = Trace()
    watch = float_watch.FloatWatch(trace, moved.get)
    horde = [chaser(f"w{index}", Body(), kind=f"Char_Kind{index}") for index in range(6)]
    horde.insert(2, chaser("bat", Body(), walks=False))
    watch.look(horde, 1000.0)
    watch.look(horde, 1001.0)
    check("each sample the next four walkers in turn, the flyer never; each traced from its centre down to DOWN_M, "
          "its kind keying the half height",
          [entry[0] for entry in trace.asked] == ["Char_Kind0", "Char_Kind1", "Char_Kind2", "Char_Kind3",
                                                  "Char_Kind4", "Char_Kind5", "Char_Kind0", "Char_Kind1"]
          and all(entry[3:] == (0.0, 3000.0) and entry[2] == (0.0, 0.0, 60.0) for entry in trace.asked))
    check("an enemy standing on the ground does not float", watch.gauge() == {
        "looked": 8, "floating": 0, "on_body": 0, "floaters": []})

    trace = Trace()
    watch = float_watch.FloatWatch(trace, moved.get)
    trace.says = {"Char_High": ("found", (0.0, 0.0, 60.0 + ground.CLEARANCE_CM), "Landscape"),
                  "Char_Bridge": ("no_ground", None, None),
                  "Char_Stacked": (ground.NOT_WORLD, None, "PersistentLevel.Char_BeastBasic_1.CollisionBubble"),
                  "Char_Wading": ("water", None, "WaterBodyLake")}
    horde = [chaser("w0", Body(z=60.0 + 150.0), kind="Char_High"), chaser("w1", Body(z=560.0), kind="Char_High"),
             chaser("w2", Body(), kind="Char_Bridge"), chaser("w3", Body(), kind="Char_Stacked")]
    watch.look(horde, 1000.0)
    watch.turn = 0
    watch.look([chaser("w4", Body(), kind="Char_Wading"), chaser("w5", Body(z=900.0, mode="MOVE_Falling")),
                chaser("w6", Body(z=900.0, mode="MOVE_Flying")), chaser("w7", None)], 1001.0)
    watch.turn = 0
    watch.look([chaser("w8", Body(z=None))], 1002.0)
    said = watch.gauge()
    check("feet 1.5 m above the ground do not float; 5 m above it, or above nothing down to DOWN_M, float, named with "
          "the mode, the height and how long ago the catch-up moved them; one on a character counted apart",
          said == {"looked": 5, "floating": 2, "on_body": 1, "floaters": [
              {"on": "w1", "mode": "MOVE_Walking", "above_m": 5.0, "moved_s_ago": None},
              {"on": "w2", "mode": "MOVE_Walking", "above_m": None, "moved_s_ago": 10.0}]})
    check("one in water is looked at and does not float; one falling or flying is not traced; one gone or unplaced "
          "is not looked at", [entry[0] for entry in trace.asked][-1] == "Char_Wading" and len(trace.asked) == 5)
    check("a status line's gauge forgets what it said",
          watch.gauge() == {"looked": 0, "floating": 0, "on_body": 0, "floaters": []})

    trace.says = {"Char_BeastBasic": ("no_ground", None, None)}
    watch.look([chaser(f"b{index}", Body()) for index in range(8)], 1000.0)
    watch.look([chaser(f"b{index}", Body()) for index in range(8)], 1001.0)
    said = watch.gauge()
    check("eight floating, five named", said["floating"] == 8 and len(said["floaters"]) == float_watch.SHOWN)

    trace.says = {"Char_BeastBasic": ("call_failed:RuntimeError", None, None)}
    asked = len(trace.asked)
    watch.look([chaser(f"b{index}", Body()) for index in range(8)], 1002.0)
    watch.look([chaser(f"b{index}", Body()) for index in range(8)], 1003.0)
    said = watch.gauge()
    check("a failed trace stops the watch, said in every gauge after",
          len(trace.asked) == asked + 1 and said["broken"] == "call_failed:RuntimeError" and said["looked"] == 0
          and watch.gauge()["broken"] == "call_failed:RuntimeError")

    events: list = []
    library = fixture.TraceLibrary(events, ground_z=40.0)
    state["classes"]["KismetSystemLibrary"] = types.SimpleNamespace(ClassDefaultObject=library)
    watch = float_watch.FloatWatch(ground.GroundTrace(lambda call, log=True, **fields: None), moved.get)
    standing, floating = Body(z=40.0 + 60.0), Body(z=40.0 + 60.0 + 500.0)
    watch.look([chaser("s", standing), chaser("f", floating, kind="Char_Other")], 1000.0)
    said = watch.gauge()
    check("with ground.py's own trace: on the ground 40 cm high, standing; 5 m above it, floating; traced from the "
          "enemy's centre, itself the context",
          said["looked"] == 2 and said["floating"] == 1 and said["floaters"][0]["on"] == "f"
          and said["floaters"][0]["above_m"] == 5.0 and library.asked[0][0] is standing
          and library.asked[0][1].Z == 100.0 and library.asked[0][2].Z == 100.0 - 3000.0)
except Exception as error:
    fails.append(f"exception {type(error).__name__}: {error}")
    print(f"ECHEC | exception {type(error).__name__}: {error}")

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
