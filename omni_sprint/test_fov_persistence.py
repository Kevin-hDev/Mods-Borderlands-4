"""The native FOV survives menu transitions and a later mod switch-off."""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

from omni_sprint import camera, settings  # noqa: E402

failures: list[str] = []
time_ns = 1_000_000_000


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        failures.append(label)


def step() -> None:
    global time_ns
    time_ns += 500_000_000
    camera.on_frame(time_ns)


settings.custom_fov.value = True
settings.fov.value = 140
first = sdk_stubs.player(sdk_stubs.BASE, fov=103.0)
state["pc"] = first
step()
check("the native value is recorded before the mod applies", first.Player.BaseFOV == 140
      and settings.native_fov.value == 103.0 and settings.applied_fov.value == 140.0
      and state["settings_saves"] > 0)

# The game's profile may reintroduce the mod's angle before the new player loads.
camera.stop()
camera.start()
state["pc"] = sdk_stubs.player(sdk_stubs.BASE + 0x1000, fov=140.0)
step()
settings.custom_fov.value = False
step()
check("switching off after a reload restores the actual native value",
      state["pc"].Player.BaseFOV == 103.0)

# A native menu change must become the new baseline, not the stale saved one.
settings.custom_fov.value = True
state["pc"].Player.BaseFOV = 98.0
step()
check("a new native choice replaces the stored baseline",
      state["pc"].Player.BaseFOV == 140.0 and settings.native_fov.value == 98.0)
settings.custom_fov.value = False
step()
check("switching off returns the new native choice", state["pc"].Player.BaseFOV == 98.0)

camera.stop()
camera.start()
state["pc"] = sdk_stubs.player(sdk_stubs.BASE + 0x2000, fov=140.0)
step()
check("an already disabled option recovers the saved native value on load",
      state["pc"].Player.BaseFOV == 98.0)

camera.stop()
camera.start()
settings.custom_fov.value = True
state["pc"] = sdk_stubs.player(sdk_stubs.BASE + 0x3000, fov=95.0)
old_pair = settings.saved_fov_pair()
mod = settings.native_fov.mod
old_save = mod.save_settings


def reject_save() -> None:
    raise OSError("simulated settings write failure")


mod.save_settings = reject_save
try:
    step()
except OSError:
    pass
check("a failed backup blocks the FOV write", state["pc"].Player.BaseFOV == 95.0
      and settings.saved_fov_pair() == old_pair)
mod.save_settings = old_save
settings.custom_fov.value = False

camera.stop()
camera.start()
settings.native_fov.value = 90.0
settings.applied_fov.value = 100.0
settings.fov.value = 100.0
settings.custom_fov.value = True
state["pc"] = sdk_stubs.player(sdk_stubs.BASE + 0x4000, fov=100.0)
step()
settings.custom_fov.value = False
step()
check("an angle inside the native menu range is not falsely claimed after reload",
      state["pc"].Player.BaseFOV == 100.0)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not failures else f"{len(failures)} ECHEC(S)")
sys.exit(1 if failures else 0)
