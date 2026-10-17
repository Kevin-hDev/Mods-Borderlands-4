"""Tests guests.py through frame.py: on a co-op host, a guest's vehicle gets the host's values at once, on foot or at the
wheel, follows a moved slider at the next check, is gripped and pushed in the air as the player's own; the host's own
vehicle and a vehicle this game does not have authority on are left alone; the guns' damage formula is never written for
a guest; a guest out of the vehicle, a new vehicle and switching the mod off give the game's values back; a failure
costs that guest alone, said once."""

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

from vehicle_driving import frame, ground, guests, settings  # noqa: E402

MS = 1_000_000
ON_FOOT = types.SimpleNamespace(Pawn=types.SimpleNamespace(Name="OakCharacter_1"))


def vehicle(name: str, local: bool = False, role: str = "ROLE_Authority", yaw: float = 90.0) -> sdk_stubs.Vehicle:
    made = sdk_stubs.Vehicle(name, sdk_stubs.Driver(), yaw=yaw)
    made.IsLocallyControlled = lambda: local
    made.GetLocalRole = lambda: role
    return made


def jump(made: sdk_stubs.Vehicle) -> float:
    return made.OakVehicleMovement.HoverSetup.PowerslideJumpHeight.constant


def accel(made: sdk_stubs.Vehicle) -> float:
    return made.DriverPawn.VehicleDriverComponent.VehicleAttributesState.MaxAccel.BaseValue


def players(*pawns) -> None:
    state["players"][:] = [types.SimpleNamespace(PlayerId=number, PawnPrivate=pawn)
                           for number, pawn in enumerate(pawns, start=256)]


formula = state["formula"]
guest_car = vehicle("OakVehicle_Guest")
state["pc"] = ON_FOOT
players(types.SimpleNamespace(Name="OakCharacter_Host"), guest_car)
frame.on_frame(1000 * MS)
check("the host on foot: a guest's vehicle gets the host's values at once", jump(guest_car) == 330.0
      and accel(guest_car) == 2500.0)
check("said in the log, for that guest", any("co-op guest OakVehicle_Guest: driving OakVehicle_Guest" in line
                                             for line in state["misc"]))
check("the guns' damage formula is never asked for a guest", formula.calls == [])

settings.jump_height.value = 300
frame.on_frame(1200 * MS)
check("a moved slider waits for the next check", jump(guest_car) == 330.0)
frame.on_frame(1500 * MS)
check("and reaches the guest's vehicle at the check", jump(guest_car) == 495.0)
settings.jump_height.value = 200

guest_car.Mesh = sdk_stubs.Mesh(2290.0, 0.0)
frame.on_frame(1550 * MS)
check("a guest's vehicle turning at speed is gripped", len(guest_car.Mesh.sets) == 1)
guest_car.boosting = True
state["ground"].below = ground.TRACE_UP + 150.0
frame.on_frame(1600 * MS)
check("boosting off the ground it is pushed, and the grip rests that frame",
      len(guest_car.Mesh.impulses) == 1 and len(guest_car.Mesh.sets) == 1)
guest_car.boosting = False
state["ground"].below = 60.0

own = vehicle("OakVehicle_Host", local=True)
proxy = vehicle("OakVehicle_Other", role="ROLE_SimulatedProxy")
state["pc"] = types.SimpleNamespace(Pawn=own)
players(own, guest_car, proxy)
frame.on_frame(2000 * MS)
check("the host at the wheel: its own vehicle is the player's own, the guest's still the guest's",
      jump(own) == 330.0 and jump(guest_car) == 330.0 and len(guests._guests) == 1)
check("a vehicle this game has no authority on is left alone", jump(proxy) == 165.0)

players(own, types.SimpleNamespace(Name="OakCharacter_Guest"), proxy)
frame.on_frame(2100 * MS)
check("the guest out of its vehicle: the game's values back", jump(guest_car) == 165.0 and accel(guest_car) == 1000.0
      and guests._guests == {})

second = vehicle("OakVehicle_Guest2")
players(own, guest_car, proxy)
frame.on_frame(2200 * MS)
players(own, second, proxy)
frame.on_frame(2300 * MS)
check("a new vehicle: the old one given back, the new one held", jump(guest_car) == 165.0 and jump(second) == 330.0)

broken = vehicle("OakVehicle_Broken")
broken.OakVehicleMovement.IsBoosting = lambda: (_ for _ in ()).throw(RuntimeError("no boost"))
players(own, second, broken)
frame.on_frame(2400 * MS)
frame.on_frame(2450 * MS)
said = [line for line in state["errors"] if "co-op guest's vehicle stopped being driven" in line]
check("a failure costs that guest alone, said once", len(said) == 1 and jump(second) == 330.0
      and guests._guests[258].failed and not guests._guests[257].failed)

frame.stop_all()
check("switching the mod off gives every guest's vehicle its values back", jump(second) == 165.0
      and jump(broken) == 165.0 and guests._guests == {})

# On a guest's game: its own vehicle is the host's to move. The driver's attributes the host writes come back there;
# written again they were multiplied twice (trial 2): they are left to the host, the vehicle's own values written.
mine = vehicle("OakVehicle_Mine", local=True, role="ROLE_AutonomousProxy")
state["pc"] = types.SimpleNamespace(Pawn=mine)
players(mine)
frame.on_frame(3000 * MS)
check("a guest's own vehicle: its own values written, the driver's left to the host",
      jump(mine) == 330.0 and accel(mine) == 1000.0 and guests._guests == {}
      and any("the driver's speed, acceleration, reverse and boost come from the host" in line for line in state["misc"]))
state["pc"] = ON_FOOT
frame.on_frame(3100 * MS)
check("and given back as they were", jump(mine) == 165.0 and accel(mine) == 1000.0)

state["players"][:] = [types.SimpleNamespace(PlayerId=n, PawnPrivate=vehicle(f"OakVehicle_{n}")) for n in range(20)]
frame.on_frame(5000 * MS)
check("the guests followed are bounded", len(guests._guests) == guests.MAX_GUESTS)
frame.stop_all()

state["players"][:] = []
mods_base = sys.modules["mods_base"]
engine, mods_base.ENGINE = mods_base.ENGINE, None
frame.on_frame(6000 * MS)
check("a lookup that fails leaves the guests to the game, said once, and the player's own frame goes on",
      any("co-op guests' vehicles left to the game" in line for line in state["errors"]))
mods_base.ENGINE = engine

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
