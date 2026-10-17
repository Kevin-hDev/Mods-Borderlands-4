"""Tests Apex Grapple in co-op: a guest's rope told to the host when it goes and when it lets go, the game's own point
sent back after each message, nothing sent solo; on the host, a guest's message kept from the game and the same pull
played on the guest's character, from the way it was told, until the guest lets go, lands or is gone; the guests'
ropes bounded and apart from the player's own."""

import math
import types

from grapple_fixture import SECOND, check, fails, fresh, game, sdk_stubs, settings, state
from apex_grapple import coop_code, coop_host, coop_link, frame, remote_ropes

import sys

MS = 1_000_000


def sends_of(pc) -> list:
    return pc.sent


def wire(pc) -> None:
    """The guest's controller: each send goes through the hooked function, as the game's own do."""
    pc.sent = []

    def send(target, code):
        pc.sent.append((target, code))
        coop_link.on_send(pc, types.SimpleNamespace(GrappleableObject=target, GrappleTargetHash=code), None, None)

    pc.ServerSetBestGrappleable = send


def lines(text: str) -> int:
    return sum(text in line for line in state["misc"])


settings.arrival_distance.value = 150

# 1. Solo: the character is the authority, nobody is told.
player, rope = fresh(on_ground=False)
wire(state["pc"])
rope.fire(player, 0)
rope.update(player, int(0.2 * SECOND))
rope.let_go("test", int(0.3 * SECOND))
check("solo, nothing is sent", state["pc"].sent == [])

# 2. A guest's rope is told to the host, with the game's own point sent back after each message.
coop_link.reset()
player, rope = fresh(on_ground=False)
player.role = "ROLE_AutonomousProxy"
pc = state["pc"]
wire(pc)
point = types.SimpleNamespace(Name="GrapplePoint_7")
coop_link.on_send(pc, types.SimpleNamespace(GrappleableObject=point, GrappleTargetHash=3497936138), None, None)
check("the game's own send is let through", coop_link.heard(pc, point, 3497936138, 0) is False)
rope.fire(player, 0)
start_code = pc.sent[0][1] if pc.sent else None
check("the rope going is told: no target and its direction", len(pc.sent) == 2 and pc.sent[0][0] is None
      and start_code not in (0, coop_code.RELEASE, None))
way = coop_code.decode_rope(start_code)
# The fixture's wall is 1000 ahead along X, the anchor at the eyes' height above the capsule's centre.
anchor_way = (1000.0, 0.0, 60.0)
told = math.degrees(math.acos(sum(a * b for a, b in zip(way, anchor_way)) / math.dist(anchor_way, (0, 0, 0))))
check("the direction told is from the character to the anchor", told < 0.01)
check("right after, the game's own point goes back with its number", pc.sent[1] == (point, 3497936138))
check("the probe's own sends are not taken for the game's", coop_link._game_code == 3497936138)
rope.update(player, int(0.2 * SECOND))
rope.update(player, int(0.21 * SECOND))
rope.let_go("jump", int(0.3 * SECOND))
check("the rope letting go is told, then the game's point again",
      pc.sent[2:] == [(None, coop_code.RELEASE), (point, 3497936138)])
rope.let_go("again", int(0.4 * SECOND))
rope.reset()
check("a rope ended once is told once", len(pc.sent) == 4)

coop_link.on_send(pc, types.SimpleNamespace(GrappleableObject=None, GrappleTargetHash=0), None, None)
rope.fire(player, int(1 * SECOND))
check("with no point from the game, 'no target' and 0 go back", pc.sent[-1] == (None, 0))
rope.reset()
check("a rope dropped at a reset is told as let go", pc.sent[-2] == (None, coop_code.RELEASE))

point.destroyed = True
coop_link.on_send(pc, types.SimpleNamespace(GrappleableObject=point, GrappleTargetHash=5), None, None)
rope.fire(player, int(2 * SECOND))
check("a point the game has destroyed is never sent back", pc.sent[-1] == (None, 0))
rope.reset()

