"""Tests look_muzzle.py: a spot of the arms moved where the world shows it, away from the camera's
axis by the ratio of the two views' half-angle tangents, kept as far ahead; the hidden pistol's muzzle from the eye;
a piece's muzzle turned with the piece as Unreal turns a rotator; fields of view out of bounds refused."""

import math
import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

from apex_grapple import look_muzzle  # noqa: E402
import vex_fixture  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def near(a, b, within=1e-6) -> bool:
    return all(abs(x - y) <= within for x, y in zip(a, b))


character = sdk_stubs.FakeCharacter()
vex_fixture.camera(state, character, yaw=90.0)
pc = state["pc"]
spread = math.tan(math.radians(55.0)) / math.tan(math.radians(38.5))
moved = look_muzzle.from_arms(pc, (-10.0, 50.0, 160.0))
check("a spot of the arms kept as far ahead, pushed away from the axis by the two views' ratio",
      near(moved, (-10.0 * spread, 50.0, 170.0 - 10.0 * spread)))
check("the hidden pistol's muzzle: ahead, left and up from the eye, then where the arms would show it",
      near(look_muzzle.waiting(pc, (50.0, 10.0, -30.0)), (10.0 * spread, 50.0, 170.0 - 30.0 * spread)))
piece = types.SimpleNamespace(K2_GetComponentLocation=lambda: types.SimpleNamespace(X=100.0, Y=0.0, Z=50.0),
                              K2_GetComponentRotation=lambda: types.SimpleNamespace(Pitch=0.0, Yaw=90.0, Roll=90.0))
check("a piece's muzzle turned with the piece: yaw 90 takes its X to the world's Y, roll 90 its Y down",
      near(look_muzzle.on_piece(piece, (20.0, 5.0, 1.0)), (100.0 - 1.0, 20.0, 50.0 - 5.0)))
pc.PlayerCameraManager.GetFOVAngle = lambda: 0.0
try:
    look_muzzle.from_arms(pc, (1.0, 1.0, 1.0))
    refused = False
except ValueError:
    refused = True
check("a field of view the game misread is refused, not used", refused)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
