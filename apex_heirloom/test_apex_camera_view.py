"""Tests the camera watch: first person and a slide look through the eyes; third person, the vehicle's mode and a
camera looking from another actor do not; without a camera, or with one that cannot be read, the eyes are assumed,
said once and not at every frame."""

import pathlib
import sys
import types

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import heirloom_stubs  # noqa: E402

heirloom_stubs.install()
from apex_heirloom import apex_camera_view as view  # noqa: E402

fails: list[str] = []
said: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


character = types.SimpleNamespace(Name="OakCharacter_1")
vehicle = types.SimpleNamespace(Name="OakVehicle_2")


def spot(x: float, y: float = 0.0, z: float = 0.0) -> types.SimpleNamespace:
    return types.SimpleNamespace(X=x, Y=y, Z=z)


# The first-person arms' animation, their eye (the Camera bone) at the origin; any other bone far away.
arms = types.SimpleNamespace(Outer=types.SimpleNamespace(
    GetSocketLocation=lambda bone: spot(0.0) if bone == "Camera" else spot(1e6)))


def camera(mode: str, target: object = character, place: tuple = (0.0, 0.0, 0.0)) -> types.SimpleNamespace:
    return types.SimpleNamespace(GetActorCameraMode=lambda actor: mode if actor is character else "Other",
                                 ViewTarget=types.SimpleNamespace(Target=target),
                                 GetCameraLocation=lambda: spot(*place))


def outside(manager: object) -> str:
    return view.outside(manager, character, arms, said.append)


check("first person looks through the eyes", outside(camera("Default")) == "")
check("so does a slide", outside(camera("Slide")) == "")
check("third person does not", outside(camera("ThirdPerson")) == "in ThirdPerson")
check("nor the vehicle's mode", outside(camera("ThirdPersonVehicle")) == "in ThirdPersonVehicle")
check("nor a camera that looks from the vehicle, whatever its mode for the character",
      outside(camera("Default", vehicle)) == "from OakVehicle_2")
check("a camera looking from nothing counts as the eyes", outside(camera("Default", None)) == "")
# Getting out of a vehicle: the character's own camera, in Default, 370 to 600 cm behind the eyes for 1.25 s, and on
# foot within 12 cm of them (sondes/apex_exit_camera_watch.py, 2026-09-26).
check("the camera flying back to the eyes after a vehicle is not in them yet",
      outside(camera("Default", place=(-300.0, 0.0, 200.0))) == view.ON_ITS_WAY)
check("12 cm off the eyes, as on foot, is in them", outside(camera("Default", place=(0.0, 0.0, 12.0))) == "")
check("only third person is told apart as such", view.third_person(outside(camera("ThirdPerson")))
      and not view.third_person(view.ON_ITS_WAY) and not view.third_person("from OakVehicle_2")
      and not view.third_person(""))
check("without a camera, the eyes are assumed, silently", view.outside(None, character, arms, said.append) == ""
      and not said)
broken = types.SimpleNamespace(ViewTarget=types.SimpleNamespace(Target=character), GetCameraLocation=lambda: spot(0.0))
check("a mode that cannot be read counts as the eyes and is said",
      outside(broken) == "" and len(said) == 1 and "mode could not be read" in said[0])
outside(broken)
check("said once, not at every frame", len(said) == 1)
placeless = types.SimpleNamespace(GetActorCameraMode=lambda _actor: "Default",
                                  ViewTarget=types.SimpleNamespace(Target=character))
check("a place that cannot be read counts as the eyes and is said once",
      outside(placeless) == "" and outside(placeless) == "" and len(said) == 2 and "place could not be read" in said[1])

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
