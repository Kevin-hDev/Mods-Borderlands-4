"""Tests look_view.py: the camera's ThirdPerson mode is the third person; a camera a metre or more from the character
along the ground too, whatever its mode; nearer, through the eyes."""

import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

sdk_stubs.install()

from apex_grapple import look_view  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def spot(x: float, y: float, z: float) -> types.SimpleNamespace:
    return types.SimpleNamespace(X=x, Y=y, Z=z)


def seen(mode: str, camera: tuple) -> str:
    manager = types.SimpleNamespace(GetActorCameraMode=lambda character: mode,
                                    GetCameraLocation=lambda: spot(*camera))
    character = types.SimpleNamespace(K2_GetActorLocation=lambda: spot(100.0, 200.0, 0.0))
    return look_view.of(types.SimpleNamespace(PlayerCameraManager=manager), character)


check("the game's third person camera", seen("CameraMode_ThirdPerson", (100.0, 200.0, 170.0)) == look_view.THIRD)
check("Kevin's camera behind, its mode lost", seen("Default", (100.0, 300.0, 170.0)) == look_view.THIRD)
check("through the eyes: the camera within a metre along the ground, however high",
      seen("Default", (110.0, 205.0, 900.0)) == look_view.FIRST
      and seen("FirstPerson", (100.0, 299.0, 170.0)) == look_view.FIRST)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
