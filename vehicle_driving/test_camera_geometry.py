"""Tests where the top of the driver sits seen from the camera, and the zoom about it (spec section 3.8)."""

import math
import pathlib
import random
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def near(values: tuple, targets: tuple) -> bool:
    return all(math.isclose(a, b, abs_tol=1e-6) for a, b in zip(values, targets))


def rotation(pitch: float, yaw: float) -> types.SimpleNamespace:
    return types.SimpleNamespace(Pitch=pitch, Yaw=yaw, Roll=0.0)


def broken() -> None:
    raise RuntimeError("unreadable")


# The formulas as they were up to 1.0.11, frozen here: the ones in the mod must give the same numbers to the last digit.
def old_point(vector: object) -> tuple | None:
    values = (float(vector.X), float(vector.Y), float(vector.Z))
    return values if all(math.isfinite(value) for value in values) else None


def old_basis(rotation: object) -> tuple:
    pitch, yaw = math.radians(float(rotation.Pitch)), math.radians(float(rotation.Yaw))
    forward = (math.cos(pitch) * math.cos(yaw), math.cos(pitch) * math.sin(yaw), math.sin(pitch))
    right = (-math.sin(yaw), math.cos(yaw), 0.0)
    up = (-math.sin(pitch) * math.cos(yaw), -math.sin(pitch) * math.sin(yaw), math.cos(pitch))
    return forward, right, up


def old_to_camera(vector: tuple, axes: tuple) -> tuple:
    return tuple(sum(a * b for a, b in zip(vector, axis)) for axis in axes)


def old_zoomed(seen: tuple, applied: tuple, share: float) -> tuple:
    game = tuple(value + offset for value, offset in zip(seen, applied))
    return tuple((1.0 - share) * value for value in game)


def generators(function: object) -> list[str]:
    return [const.co_name for const in function.__code__.co_consts
            if isinstance(const, types.CodeType) and const.co_name == "<genexpr>"]


sdk_stubs.install()

from vehicle_driving import camera_geometry as geometry  # noqa: E402

check("looking straight down, a point below is straight ahead",
      near(geometry.to_camera((0.0, 0.0, -100.0), geometry.basis(rotation(-90.0, 0.0))), (100.0, 0.0, 0.0)))
turned = geometry.basis(rotation(0.0, 90.0))
check("turned a quarter right, the world's Y is ahead and its -X on the right",
      near(geometry.to_camera((0.0, 50.0, 0.0), turned), (50.0, 0.0, 0.0))
      and near(geometry.to_camera((-20.0, 0.0, 0.0), turned), (0.0, 20.0, 0.0)))
check("looking up 30 degrees, a point above is partly ahead",
      near(geometry.to_camera((0.0, 0.0, 10.0), geometry.basis(rotation(30.0, 0.0))),
           (5.0, 0.0, 10.0 * math.cos(math.radians(30.0)))))

driver = sdk_stubs.Driver()
car = sdk_stubs.Vehicle("OakVehicle_1", driver)
check("the target is the top of the driver's capsule", geometry.driver_top(car) == (100.0, 200.0, 250.0))
driver.CapsuleComponent = None
check("a capsule that cannot be read counts as a standing character's", geometry.driver_top(car) == (100.0, 200.0, 260.0))
driver.CapsuleComponent = types.SimpleNamespace(GetScaledCapsuleHalfHeight=lambda: 1000.0)
check("and so does one beyond any character", geometry.driver_top(car) == (100.0, 200.0, 260.0))
car.DriverPawn = None
check("no driver, no target", geometry.driver_top(car) is None)
lost = sdk_stubs.Driver()
lost.location = sdk_stubs.vector(float("nan"), 0.0, 0.0)
car.DriverPawn = lost
check("a driver nowhere, no target", geometry.driver_top(car) is None)

seated = sdk_stubs.Vehicle("OakVehicle_2", sdk_stubs.Driver())
camera = sdk_stubs.CameraManager()
check("seen from the camera, the top of the driver is ahead and a little below",
      near(geometry.sighting(seated, camera), (400.0, 0.0, -10.0)))
