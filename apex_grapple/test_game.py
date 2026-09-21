"""Tests what the mod reads from the game and the two things it writes: the velocity and the movement mode."""

import math
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

from apex_grapple import game  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def near(got: float, wanted: float, margin: float = 0.01) -> bool:
    return abs(got - wanted) <= margin


player = sdk_stubs.FakeCharacter()
movement = player.CharacterMovement
state["pc"] = sdk_stubs.player(player, state["mappings"])

check("with no player there is no character yet", game.character() is None)
check("the first look finds the player", game.refresh(0, at_once=True))
check("and hands the character over", game.character() is player)
check("a second look a moment later costs nothing", not game.refresh(1, at_once=True))

check("the key list comes from the game", len(game.input_mappings()) == len(state["mappings"]))

check("standing on the ground reads as standing", game.is_on_ground(movement))
check("the mode is named", game.movement_mode(movement) == "MOVE_Walking")
movement.MovementMode = sdk_stubs.Mode("MOVE_Falling")
check("falling does not read as standing", not game.is_on_ground(movement))

check("the position comes back as three numbers", game.location(player) == (0.0, 0.0, 100.0))
movement.Velocity = sdk_stubs.vector(10.0, -20.0, 30.0)
check("so does the velocity", game.velocity(movement) == (10.0, -20.0, 30.0))
game.set_velocity(movement, (1.0, 2.0, 3.0))
check("a written velocity is written whole", game.velocity(movement) == (1.0, 2.0, 3.0))

check("the gravity is the game's own, as a positive number", near(game.gravity(movement), 980.0))
movement.GravityScale = 2.0
check("Apex Movement's doubled gravity is followed", near(game.gravity(movement), 1960.0))


def refuse() -> float:
    raise AttributeError("no such function on this build")


movement.GetGravityZ = refuse
check("a game that will not answer falls back on the measured 980 times the scale",
      near(game.gravity(movement), 1960.0))
movement.GetGravityZ = lambda: 0.0
check("a gravity of zero is not believed either", near(game.gravity(movement), 1960.0))
movement.GravityScale = 1.0

player.input = sdk_stubs.vector(0.6, -0.8, 0.0)
check("the stick comes back in world axes", game.stick(player) == (0.6, -0.8, 0.0))

player.pitch, player.yaw = 0.0, 90.0
looking = game.aim(player)
check("the eyes sit above the middle of the character",
      looking is not None and near(looking[0][2], 100.0 + game.EYE_ABOVE_CENTRE))
check("a yaw of ninety looks along Y", near(looking[1][0], 0.0) and near(looking[1][1], 1.0))
player.pitch, player.yaw = 90.0, 0.0
check("a pitch of ninety looks straight up", near(game.aim(player)[1][2], 1.0))
player.pitch, player.yaw = -45.0, 0.0
check("a pitch of minus forty five looks down at forty five", near(game.aim(player)[1][2], -math.sin(math.pi / 4)))

# The camera manager is the first choice; the eyes are the fallback, and both must work.
state["pc"].PlayerCameraManager = sdk_stubs.types.SimpleNamespace(
    GetCameraLocation=lambda: sdk_stubs.vector(5.0, 6.0, 7.0),
    GetCameraRotation=lambda: sdk_stubs.types.SimpleNamespace(Pitch=0.0, Yaw=0.0, Roll=0.0))
check("the camera is used when the game gives one", game.aim(player)[0] == (5.0, 6.0, 7.0))
state["pc"].PlayerCameraManager = sdk_stubs.types.SimpleNamespace(
    GetCameraLocation=lambda: (_ for _ in ()).throw(RuntimeError("no camera yet")),
    GetCameraRotation=lambda: None)
check("a camera that fails falls back on the eyes rather than losing the shot",
      near(game.aim(player)[0][2], 100.0 + game.EYE_ABOVE_CENTRE))
state["pc"].PlayerCameraManager = None

player.Controller = None
check("no controller means no aim at all, rather than a wrong one", game.aim(player) is None)

player.destroyed = True
check("a destroyed character is not handed out", game.character() is None)
game.forget()
check("forgetting leaves nothing behind", game.character() is None and game.anim() is None)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
