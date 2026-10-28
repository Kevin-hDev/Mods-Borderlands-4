"""Tests the camera view at the wheel: what it writes each frame, and that it takes back only its own (spec section
3.8)."""

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


def at(manager: object) -> types.SimpleNamespace:
    """The player's controller, its camera manager given."""
    return types.SimpleNamespace(PlayerCameraManager=manager)


def generators(function: object) -> list[str]:
    return [const.co_name for const in function.__code__.co_consts
            if isinstance(const, types.CodeType) and const.co_name == "<genexpr>"]


class CountedOffset:
    """An offset counting how often its components are read."""

    def __init__(self) -> None:
        self.__dict__.update(values={"X": 0.0, "Y": 0.0, "Z": 0.0}, reads=0)

    def __getattr__(self, name: str) -> float:
        if name not in ("X", "Y", "Z"):
            raise AttributeError(name)
        self.__dict__["reads"] += 1
        return self.__dict__["values"][name]

    def __setattr__(self, name: str, value: float) -> None:
        self.__dict__["values"][name] = value


def offset(manager: sdk_stubs.CameraManager) -> tuple:
    held = manager.CameraModeState.CameraLocationOffset
    return held.X, held.Y, held.Z


class Stuck:
    """An offset the game will not let us write."""

    X = Y = Z = 0.0

    def __setattr__(self, name: str, value: float) -> None:
        pass


sdk_stubs.install()

from vehicle_driving import camera_view, report  # noqa: E402

MS = 1_000_000
ZERO = (0.0, 0.0, 0.0)
driver = sdk_stubs.Driver()
car = sdk_stubs.Vehicle("OakVehicle_1", driver)
manager = sdk_stubs.CameraManager()
view = camera_view.CameraView()

check("the game's own view writes nothing",
      view.step(0, car, at(manager), "Default", ZERO) == [] and offset(manager) == ZERO)
view.step(1 * MS, car, at(manager), "Close", ZERO)
check("Close moves the camera 30 percent of the way to the top of the driver", near(offset(manager), (120.0, 0.0, -3.0)))
manager.draw()
view.step(2 * MS, car, at(manager), "Close", ZERO)
check("drawn with it, the next frame writes the same: the zoom holds still", near(offset(manager), (120.0, 0.0, -3.0)))
view.step(3 * MS, car, at(manager), "Close", ZERO)
check("a frame the game has not drawn yet writes the same too", near(offset(manager), (120.0, 0.0, -3.0)))
manager.draw()
view.step(4 * MS, car, at(manager), "Closest", ZERO)
check("Closest after Close counts the offset Close left: 65 percent of the way", near(offset(manager), (260.0, 0.0, -6.5)))
manager.draw()
view.step(5 * MS, car, at(manager), "Custom", (200.0, -30.0, 90.0))
check("Custom writes its three sliders as they are", offset(manager) == (200.0, -30.0, 90.0))
manager.draw()
view.step(6 * MS, car, at(manager), "Far", ZERO)
check("Far after Custom counts the Custom offset the camera carries: 35 percent further back",
      near(offset(manager), (-140.0, 0.0, 3.5)))
view.step(7 * MS, car, at(manager), "Default", ZERO)
check("back to the game's view, our value still in place is set back to 0", offset(manager) == ZERO)
manager.draw()
view.step(8 * MS, car, at(manager), "Close", ZERO)
manager.CameraModeState.CameraLocationOffset.X = 55.0
check("a value that is no longer ours is never erased",
      view.release() == [] and manager.CameraModeState.CameraLocationOffset.X == 55.0)
manager.CameraModeState.CameraLocationOffset = types.SimpleNamespace(X=0.0, Y=0.0, Z=0.0)
view.step(9 * MS, car, at(manager), "Custom", ZERO)
check("Custom left at 0 is the game's view: nothing written", offset(manager) == ZERO)

fresh = camera_view.CameraView()
car.DriverPawn = None
fresh.step(10 * MS, car, at(manager), "Close", ZERO)
check("no driver to aim at before the first write: nothing written", offset(manager) == ZERO)
car.DriverPawn = driver
manager.draw()
fresh.step(11 * MS, car, at(manager), "Close", ZERO)
kept = offset(manager)
manager.draw()
car.DriverPawn = None
fresh.step(12 * MS, car, at(manager), "Close", ZERO)
check("a driver unreadable for a frame keeps the last offset", kept != ZERO and offset(manager) == kept)
car.DriverPawn = driver
fresh.release()