check("that is 1.43 degrees under the reticle", abs(geometry.below_reticle((400.0, 0.0, -10.0)) - 1.4321) < 0.001)
camera.GetCameraLocation = broken
check("a camera that cannot be read, nothing seen", geometry.sighting(seated, camera) is None)

check("a zoom to 0.7 moves the camera 30 percent of the way to the target",
      near(geometry.zoomed((400.0, 0.0, -10.0), geometry.ZERO, 0.7), (120.0, 0.0, -3.0)))
check("seen from a camera already moved, the offset it carries is added back first",
      near(geometry.zoomed((280.0, 0.0, -7.0), (120.0, 0.0, -3.0), 0.7), (120.0, 0.0, -3.0)))
check("a zoom beyond 1 moves the camera back", near(geometry.zoomed((400.0, 0.0, -10.0), geometry.ZERO, 1.35),
                                                    (-140.0, 0.0, 3.5)))

rng = random.Random(20261024)
differences = 0
for _ in range(20_000):
    turned_to = rotation(rng.uniform(-89.0, 89.0), rng.uniform(-180.0, 180.0))
    target = (rng.uniform(-3000.0, 3000.0), rng.uniform(-3000.0, 3000.0), rng.uniform(-3000.0, 3000.0))
    applied = (rng.uniform(-500.0, 500.0), rng.uniform(-500.0, 500.0), rng.uniform(-500.0, 500.0))
    share = rng.choice((0.7, 0.35, 0.5, 1.35, rng.uniform(0.1, 2.0)))
    axes = old_basis(turned_to)
    spot = sdk_stubs.vector(rng.uniform(-1e5, 1e5), rng.uniform(-1e5, 1e5), rng.uniform(-1e4, 1e4))
    differences += repr(geometry.basis(turned_to)) != repr(axes)
    differences += repr(geometry.to_camera(target, axes)) != repr(old_to_camera(target, axes))
    differences += repr(geometry.zoomed(target, applied, share)) != repr(old_zoomed(target, applied, share))
    differences += repr(geometry.point(spot)) != repr(old_point(spot))
    rider = sdk_stubs.Driver()
    rider.location = sdk_stubs.vector(rng.uniform(-1e5, 1e5), rng.uniform(-1e5, 1e5), rng.uniform(-1e4, 1e4))
    eye = sdk_stubs.CameraManager()
    eye.location, eye.rotation = spot, turned_to
    top = old_point(rider.location)
    expected = old_to_camera(tuple(a - b for a, b in zip((top[0], top[1], top[2] + 80.0), old_point(spot))), axes)
    differences += repr(geometry.sighting(sdk_stubs.Vehicle("OakVehicle_3", rider), eye)) != repr(expected)
odd = (float("nan"), float("inf"), -float("inf"), 1e308, -0.0)
for x in odd:
    spot = sdk_stubs.vector(x, 1.0, 2.0)
    differences += repr(geometry.point(spot)) != repr(old_point(spot))
check("the formulas give the same numbers as before to the last digit, on 20,000 random cameras and targets",
      differences == 0)
hot = [geometry.point, geometry.basis, geometry.to_camera, geometry.driver_top, geometry.sighting, geometry.zoomed]
check("no generator runs in the camera's formulas at each frame", all(generators(function) == [] for function in hot))
calls = {"cos": 0, "sin": 0}
real_math = geometry.math
counting = types.SimpleNamespace(**{name: getattr(math, name) for name in dir(math) if not name.startswith("_")})
counting.cos = lambda value: calls.__setitem__("cos", calls["cos"] + 1) or math.cos(value)
counting.sin = lambda value: calls.__setitem__("sin", calls["sin"] + 1) or math.sin(value)
geometry.math = counting
geometry.basis(rotation(12.0, 34.0))
geometry.math = real_math
check("a camera's axes take one cosine and one sine of each angle", calls == {"cos": 2, "sin": 2})

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
