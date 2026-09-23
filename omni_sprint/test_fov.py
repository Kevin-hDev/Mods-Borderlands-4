"""Tests the FOV option: nothing written while it is off, the FOV set and kept, a value the game put back set again
and kept as the game's, a change of the slider not taken for the game's, a slider past its bounds held in them, the
game's value given back when the option goes off, and stopping."""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


state = sdk_stubs.install()

from omni_sprint import fov, settings  # noqa: E402

MS = 1_000_000
now = 1_000 * MS


def step(ms: int = 500) -> None:
    global now
    now += ms * MS
    fov.on_frame(now)


def notes() -> list[str]:
    return [line.removeprefix("[Omni Sprint] ") for line in state["misc"]]


fov.reset()
step()
check("without a player nothing happens", state["misc"] == [])

pc = sdk_stubs.player(sdk_stubs.BASE, fov=90.0)
state["pc"] = pc
step()
check("the option off: nothing is written", pc.Player.BaseFOV == 90.0 and state["misc"] == [])

settings.custom_fov.value = True
settings.fov.value = 150
step(100)
check("a tick before the next check does nothing", pc.Player.BaseFOV == 90.0)
step(400)
check("the FOV is set, and the game's is said", pc.Player.BaseFOV == 150.0 and notes() == ["FOV set to 150, game's 90"])
step()
check("a FOV already set is not written again", len(notes()) == 1)
pc.Player.BaseFOV = 100.0
step()
check("a FOV the game put back is set again, its value kept as the game's",
      pc.Player.BaseFOV == 150.0 and notes()[-1] == "FOV found at the game's 100, set to 150 again")
settings.fov.value = 120
step()
check("a change of the slider is applied", pc.Player.BaseFOV == 120.0 and notes()[-1] == "FOV set to 120")
settings.fov.value = 400
step()
check("a slider past its bounds is held in them", pc.Player.BaseFOV == 150.0)
settings.custom_fov.value = False
step()
check("the option off gives back the game's last value, not the slider's old one",
      pc.Player.BaseFOV == 100.0 and notes()[-1] == "FOV given back to the game's 100")
count = len(notes())
step()
check("and gives it back only once", pc.Player.BaseFOV == 100.0 and len(notes()) == count)

pc.Player.BaseFOV = 90.0
settings.custom_fov.value = True
settings.fov.value = 90
step()
check("a slider equal to the game's writes nothing", pc.Player.BaseFOV == 90.0 and len(notes()) == count)

settings.fov.value = 130
step()
fov.stop()
check("stopping gives the game its FOV back", pc.Player.BaseFOV == 90.0)
step()
check("stopping forgets the FOV: the next switch-on sets it again", pc.Player.BaseFOV == 130.0)
settings.custom_fov.value = False

fov.reset()
pc = sdk_stubs.player(sdk_stubs.BASE, fov=90.0)
state["pc"] = pc
settings.custom_fov.value = True
settings.fov.value = 150
step()
pc.Player.BaseFOV = 105.0
settings.custom_fov.value = False
step()
check("switching off leaves a newer FOV from another owner alone", pc.Player.BaseFOV == 105.0)

fov.reset()
first = sdk_stubs.player(sdk_stubs.BASE, fov=90.0)
second = sdk_stubs.player(sdk_stubs.BASE + 0x1000, fov=100.0)
state["pc"] = first
settings.custom_fov.value = True
step()
state["pc"] = second
step()
check("changing player restores the first and uses the second's own FOV",
      first.Player.BaseFOV == 90.0 and second.Player.BaseFOV == 150.0)
settings.custom_fov.value = False
step()
check("switching off restores only the second player's FOV", second.Player.BaseFOV == 100.0)

fov.reset()
state["pc"] = first
settings.custom_fov.value = True
step()
state["pc"] = None
fov.stop()
check("stopping at the title restores the still-live former player", first.Player.BaseFOV == 90.0)

fov.reset()
state["pc"] = first
settings.custom_fov.value = "False"
step()
check("a malformed switch does not enable custom FOV", first.Player.BaseFOV == 90.0)
settings.custom_fov.value = False
settings.fov.value = "999"
try:
    malformed_fov = settings.fov_value()
except (TypeError, ValueError):
    malformed_fov = None
check("a malformed slider falls back to its default", malformed_fov == 110.0)
settings.fov.value = float("nan")
check("a non-finite slider falls back to its default", settings.fov_value() == 110.0)


class RestoreFailurePlayer(sdk_stubs.FakePlayer):
    def __init__(self) -> None:
        self.block_restore = False
        self._fov = 90.0

    @property
    def BaseFOV(self) -> float:
        return self._fov

    @BaseFOV.setter
    def BaseFOV(self, value: float) -> None:
        if self.block_restore and value == 90.0:
            raise ValueError("temporary test failure")
        self._fov = value


fov.reset()
pc = sdk_stubs.player(sdk_stubs.BASE)
pc.Player = RestoreFailurePlayer()
state["pc"] = pc
settings.custom_fov.value = True
settings.fov.value = 150
mod = state["mods"][0]
mod.enable()
step()
pc.Player.block_restore = True
mod.disable()
check("a failed restoration keeps the custom FOV pending", pc.Player.BaseFOV == 150.0)
pc.Player.block_restore = False
mod.enable()
mod.disable()
check("a later disable retries the pending restoration", pc.Player.BaseFOV == 90.0)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
