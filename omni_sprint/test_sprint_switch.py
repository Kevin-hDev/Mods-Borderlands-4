"""The sprint's own switch (Kevin, 2026-09-25): off, the game's limit and backward animation come back while the
camera keeps its checks; on again, the sprint opens again."""

import pathlib
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


state = sdk_stubs.install()

from omni_sprint import animation, camera, definition, frame, memory, settings  # noqa: E402

fake = sdk_stubs.FakeMemory()
sdk_stubs.patch_memory(memory, fake)
COMPONENT, SIREN = sdk_stubs.BASE + 0x1000, sdk_stubs.BASE + 0x20000
fake.put_definition(SIREN, definition.KNOWN)
fake.put_pointer(COMPONENT + 0x1CF0, SIREN)
state["pc"] = sdk_stubs.player(COMPONENT)
MS = 1_000_000
now = 1_000 * MS


def step() -> None:
    global now
    now += 500 * MS
    frame.on_frame(now)


def angle() -> float:
    return fake.get_float(SIREN + 580)


frame.reset()
check("switched on by default, the sprint opens", settings.sprint_enabled() and (step(), angle())[1] == 180.0)
settings.omni_sprint.value = False
step()
check("switched off, the game's limit is back at the next check and the log says so",
      angle() == 60.0 and state["misc"][-1].endswith("sprint switched off, game sprint limit put back in 1 movement "
                                                     "definition(s)"))
writes = fake.writes
step()
check("off, nothing more is written", fake.writes == writes and angle() == 60.0)
state["pc"] = None
step()
state["pc"] = sdk_stubs.player(COMPONENT)
check("off, the player's presence is still followed for the camera", frame._player_present is False)

calls = []
animation.inspect = lambda _obj: (True, None, None)
animation.update = lambda _frame, _now: calls.append("update")
animation.stop = lambda: calls.append("stop")
camera.on_frame = lambda _now: calls.append("camera")
frame.tick(object(), None, None, None)
check("off, the backward animation is released and the camera still runs", calls == ["stop", "camera"])
settings.omni_sprint.value = True
calls.clear()
frame.tick(object(), None, None, None)
now = time.perf_counter_ns()  # tick reads the real clock: the next check follows it.
step()
check("switched on again, the backward animation runs and the sprint opens again",
      calls[:2] == ["update", "camera"] and angle() == 180.0)
settings.omni_sprint.value = "yes"
check("only an explicit off turns the sprint off", settings.sprint_enabled())

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