pc.ServerSetBestGrappleable = lambda target, code: (_ for _ in ()).throw(RuntimeError("refused"))
check("a refused send costs the host's copy, never the rope", rope.fire(player, int(3 * SECOND)) and rope.busy)
check("and is said once", any("the other players could not be told" in line for line in state["errors"]))
rope.reset()

# 3. On the host: a guest's message is kept from the game, and the same pull is played on the guest.
coop_host.reset()
coop_link.reset()
host, host_rope = fresh(on_ground=True)
host_pc = state["pc"]
wire(host_pc)
guest = sdk_stubs.FakeCharacter()
guest.location = sdk_stubs.vector(0.0, 0.0, 100.0)
guest_pc = types.SimpleNamespace(Name="PC_Guest", Pawn=guest, PlayerState=types.SimpleNamespace(PlayerId=42))
code = coop_code.encode_rope((1000.0, 0.0, 0.0))
check("a guest's message of ours is kept from the game",
      coop_link.on_send(guest_pc, types.SimpleNamespace(GrappleableObject=None, GrappleTargetHash=code), None, None)
      is not None)
check("a guest's own target is the game's business",
      coop_link.on_send(guest_pc, types.SimpleNamespace(GrappleableObject=object(), GrappleTargetHash=9), None, None)
      is None)
check("so is a guest's 'no target'",
      coop_link.on_send(guest_pc, types.SimpleNamespace(GrappleableObject=None, GrappleTargetHash=0), None, None)
      is None)
state["kismet"].calls.clear()
coop_host.tick(0)
check("the anchor is looked for from the guest's character, the way it told",
      state["kismet"].calls and state["kismet"].calls[-1][0].X == 0.0 and state["kismet"].calls[-1][1].X > 1000.0)
check("the hook is said with the guest's name", lines("co-op guest PC_Guest: hook away, 1000 away") == 1)
check("and the host draws the guest's rope", remote_ropes._remotes[42].waiting is not None
      and abs(remote_ropes._remotes[42].waiting[0][0] - 1000.0) < 1.0)
coop_host.tick(int(0.1 * SECOND))
check("nothing is written while the hook flies", game.velocity(guest.CharacterMovement) == (0.0, 0.0, 0.0))
coop_host.tick(int(0.2 * SECOND))
check("at contact the guest is taken off the ground, as the player is",
      guest.CharacterMovement.modes == [3] and game.velocity(guest.CharacterMovement)[2] > 0.0)
check("the host's own character is left alone", game.velocity(host.CharacterMovement) == (0.0, 0.0, 0.0)
      and host.CharacterMovement.modes == [])
coop_host.tick(int(0.21 * SECOND))
check("the guest is pulled toward the anchor", game.velocity(guest.CharacterMovement)[0] > 0.0)
guest.CharacterMovement.acceleration = sdk_stubs.vector(0.0, 24000.0, 0.0)
coop_host.tick(int(0.22 * SECOND))
check("the guest's stick, read from its acceleration, steers its pull", game.velocity(guest.CharacterMovement)[1] > 0.0)
guest.CharacterMovement.acceleration = sdk_stubs.vector(0.0, 0.0, 0.0)
coop_link.on_send(guest_pc, types.SimpleNamespace(GrappleableObject=None, GrappleTargetHash=coop_code.RELEASE),
                  None, None)
coop_host.tick(int(0.23 * SECOND))
kept = game.velocity(guest.CharacterMovement)
check("the guest letting go ends its pull on the host", lines("co-op guest PC_Guest: let go: released by the guest") == 1)
coop_host.tick(int(0.24 * SECOND))
check("its speed is left as it was", game.velocity(guest.CharacterMovement) == kept)

