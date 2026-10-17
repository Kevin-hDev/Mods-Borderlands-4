"""Tests the co-op messages between games: the host's texts read strictly and kept from the guest's game, never from
the host's own sends; who the host tells of each grapple, never a guest of its own; the looks going round, a guest's
look told to the host when it changes and every few seconds, and a departed guest's look forgotten."""

import types

from grapple_fixture import SECOND, check, fails, fresh, sdk_stubs, settings, state
from apex_grapple import coop_code, coop_link, coop_messages, coop_relay, look_code, look_settings, remote_ropes

import sys

drawn: list[tuple] = []
remote_ropes.look = lambda player, number: drawn.append(("look", player, number))
remote_ropes.start = lambda player, anchor, flight_s, now_ns: drawn.append(("start", player, anchor, flight_s))
remote_ropes.release = lambda player, now_ns: drawn.append(("release", player))


class Controller:
    def __init__(self, name: str, player: int) -> None:
        self.Name = name
        self.PlayerState = types.SimpleNamespace(PlayerId=player)
        self.texts: list[str] = []

    def ClientMessage(self, text: str, kind: str, life: float) -> None:
        self.texts.append(text)


class Pawn:
    def __init__(self, controller: Controller | None, local: bool) -> None:
        self.Controller, self.local = controller, local
        self.CharacterMovement = object()

    def IsLocallyControlled(self) -> bool:
        return self.local


def player(pawn: Pawn, number: int) -> types.SimpleNamespace:
    return types.SimpleNamespace(PlayerId=number, PawnPrivate=pawn)


# 1. The texts.
text = coop_messages.start(256, (1234.56, -678.25, 90.0), 0.384)
check("a rope's text", text == "ApexGrapple:1 S 256 1234.6 -678.2 90.0 384")
check("it reads back", coop_messages.parse(text) == ("S", 256, (1234.6, -678.2, 90.0), 0.384))
check("a look's and a release's read back", coop_messages.parse(coop_messages.look(3, 77)) == ("L", 3, 77)
      and coop_messages.parse(coop_messages.release(3)) == ("R", 3))
check("another text is not ours", coop_messages.parse("Hello there") is None)
for bad in ("ApexGrapple:1 S 1 nan 0 0 10", "ApexGrapple:1 S 1 1e9 0 0 10", "ApexGrapple:1 S 1 0 0 0 99999",
            "ApexGrapple:1 S -1 0 0 0 10", "ApexGrapple:1 L 1 " + str(look_code.COUNT), "ApexGrapple:1 X 1",
            "ApexGrapple:1 R 1 2", "ApexGrapple:1 S 1 0 0 0", "ApexGrapple:1 R " + "9" * 200):
    try:
        coop_messages.parse(bad)
        check(f"refused: {bad[:40]}", False)
    except ValueError:
        pass
check("every malformed text of ours is refused whole", True)

# 2. Received by a guest's game: ours kept from the game and drawn; the host's own sends untouched.
character, rope = fresh(on_ground=False)
local_pc = state["pc"]
check("ours, received: kept from the game", coop_messages.heard(local_pc, coop_messages.release(5), 0) is True
      and drawn[-1] == ("release", 5))
coop_messages.heard(local_pc, coop_messages.start(5, (1.0, 2.0, 3.0), 0.2), 0)
coop_messages.heard(local_pc, coop_messages.look(5, 42), 0)
check("a rope and a look reach the drawing", drawn[-2][:2] == ("start", 5) and drawn[-1] == ("look", 5, 42))
other = Controller("PC_Guest", 9)
check("the host sending to a guest's controller: untouched", coop_messages.heard(other, coop_messages.release(5), 0)
      is False)
check("a text of the game: untouched", coop_messages.heard(local_pc, "You found a chest", 0) is False)
before = len(drawn)
check("a malformed text of ours: kept from the game, drawn nothing",
      coop_messages.heard(local_pc, "ApexGrapple:1 S 1 nan 0 0 1", 0) is True and len(drawn) == before)
check("and said once", any("co-op message from the host was dropped" in line for line in state["errors"]))
check("the hook blocks ours", coop_messages.on_message(local_pc, types.SimpleNamespace(S=coop_messages.release(1)),
                                                       None, None) is not None)

