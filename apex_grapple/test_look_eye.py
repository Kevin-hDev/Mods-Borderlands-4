"""Tests look_eye.py: the camera of the frame being drawn. The game's camera, filled at the end of the frame before,
moved by the character's step since; turned as the controller turns now; taken as given when that frame was not
seen; the two clocks matched within a few thousandths of a second; only the last frames kept."""

import math
import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

from apex_grapple import look_eye  # noqa: E402
import sdk_objects  # noqa: E402
import vex_fixture  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def near(a, b, within=1e-6) -> bool:
    return all(abs(x - y) <= within for x, y in zip(a, b))


character = sdk_stubs.FakeCharacter()
clock = vex_fixture.camera(state, character, yaw=90.0)
pc = state["pc"]
manager = pc.PlayerCameraManager

eye, (ahead, left, up) = look_eye.camera(pc)
check("a camera filled before any frame seen is taken as given; looking along +Y, left is +X, Unreal's Y being right",
      eye == vex_fixture.EYE and near(ahead, (0.0, 1.0, 0.0)) and near(left, (1.0, 0.0, 0.0)) and near(up, (0, 0, 1)))

# Frame 1 at 10 s: the character at the origin. Frame 2: it has moved 40 cm along X; the camera handed out is
# still frame 1's, filled at its end, its clock kept in single precision.
clock["now"] = 10.0
look_eye.note(pc)
clock["now"] = 10.0101
character.location = sdk_objects.vector(40.0, 0.0, 0.0)
manager.CameraCachePrivate.Timestamp = 10.0004
eye, _axes = look_eye.camera(pc)
check("the camera of the frame before is moved by the character's step since", near(eye, (40.0, 0.0, 170.0)))
check("asked again in the same frame, the same camera", near(look_eye.camera(pc)[0], (40.0, 0.0, 170.0)))

pc.ControlRotation = types.SimpleNamespace(Pitch=-30.0, Yaw=180.0, Roll=0.0)
_eye, (ahead, left, up) = look_eye.camera(pc)
check("turned as the controller turns now, not as the camera handed out",
      near(ahead, (-math.cos(math.radians(30)), 0.0, -0.5)) and near(left, (0.0, 1.0, 0.0))
      and near(up, (-0.5, 0.0, math.cos(math.radians(30)))))

manager.CameraCachePrivate.Timestamp = 10.0101
check("a camera filled in this very frame is not moved", near(look_eye.camera(pc)[0], vex_fixture.EYE))

manager.CameraCachePrivate.Timestamp = 9.98
check("a camera from a frame not seen is taken as given", near(look_eye.camera(pc)[0], vex_fixture.EYE))

for second in (10.02, 10.03, 10.04):
    clock["now"] = second
    look_eye.note(pc)
check("only the last two frames are kept", sorted(look_eye._seen) == [10.03, 10.04])
manager.CameraCachePrivate.Timestamp = 10.0
check("so a frame long gone no longer moves the camera", near(look_eye.camera(pc)[0], vex_fixture.EYE))

look_eye.forget()
check("forgotten, nothing is kept", look_eye._seen == {})

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
