"""Tests the co-op guests: on the host only, every guest on foot gets the values the switched-on movements want, the
game's own are put back when a movement goes off or the mod stops, and a guest who leaves is forgotten."""

import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

from apex_movement import camera_settings, frame, guests, settings  # noqa: E402

# Movement isolation: native loot lifecycle has its own tests.
camera_settings.loot.enabled.value = False

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


S = guests.REFRESH_NS


def seat(*characters: object) -> None:
    state["players"][:] = [types.SimpleNamespace(Name=f"State{index}", PawnPrivate=character)
                           for index, character in enumerate(characters)]


def lines() -> list[str]:
    return [line for line in state["misc"] if "co-op guest" in line]


def wanted(fields: dict) -> guests.Wanted:
    return lambda guest: dict(fields)


host = sdk_stubs.FakeCharacter(name="Host")
guest = sdk_stubs.FakeCharacter(name="Guest", local=False)
seat(host, guest)
moved = guest.CharacterMovement

# 1. Only the host writes on a guest, and only on a guest.
seat(host)
guests.update(host, 0, wanted({"GravityScale": 2.0}))
check("a game without a guest writes nothing", host.CharacterMovement.GravityScale == 1.0 and not lines())

seat(sdk_stubs.FakeCharacter(name="Me", role="ROLE_AutonomousProxy"), sdk_stubs.FakeCharacter(
    name="TheHost", role="ROLE_SimulatedProxy", local=False))
me = state["players"][0].PawnPrivate
guests.update(me, S, wanted({"GravityScale": 2.0}))
check("a guest's game writes on nobody", state["players"][1].PawnPrivate.CharacterMovement.GravityScale == 1.0
      and not lines())

seat(host, guest)
guests.update(host, 2 * S, wanted({"GravityScale": 2.0, "GlidingSpeed": (1560.0, 1560.0)}))
check("the host writes the wanted values on the guest", moved.GravityScale == 2.0)
check("an attribute pair gets both its fields", (moved.GlidingSpeed.BaseValue, moved.GlidingSpeed.Value)
      == (1560.0, 1560.0))
check("the host's own character is left alone", host.CharacterMovement.GravityScale == 1.0)
check("the guest's arrival is said", any("Guest: the host applies" in line for line in lines()))
said = len(lines())
guests.update(host, 2 * S + 1, wanted({"GravityScale": 2.0, "GlidingSpeed": (1560.0, 1560.0)}))
check("an unchanged frame says nothing", len(lines()) == said)

# 2. The game's values are kept and handed to the movements.
seen: dict = {}


def read_game(guest: guests.GuestFrame) -> dict:
    seen["gravity"], seen["glide"] = guest.game_value("GravityScale"), guest.game_value("GlidingSpeed")
    seen["frame"] = (guest.character, guest.now_ns)
    return {"GravityScale": 2.0, "GlidingSpeed": (1560.0, 1560.0)}


guests.update(host, 2 * S + 2, read_game)
check("a movement reads the game's own value, not the one written", seen["gravity"] == 1.0
      and seen["glide"] == (1200.0, 1200.0))
check("and is told which guest and which frame", seen["frame"] == (guest, 2 * S + 2))

# 2b. Each guest keeps a notebook of its own from frame to frame, for movements that follow it.


def count_frames(frame: guests.GuestFrame) -> dict:
    frame.memo["frames"] = frame.memo.get("frames", 0) + 1
    return {"GravityScale": 2.0}


guests.update(host, 2 * S + 2, count_frames)
guests.update(host, 2 * S + 2, count_frames)
check("a guest's notebook is kept from frame to frame", guests._guests[0].memo["frames"] == 2)

