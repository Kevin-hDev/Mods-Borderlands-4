"""Shared setup for independent grapple lifecycle and control tests."""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

from apex_grapple import game, grapple, settings  # noqa: E402

fails: list[str] = []
SECOND = 1_000_000_000


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def fly(player, rope, from_s: float, to_s: float, step: float = 0.05) -> float:
    """Runs the pull frame by frame, moving the player the way the mod sent him.

    The mod owns the velocity while the rope holds, and it watches whether the player really covers
    the ground it gave him: a test that left him standing still would read as a wall.
    """
    now = from_s
    while now < to_s - 1e-9:
        speed = game.velocity(player.CharacterMovement)
        spot = player.location
        player.location = sdk_stubs.vector(spot.X + speed[0] * step, spot.Y + speed[1] * step,
                                           spot.Z + speed[2] * step)
        now = round(now + step, 4)
        rope.update(player, int(now * SECOND))
    return now


def fresh(hit=(1000.0, "StaticMeshActor"), on_ground=True):
    """A player looking along X, with a surface where the test asks for one.

    In the air by choice, for the tests of the model itself: a pull that starts on the ground is
    given the take-off lift, which is not part of the model and would hide what it does.
    """
    player = sdk_stubs.FakeCharacter()
    if not on_ground:
        player.CharacterMovement.MovementMode = sdk_stubs.Mode("MOVE_Falling")
    state["pc"] = sdk_stubs.player(player, state["mappings"])
    state["kismet"].hit = hit
    game.forget()
    game.refresh(0, at_once=True)
    return player, grapple.Rope()