far_driver = sdk_stubs.Driver()
far_driver.location = sdk_stubs.vector(100_000.0, 200.0, 170.0)
astray = sdk_stubs.Vehicle("OakVehicle_2", far_driver)
manager.draw()
try:
    camera_view.CameraView().step(13 * MS, astray, at(manager), "Close", ZERO)
    raised = False
except ValueError:
    raised = True
check("a target far away raises instead of throwing the camera, and writes nothing", raised and offset(manager) == ZERO)

manager.CameraModeState.CameraLocationOffset = Stuck()
try:
    camera_view.CameraView().step(14 * MS, car, at(manager), "Close", ZERO)
    refused = False
except RuntimeError:
    refused = True
check("an offset the game refuses raises", refused)
manager.CameraModeState.CameraLocationOffset = types.SimpleNamespace(X=0.0, Y=0.0, Z=0.0)

check("no camera manager: nothing to write", camera_view.CameraView().step(15 * MS, car, at(None), "Close", ZERO) == [])

gone = sdk_stubs.CameraManager()
held = camera_view.CameraView()
held.step(16 * MS, car, at(gone), "Close", ZERO)
sdk_stubs.destroy(gone)
check("a manager the game destroyed is never written again",
      held.release() == [] and gone.CameraModeState.CameraLocationOffset.X != 0.0)

summary = camera_view.CameraView()
watched = sdk_stubs.CameraManager()
lines: list[str] = []
for step in range(0, 5001, 50):
    watched.draw()
    lines += summary.step(step * MS, car, at(watched), "Close", ZERO)
check("a summary every 5 seconds a view writes, with the reticle's clearance over the top of the driver",
      len(lines) == 1 and lines[0].startswith("camera view=Close frames=101 ") and "target_below_mean=1.4" in lines[0]
      and isinstance(lines[0], report.Summary))
watched.draw()
check("another view starts its own count", summary.step(5050 * MS, car, at(watched), "Closer", ZERO) == [])

steady_manager = sdk_stubs.CameraManager()
counted = steady_manager.CameraModeState.CameraLocationOffset = CountedOffset()
steady = camera_view.CameraView()
steady.step(30_000 * MS, car, at(steady_manager), "Close", ZERO)
pointers = len(sdk_stubs.WeakPointer.made)
reads: list[int] = []
for number in range(1, 11):
    steady_manager.draw()
    before = counted.reads
    steady.step((30_000 + number) * MS, car, at(steady_manager), "Close", ZERO)
    reads.append(counted.reads - before)
check("a steady frame reads the offset once, to see whether the game drew the camera, not again after writing it",
      reads == [3] * 10 and near(offset(steady_manager), (120.0, 0.0, -3.0)))
check("the manager is held by one weak pointer from the first write, not a new one each frame",
      len(sdk_stubs.WeakPointer.made) == pointers)
steady.release()
check("no generator runs in the camera view at each frame",
      generators(camera_view.CameraView.step) == [] and generators(camera_view._same) == [])

from vehicle_driving import camera_share  # noqa: E402

check("no camera mod at the wheel: nothing to add", camera_share.framing() == ZERO)
shared = camera_view.CameraView()
pulled = sdk_stubs.CameraManager()
camera_share.publish((-80.0, 0.0, 0.0))
shared.step(20_000 * MS, car, at(pulled), "Default", ZERO)
check("the camera mods' framing is written on the game's own view, and the camera mods are told not to write",
      offset(pulled) == (-80.0, 0.0, 0.0) and camera_share.claimed())
pulled.draw()
shared.step(20_001 * MS, car, at(pulled), "Close", ZERO)
check("a view keeps its place and the framing adds to it", near(offset(pulled), (40.0, 0.0, -3.0)))
pulled.draw()
shared.step(20_002 * MS, car, at(pulled), "Close", ZERO)
check("drawn with both, the next frame writes the same: the zoom does not count the framing twice",
      near(offset(pulled), (40.0, 0.0, -3.0)))
pulled.draw()
shared.step(20_003 * MS, car, at(pulled), "Custom", (200.0, -30.0, 90.0))
check("Custom's sliders plus the framing", offset(pulled) == (120.0, -30.0, 90.0))
pulled.draw()
sys.modules[camera_share.SLOT].framing_ns = 1
shared.step(20_004 * MS, car, at(pulled), "Default", ZERO)
check("a framing from a frame long gone (camera mod switched off) is never added", offset(pulled) == ZERO)
shared.release()

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