# 2c. One float of a struct: written alone, the rest of the struct left to the game, and given back.
guests.update(host, 2 * S + 2, wanted({"GravityScale": 2.0, "MaxGroundSpeedScale.Value": 0.8}))
check("one float of a struct is written alone", moved.MaxGroundSpeedScale.Value == 0.8)
guests.update(host, 2 * S + 2, wanted({"GravityScale": 2.0}))
check("and given back when no longer wanted", moved.MaxGroundSpeedScale.Value == 1.15)
guests.update(host, 2 * S + 2, wanted({"GravityScale": 2.0, "bServerAcceptClientAuthoritativePosition": True}))
check("a switch is turned on", moved.bServerAcceptClientAuthoritativePosition is True)
guests.update(host, 2 * S + 2, wanted({"GravityScale": 2.0, "bServerAcceptClientAuthoritativePosition": True}))
check("a switch already on is not written or said again",
      sum("bServerAcceptClientAuthoritativePosition True" in line for line in lines()) == 1)
guests.update(host, 2 * S + 2, wanted({"GravityScale": 2.0}))
check("and given back off, as a switch", moved.bServerAcceptClientAuthoritativePosition is False)

# 3. A field no movement wants any more gets the game's value back.
guests.update(host, 2 * S + 3, wanted({"GravityScale": 2.0}))
check("a field no longer wanted is put back", (moved.GlidingSpeed.BaseValue, moved.GlidingSpeed.Value)
      == (1200.0, 1200.0) and moved.GravityScale == 2.0)
check("its return is said", any("GlidingSpeed back to the game's" in line for line in lines()))

# 4. The game taking a value back is written over at the next frame.
moved.GravityScale = 1.0
guests.update(host, 2 * S + 4, wanted({"GravityScale": 2.0}))
check("a value the game took back is written again", moved.GravityScale == 2.0)

# 5. The player list is read once a second.
late = sdk_stubs.FakeCharacter(name="Late", local=False)
seat(host, guest, late)
guests.update(host, 2 * S + 5, wanted({"GravityScale": 2.0}))
check("a guest who just arrived waits for the next look", late.CharacterMovement.GravityScale == 1.0)
guests.update(host, 3 * S, wanted({"GravityScale": 2.0}))
check("and gets the values at the next look", late.CharacterMovement.GravityScale == 2.0)

# 6. A guest in a vehicle is skipped and keeps what was written; back on foot, followed again.
vehicle = types.SimpleNamespace(Name="Vehicle", IsLocallyControlled=lambda: False)
seat(host, vehicle, late)
guests.update(host, 4 * S, wanted({"GravityScale": 3.0}))
check("a guest in a vehicle is skipped", moved.GravityScale == 2.0 and late.CharacterMovement.GravityScale == 3.0)
seat(host, guest, late)
guests.update(host, 5 * S, wanted({"GravityScale": 3.0}))
check("back on foot, followed again", moved.GravityScale == 3.0)

# 7. A guest who leaves is forgotten: nothing is written into a destroyed character.
sdk_stubs.destroy(late)
seat(host, guest)
guests.update(host, 6 * S, wanted({"GravityScale": 3.0}))
check("a guest gone is forgotten and said", len(guests._guests) == 1 and any("Late gone" in line for line in lines()))

# 8. Bounded: never more guests than the game takes players.
crowd = [sdk_stubs.FakeCharacter(name=f"Crowd{index}", local=False) for index in range(guests.MAX_PLAYERS + 2)]
state["players"][:] = [types.SimpleNamespace(PawnPrivate=character) for character in [host, *crowd]]
guests.update(host, 7 * S, wanted({"GravityScale": 3.0}))
check("no more guests are followed than the game takes players", len(guests._guests) <= guests.MAX_PLAYERS)

# 9. Stopping puts every guest's values back and forgets them.
check("nothing fails to come back", guests.give_back_all() == [])
check("the guest has the game's values again", moved.GravityScale == 1.0 and not guests._guests)

# 10. Bounded lines: a value written every frame cannot fill the log, nor can the fields all together.
seat(host, guest)
for step in range(guests.MAX_FIELD_LINES + 20):
    moved.GravityScale = 1.0
    guests.update(host, 8 * S + step, wanted({"GravityScale": 2.0}))
