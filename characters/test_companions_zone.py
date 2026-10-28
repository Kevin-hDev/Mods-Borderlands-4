"""Tests a companion's zone (companions/zone.py): read with its owner, or why not; set on the hunter once he is
FOLLOW_M away, at most every FOLLOW_S, counted moved or refused, in a row, and away when the game moved it; put back
where it stood once moved; its radius made RADIUS_M with It Follows' patch, said first, written back once; a refused
write said, nothing to write back; a zone gone said."""

import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()
sys.modules["unrealsdk.unreal"].WeakPointer = lambda target: (lambda: None if target.gone else target)

from characters.companions import zone as zone_module  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


events: list[str] = []


class Zone:
    def __init__(self, at: tuple = (0.0, 0.0, 0.0)) -> None:
        self.gone, self.radius, self.at, self.holds = False, 1500.0, at, True
        self.Class, self.Name = types.SimpleNamespace(Name="GbxTerritoryComponent"), "Territory"

    def K2_GetComponentLocation(self) -> object:
        return types.SimpleNamespace(X=self.at[0], Y=self.at[1], Z=self.at[2])

    def K2_SetWorldLocation(self, NewLocation: object, bSweep: bool, SweepHitResult: object, bTeleport: bool) -> None:
        events.append(f"move {NewLocation.X} {bSweep} {bTeleport}")
        if self.holds:
            self.at = (NewLocation.X, NewLocation.Y, NewLocation.Z)

    def GetOwner(self) -> object:
        return types.SimpleNamespace(Class=types.SimpleNamespace(Name="OakSpawner"), Name="OakSpawner_7")


class Patch:
    refuse = False

    def __init__(self, cm: float) -> None:
        self.cm = cm
        events.append(f"patch {cm}")

    def apply(self, zone: Zone) -> float:
        if Patch.refuse:
            raise RuntimeError("territory write verification failed")
        self.before, zone.radius = zone.radius, self.cm
        return self.before

    def restore(self, zone: Zone) -> str:
        zone.radius = self.before
        return "restored"


check("followed every 2 s from 5 m; held within 5 m; placed within 1 m; widened to 40 m", (
      zone_module.FOLLOW_S, zone_module.FOLLOW_M, zone_module.HELD_M, zone_module.PLACED_CM, zone_module.RADIUS_M)
      == (2.0, 5.0, 5.0, 100.0, 40.0))
owned = Zone()
check("a zone read with its owner", zone_module.zone_of(types.SimpleNamespace(GetTerritory=lambda: owned)) == (
      owned, "GbxTerritoryComponent:Territory owned by OakSpawner:OakSpawner_7"))
check("no zone", zone_module.zone_of(types.SimpleNamespace(GetTerritory=lambda: None)) == (None, "none"))
check("a read that fails: why", zone_module.zone_of(types.SimpleNamespace(GetTerritory=lambda: 1 / 0)) == (
      None, "error:ZeroDivisionError:division by zero"))
orphan = Zone()
orphan.GetOwner = lambda: None
check("no owner", zone_module.zone_of(types.SimpleNamespace(GetTerritory=lambda: orphan))[1].endswith("owned by none"))
orphan.GetOwner = lambda: 1 / 0
check("an owner unread: why", zone_module.zone_of(types.SimpleNamespace(GetTerritory=lambda: orphan))[1].endswith(
      "owned by error:ZeroDivisionError"))
check("a place read, or None", zone_module.point(Zone((1.0, 2.0, 3.0))) == (1.0, 2.0, 3.0)
      and zone_module.point(object()) is None and zone_module.point(Zone((float("nan"), 0.0, 0.0))) is None)

zone = Zone((100.0, 0.0, 0.0))
held = zone_module.ZoneOnHunter(zone, lambda text: events.append(f"note {text}"))
check("never moved: nothing to put back", held.put_back() == "never_moved" and held.home == (100.0, 0.0, 0.0))
check("the hunter within 5 m: kept", held.follow((500.0, 0.0, 0.0), 10.0) == ("kept", (100.0, 0.0, 0.0)))
events.clear()
check("the hunter farther: moved onto him, said first, no sweep, teleported", held.follow((2000.0, 0.0, 0.0), 10.0)
      == ("moved", (2000.0, 0.0, 0.0)) and events == ["note about to call K2_SetWorldLocation on the zone (follow)",
                                                       "move 2000.0 False True"] and held.moves == 1)
check("within FOLLOW_S: waiting", held.follow((9000.0, 0.0, 0.0), 11.9)[0] == "waiting" and held.moves == 1)
zone.holds = False
check("not taken: counted refused, in a row", held.follow((9000.0, 0.0, 0.0), 12.0)[0] == "not_moved"
      and held.follow((20000.0, 0.0, 0.0), 14.0)[0] == "not_moved" and (held.refused, held.in_row) == (2, 2))
zone.holds = True
check("taken again: the row ends", held.follow((30000.0, 0.0, 0.0), 16.0)[0] == "moved" and held.in_row == 0)
away = held.away
held.follow((30000.0, 0.0, 0.0), 16.5)
check("where it was put: not away", held.away == away)
zone.at = (31000.0, 0.0, 0.0)
held.follow((30000.0, 0.0, 0.0), 16.6)
check("moved by the game beyond 5 m: counted away", held.away == away + 1)
check("the hunter unread: waiting", held.follow(None, 30.0)[0] == "waiting")
events.clear()
check("put back where it stood", held.put_back() == "restored" and zone.at == (100.0, 0.0, 0.0)
      and events == ["note about to call K2_SetWorldLocation on the zone (back)", "move 100.0 False True"])
zone.at, zone.holds = (5000.0, 0.0, 0.0), False
check("put back refused: said", held.put_back() == "restore_failed")
zone.K2_SetWorldLocation = lambda **k: 1 / 0
check("put back failing: said", held.put_back() == "restore_error:ZeroDivisionError")
zone.gone = True
check("the zone gone: unavailable, and waiting", held.put_back() == "unavailable"
      and held.follow((0.0, 0.0, 0.0), 99.0) == ("waiting", None))

patches = types.SimpleNamespace(TerritoryRadiusPatch=Patch)
zone = Zone()
held = zone_module.ZoneOnHunter(zone, lambda text: events.append(f"note {text}"))
check("never widened: nothing written back", held.narrow() == "not_widened")
events.clear()
check("widened to RADIUS_M, said first, the radius it had said", held.widen(patches) == "15.0->40.0"
      and zone.radius == 4000.0 and events == ["patch 4000.0", "note about to write the zone's combat radius 40.0 m"])
events.clear()
check("written back, said first", held.narrow() == "restored" and zone.radius == 1500.0
      and events == ["note about to write the zone's own combat radius back"])
check("written back once", held.narrow() == "not_widened")
Patch.refuse = True
check("a refused write said, nothing to write back", held.widen(patches) == "failed:RuntimeError"
      and held.narrow() == "not_widened")
Patch.refuse = False
held.widen(patches)
zone.gone = True
check("the zone gone: said", held.narrow() == "unavailable" and held.widen(patches) == "unavailable")

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