# The host's copy of a guest moves only when the guest's moves arrive: standing still for a frame is no wall, nor is
# the ground, the anchor or its passing. Only the longest pull ends a rope whose release was lost.
coop_link.on_send(guest_pc, types.SimpleNamespace(GrappleableObject=None, GrappleTargetHash=code), None, None)
coop_host.tick(int(1 * SECOND))
coop_host.tick(int(1.2 * SECOND))
coop_host.tick(int(1.25 * SECOND))
coop_host.tick(int(1.3 * SECOND))
guest.location = sdk_stubs.vector(990.0, 0.0, 100.0)
guest.CharacterMovement.MovementMode = sdk_stubs.Mode("MOVE_Walking")
coop_host.tick(int(1.9 * SECOND))
check("a guest standing still for a frame, at the anchor, on the ground: still pulled",
      coop_host._ropes[0].state == coop_host.ATTACHED and lines("co-op guest PC_Guest: let go:") == 1)
coop_host.tick(int((1.2 + float(settings.longest_pull.value) + 0.1) * SECOND))
check("the longest pull ends a rope whose release was lost",
      lines("co-op guest PC_Guest: let go: too long") == 1 and coop_host._ropes[0].state is None)
settings.longest_pull.value = 0.0
coop_link.on_send(guest_pc, types.SimpleNamespace(GrappleableObject=None, GrappleTargetHash=code), None, None)
coop_host.tick(int(20 * SECOND))
coop_host.tick(int(20.2 * SECOND))
coop_host.tick(int((20.2 + coop_host.NO_WORD_S - 0.1) * SECOND))
check("with no longest pull, a guest swings on", coop_host._ropes[0].state == coop_host.ATTACHED)
coop_host.tick(int((20.2 + coop_host.NO_WORD_S) * SECOND))
check("but a lost release still ends at the slider's top", lines("let go: no word from the guest") == 1)
settings.longest_pull.value = 4.0
guest.CharacterMovement.MovementMode = sdk_stubs.Mode("MOVE_Falling")
guest.location = sdk_stubs.vector(0.0, 0.0, 100.0)

# No surface that way.
state["kismet"].hit = None
coop_link.on_send(guest_pc, types.SimpleNamespace(GrappleableObject=None, GrappleTargetHash=code), None, None)
coop_host.tick(int(3 * SECOND))
check("with no surface that way, nothing is pulled, and it is said", lines("no surface found that way") == 1
      and coop_host._ropes[0].state is None)
state["kismet"].hit = (1000.0, "StaticMeshActor")

# A guest gone, or in a vehicle.
coop_link.on_send(guest_pc, types.SimpleNamespace(GrappleableObject=None, GrappleTargetHash=code), None, None)
coop_host.tick(int(4 * SECOND))
guest_pc.Pawn = types.SimpleNamespace(Name="Vehicle")
coop_host.tick(int(4.1 * SECOND))
check("a guest in a vehicle has its rope ended", lines("shot called off: guest gone") == 1)
guest_pc.Pawn = guest

# Bounded.
for index in range(coop_host.MAX_GUESTS + 3):
    other = types.SimpleNamespace(Name=f"PC_{index}", Pawn=guest)
    coop_host.heard(other, code, 0)
check("the guests followed are bounded", len(coop_host._ropes) == coop_host.MAX_GUESTS)
coop_host.reset()
check("switching off forgets every guest", coop_host._ropes == [])

# Through the frame loop, and apart from the player's rope.
coop_host.heard(guest_pc, code, 0)
frame.on_frame(host.anim, 5 * SECOND)
check("the frame loop runs the guests' ropes", coop_host._ropes and coop_host._ropes[0].state == coop_host.FLYING)
guest_pc.Pawn = types.SimpleNamespace(Name="Broken", CharacterMovement=None)
coop_host._ropes[0].pointer = lambda: (_ for _ in ()).throw(RuntimeError("broken"))
frame.on_frame(host.anim, 5 * SECOND + 10 * MS)
check("a failure in the guests' ropes is said and costs them only", coop_host._ropes == []
      and any("co-op guests' ropes stopped" in line for line in state["errors"]))
check("the player's own rope still answers", host_rope.fire(host, 6 * SECOND) and host_rope.busy)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
