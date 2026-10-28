"""Tests the wall climb a co-op host plays for each guest: the stick read from the guest's acceleration, the climb
pushing the guest up the wall like the player's own, the host trusting the guest's place during it, its end, its
jumps given back, one climber per guest started
over when stale, the bounded lines, and the frame loop handing every guest to it."""

import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

from apex_movement import camera_settings, climber, frame, guest_trust, guests, settings, wall_climb  # noqa: E402

# Movement isolation: native loot lifecycle has its own tests.
camera_settings.loot.enabled.value = False

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def notes(text: str) -> int:
    return sum(text in line for line in state["misc"])


MS = 1_000_000
S = 1_000_000_000
kismet = state["kismet"]
host = sdk_stubs.FakeCharacter(name="Host")
guest = sdk_stubs.FakeCharacter(name="Guest", local=False)
moved = guest.CharacterMovement
memo: dict = {}


def frame_of(now_ns: int) -> guests.GuestFrame:
    return guests.GuestFrame(guest, now_ns, lambda field: None, memo)


# 1. The stick as the host knows it.
moved.MaxAcceleration = 24000.0
moved.acceleration = sdk_stubs.vector(24000.0, 0.0)
check("pushed fully, the guest's acceleration reads as the stick pushed fully", climber.remote_stick(guest) == (1.0, 0.0))
moved.acceleration = sdk_stubs.vector(0.0, 0.0)
check("let go, it reads as the stick let go", climber.remote_stick(guest) == (0.0, 0.0))
moved.acceleration = sdk_stubs.vector(30000.0, 40000.0)
stick = climber.remote_stick(guest)
check("never longer than a stick pushed fully", abs(stick[0] - 0.6) < 1e-9 and abs(stick[1] - 0.8) < 1e-9)
moved.MaxAcceleration = 0.0
check("no acceleration allowed, no stick", climber.remote_stick(guest) == (0.0, 0.0))
moved.MaxAcceleration = 24000.0

# 2. A guest jumping at a wall, stick and camera toward it, climbs on the host.
moved.MovementMode = sdk_stubs.Mode("MOVE_Falling")
kismet.hit = (120.0, sdk_stubs.vector(-1.0, 0.0, 0.0))
moved.acceleration = sdk_stubs.vector(24000.0, 0.0)
guest.JumpCurrentCount = 2
check("climbing, the host takes the guest's place", wall_climb.for_guest(frame_of(20 * MS)) == guest_trust.SWITCHES)
check("the guest climbs: up and into the wall, like the player",
      (moved.Velocity.X, moved.Velocity.Y, moved.Velocity.Z) == (100.0, 0.0, 370.0))
check("though the input the player's climb reads stays empty on the host", guest.input.X == 0.0 and guest.input.Y == 0.0)
check("the start is said with the guest's name", notes("co-op guest Guest: wall climb start z=100") == 1)
check("the host's own character is left alone", host.CharacterMovement.Velocity.Z == 0.0)
wall_climb.for_guest(frame_of(30 * MS))
check("the climb gives the guest's jumps back, as a landing",
      guest.JumpCurrentCount == 1 and moved.JumpedCount == 1)
moved.Velocity = sdk_stubs.vector(0.0, 0.0, 0.0)
wall_climb.for_guest(frame_of(40 * MS))
check("the push is written every frame of the climb", moved.Velocity.Z == 370.0)

# 3. The stick let go past its grace ends the climb, which waits before the next.
moved.acceleration = sdk_stubs.vector(0.0, 0.0)
wall_climb.for_guest(frame_of(50 * MS))
wall_climb.for_guest(frame_of(800 * MS))
check("the stick let go past its grace ends the guest's climb", notes("co-op guest Guest: wall climb end reason=stick") == 1)
check("after its end, the guest still in the air, the host still takes its place",
      wall_climb.for_guest(frame_of(805 * MS)) == guest_trust.SWITCHES)
moved.Velocity = sdk_stubs.vector(0.0, 0.0, -100.0)
moved.acceleration = sdk_stubs.vector(24000.0, 0.0)
wall_climb.for_guest(frame_of(810 * MS))
check("a climb that ended short waits before the next, like the player's", moved.Velocity.Z == -100.0)

# 4. A climber left without frames starts over: no climb carried from long ago.
kept = memo["climb"]
wall_climb.for_guest(frame_of(810 * MS + 2 * S))
check("a stale climber starts over", memo["climb"] is not kept)

# 5. Bounded lines.
wall_climb._guest_lines = wall_climb.MAX_GUEST_LINES
said = notes("co-op guest Guest: wall climb")
moved.MovementMode = sdk_stubs.Mode("MOVE_Walking")
wall_climb.for_guest(frame_of(810 * MS + 2 * S + 10 * MS))
moved.MovementMode = sdk_stubs.Mode("MOVE_Falling")
memo.clear()
wall_climb.for_guest(frame_of(900 * MS + 3 * S))
check("past the bound a guest's climbs are no longer said", notes("co-op guest Guest: wall climb") == said)
wall_climb.stop(None)
check("switching the climb off and on gives the lines back", wall_climb._guest_lines == 0)

# 6. Through the frame loop, the host's wall climb switched on.
settings.wall_climb.value = True
sdk_stubs.use_character(state, host)
state["players"][:] = [types.SimpleNamespace(PawnPrivate=host), types.SimpleNamespace(PawnPrivate=guest)]
moved.Velocity = sdk_stubs.vector(0.0, 0.0, 0.0)
moved.acceleration = sdk_stubs.vector(24000.0, 0.0)
frame.on_frame(host.anim, 10 * S)
frame.on_frame(host.anim, 10 * S + 10 * MS)
check("the frame loop hands the guest to the climb", moved.Velocity.Z == 370.0)
check("and the host trusts the climbing guest's place",
      moved.bIgnoreClientMovementErrorChecksAndCorrection is True and moved.bServerAcceptClientAuthoritativePosition is True)
settings.wall_climb.value = False
moved.Velocity = sdk_stubs.vector(0.0, 0.0, 0.0)
frame.on_frame(host.anim, 10 * S + 20 * MS)
check("with the climb switched off on the host, the guest is not pushed", moved.Velocity.Z == 0.0)
check("and the host corrects the guest again, the switches given back as switches",
      moved.bIgnoreClientMovementErrorChecksAndCorrection is False and moved.bServerAcceptClientAuthoritativePosition is False)
frame.stop_all()

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