check("a field written every frame stops at its own bound, the last line saying so",
      sum("GravityScale 2.0" in line for line in state["misc"][-guests.MAX_FIELD_LINES - 5:]) == guests.MAX_FIELD_LINES
      and "last line for this field" in state["misc"][-1])
for step in range(guests.MAX_LINES):
    setattr(moved, f"Field{step}", -1.0)
for step in range(guests.MAX_LINES):
    guests.update(host, 9 * S + step, wanted({"GravityScale": 2.0, f"Field{step}": float(step)}))
check("all the fields together stop at the bound, the last line saying so", guests._lines == guests.MAX_LINES
      and "last co-op line" in state["misc"][-1])
guests.give_back_all()
state["misc"].clear()

# 11. Through the frame loop, with the real movements and their switches.
for switch in (settings.glide, settings.air_strafe, settings.heavier_fall):
    switch.value = True
sdk_stubs.use_character(state, host)
seat(host, guest)
frame.on_frame(host.anim, 10 * S)
frame.on_frame(host.anim, 10 * S + 1)
check("the guest gets the walk speed", moved.MinAnalogWalkSpeed == float(settings.walk_speed.value))
check("the guest gets the air strafe", moved.MaxAcceleration == float(settings.air_acceleration.value)
      and moved.AirControl == 20.0)
check("the guest gets the heavier fall", moved.GravityScale == float(settings.fall_weight.value))
factor = float(settings.glide_speed.value) / 100.0
check("the guest gets the faster glide from its own game value",
      abs(moved.GlidingSpeed.BaseValue - 1200.0 * factor) < 0.01)
moved.bIsSprinting = True
frame.on_frame(host.anim, 10 * S + 2)
check("a sprinting guest gets the sprint speed", moved.MinAnalogWalkSpeed == float(settings.sprint_speed.value))

moved.bIsSprinting = False
asset = sdk_stubs.slide_asset(state)
moved.ControlledMoveReplicationData.ControlledMove = asset
moved.Velocity = sdk_stubs.vector(1100.0, 0.0)
frame.on_frame(host.anim, 10 * S + 2 + 50_000_000)
first = moved.MaxGroundSpeedScale.Value
frame.on_frame(host.anim, 10 * S + 2 + 550_000_000)
unit = asset.speed.constant * 1.1017
check("a sliding guest starts at the slide speed through its own scale",
      abs(first * unit - float(settings.slide_speed.value)) < 0.5)
check("and the host slows it down as the guest's game does", moved.MaxGroundSpeedScale.Value < first)
check("the host's own scale is left alone", host.CharacterMovement.MaxGroundSpeedScale.Value == 1.15)
moved.ControlledMoveReplicationData.ControlledMove = None
frame.on_frame(host.anim, 10 * S + 2 + 600_000_000)
check("the slide over, the guest gets the game's scale back", moved.MaxGroundSpeedScale.Value == 1.15
      and "slide" not in guests._guests[0].memo)

settings.heavier_fall.value = False
frame.on_frame(host.anim, 11 * S + 3)
check("a movement switched off gives the guest the game's value back", moved.GravityScale == 1.0
      and moved.AirControl == 20.0)
settings.heavier_fall.value = True

frame.on_frame(host.anim, 11 * S + 4)
frame.stop_all()
check("stopping the mod gives the guest every game value back", moved.GravityScale == 1.0
      and moved.MaxAcceleration == 2048.0 and moved.AirControl == 0.6 and moved.GlidingSpeed.BaseValue == 1200.0)

# 12. A failure leaves the guests to the game, alone: the player's movements go on.
state["errors"].clear()
original_look = guests._look
guests._look = lambda player: (_ for _ in ()).throw(RuntimeError("no game state"))
frame.on_frame(host.anim, 20 * S)
frame.on_frame(host.anim, 21 * S)
check("a guest failure is reported once", sum("co-op guests" in line for line in state["errors"]) == 1)
check("the player's own movements go on", host.CharacterMovement.AirControl == 20.0)
guests._look = original_look
frame.stop_all()

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
