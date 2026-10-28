"""Tests Omni Sprint's own copy of the open sprint: off while the shared runtime has the omni direction unit, on when
the runtime is an older copy without it or refused this mod, said once, synced with Omni Sprint's settings only, and
stopped when the shared runtime can do it again."""

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

from omni_sprint import camera, sprint_fallback  # noqa: E402


class Unit:
    made: list["Unit"] = []

    def __init__(self, load, identifier) -> None:
        self.identifier, self.synced, self.stopped = identifier, [], False
        Unit.made.append(self)

    def sync(self, clients, settings, pc, controller, now_ns) -> None:
        self.synced.append((tuple(client.settings for client in clients), settings, pc, controller))

    def stop(self) -> None:
        self.stopped = True


sprint_fallback.omni_direction = types.SimpleNamespace(OmniDirection=Unit, game_modules=None)
pc = object()
camera._registered, camera._runtime = True, types.SimpleNamespace(omni=object())
sprint_fallback.tick(pc, 0)
check("with the shared runtime's unit, its own copy stays off", Unit.made == [])
camera._runtime = types.SimpleNamespace()
sprint_fallback.tick(pc, 1)
sprint_fallback.tick(pc, 2)
unit = Unit.made[0] if Unit.made else None
check("a runtime from an older copy: its own copy starts once, under its own hook name, and says so",
      len(Unit.made) == 1 and unit.identifier == "omni_sprint:omni_direction"
      and state["misc"].count("[Omni Sprint] shared camera runtime without the open sprint: Omni Sprint opens it on "
                              "its own") == 1)
check("synced with Omni Sprint's settings only, the player, and no camera controller: the body is never turned",
      unit.synced[-1] == ((camera.ADAPTER,), camera.ADAPTER, pc, None))
camera._runtime = types.SimpleNamespace(omni=object())
sprint_fallback.tick(pc, 3)
check("the shared runtime able again, its own copy stops", unit.stopped and sprint_fallback._unit is None)
camera._registered, camera._runtime = False, None
sprint_fallback.tick(pc, 4)
check("a refused camera: its own copy runs too", len(Unit.made) == 2)
sprint_fallback.stop()
sprint_fallback.stop()
check("stopping twice is safe", Unit.made[1].stopped and sprint_fallback._unit is None)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
