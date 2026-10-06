"""Tests where the top of the driver sits seen from the camera, and the zoom about it (spec section 3.8)."""

import math
import pathlib
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

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