# 3. On the host: who is told what.
host_pc = Controller("PC_Host", 1)
state["pc"] = host_pc
host_pc.OakCharacter = character
first, second = Controller("PC_A", 2), Controller("PC_B", 3)
state["players"][:] = [player(Pawn(host_pc, True), 1), player(Pawn(first, False), 2), player(Pawn(second, False), 3)]
coop_relay.host_rope_start((10.0, 20.0, 30.0), 0.25)
check("the host's rope is told to every guest", first.texts[-1] == second.texts[-1] == coop_messages.start(
    1, (10.0, 20.0, 30.0), 0.25))
coop_relay.host_rope_end()
check("and its release", first.texts[-1] == second.texts[-1] == coop_messages.release(1))
first.texts.clear(), second.texts.clear()
coop_relay.guest_rope_start(first, (5.0, 5.0, 5.0), 0.1, 0)
check("a guest's rope is drawn on the host and told to the others, never to that guest",
      drawn[-1] == ("start", 2, (5.0, 5.0, 5.0), 0.1) and second.texts == [coop_messages.start(2, (5.0, 5.0, 5.0), 0.1)]
      and first.texts == [])
coop_relay.guest_rope_end(first, 0)
check("and its release", drawn[-1] == ("release", 2) and second.texts[-1] == coop_messages.release(2)
      and first.texts == [])
coop_relay.guest_look(first, 99)
check("a guest's look is drawn on the host and told to the others", drawn[-1] == ("look", 2, 99)
      and second.texts[-1] == coop_messages.look(2, 99) and first.texts == [])
told = len(second.texts)
coop_relay.guest_look(first, 99)
check("the same look again is not told again", len(second.texts) == told)

# The looks go round.
first.texts.clear(), second.texts.clear()
coop_relay.tick(0)
mine = look_code.mine()
check("each guest is told the host's look and the others', never its own",
      first.texts == [coop_messages.look(1, mine)]
      and second.texts == [coop_messages.look(1, mine), coop_messages.look(2, 99)])
coop_relay.tick(SECOND)
check("not again before a few seconds", len(first.texts) == 1)
state["players"].pop(1)
coop_relay.tick(6 * SECOND)
check("a departed guest's look is forgotten", 2 not in coop_relay._looks)

# On a guest's game, the other players' controllers do not exist: nobody is told.
state["players"][:] = [player(Pawn(None, False), 1), player(Pawn(local_pc, True), 2)]
second.texts.clear()
coop_relay.host_rope_start((1.0, 1.0, 1.0), 0.1)
coop_relay.tick(20 * SECOND)
check("a guest's game tells nobody", second.texts == [] and first.texts[-1] != coop_messages.start(
    1, (1.0, 1.0, 1.0), 0.1))

# 4. A guest's look told to the host.
coop_link.reset()
state["pc"] = local_pc
character.role = "ROLE_AutonomousProxy"
local_pc.sent = []
local_pc.ServerSetBestGrappleable = lambda target, code: local_pc.sent.append((target, code))
coop_link.tick(character, 0)
check("a guest tells the host its look", local_pc.sent[0] == (None, coop_code.encode_look(look_code.mine())))
coop_link.tick(character, SECOND)
check("not again while it holds, within a few seconds", len(local_pc.sent) == 2)
look_settings.rope_colour.value = "RED"
coop_link.tick(character, 2 * SECOND)
check("again as soon as it changes", local_pc.sent[-2] == (None, coop_code.encode_look(look_code.mine())))
coop_link.tick(character, 8 * SECOND)
check("and again every few seconds", len(local_pc.sent) == 6)
character.role = "ROLE_Authority"
coop_link.tick(character, 20 * SECOND)
check("the host tells nobody its look this way", len(local_pc.sent) == 6)

received: list[tuple] = []
coop_relay.guest_look = lambda controller, number: received.append((controller, number))
state["pc"] = host_pc
coop_link.on_send(first, types.SimpleNamespace(GrappleableObject=None, GrappleTargetHash=coop_code.encode_look(1234)),
                  None, None)
check("the host hands a guest's look to the relay", received == [(first, 1234)])

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
