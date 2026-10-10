"""The sprint's own switch (Kevin, 2026-09-25): off, the shared runtime gives the game's limit back while the
camera keeps its checks; on again, the sprint opens again."""

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


state = sdk_stubs.install()

from omni_sprint import camera, frame, settings  # noqa: E402
from apex_camera_runtime import movement_definition as definition  # noqa: E402

fake = sdk_stubs.FakeMemory()
sdk_stubs.patch(fake)
COMPONENT, SIREN = sdk_stubs.BASE + 0x1000, sdk_stubs.BASE + 0x20000
fake.put_definition(SIREN, definition.KNOWN)
fake.put_pointer(COMPONENT + 0x1CF0, SIREN)
state["pc"] = sdk_stubs.player(COMPONENT)
MS = 1_000_000
clock = [1_000 * MS]
# The runtime keeps the limit twice a second on the frame's clock: the test moves that clock half a second a step.
frame.time = types.SimpleNamespace(perf_counter_ns=lambda: clock[0])


def step() -> None:
    clock[0] += 500 * MS
    frame.tick(sdk_stubs.body(state["pc"]), None, None, None)


def angle() -> float:
    return fake.get_float(SIREN + 580)


frame.reset()
check("switched on by default, the sprint opens", settings.sprint_enabled() and (step(), angle())[1] == 180.0)
settings.omni_sprint.value = False
step()
check("switched off, the game's limit is back at the next check and the log says so",
      angle() == 60.0 and state["misc"][-1].endswith("open sprint no longer asked, game sprint limit put back in 1 "
                                                     "movement definition(s)"))
writes = fake.writes
step()
check("off, nothing more is written", fake.writes == writes and angle() == 60.0)
settings.omni_sprint.value = True
step()
check("switched on again, the sprint opens again", angle() == 180.0)
settings.omni_sprint.value = "yes"
check("only an explicit off turns the sprint off", settings.sprint_enabled())
camera.stop()

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
