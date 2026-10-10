"""Tests the one writer of the sprint's backward slot: the forward sprint while the body is held turned, Omni Sprint's
backward carrier otherwise, emptied as the game leaves it, never a body's slot once that body is replaced, and a body
whose layout is unknown left alone."""

import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from apex_camera_runtime import sprint_slot  # noqa: E402
from apex_camera_runtime.sprint_slot import CARRIER, FORWARD, NONE  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


class Carrier:
    """Stands in for backward_carrier.BackwardCarrier: fills the slot with its own run while asked."""

    def __init__(self) -> None:
        self.owner = None
        self.run = object()
        self.updates = 0

    def update(self, character, anim, now_ns) -> None:
        self.updates += 1
        anim.players[1].BlendSpace, self.owner = self.run, anim

    def stop(self) -> None:
        if self.owner is not None:
            self.owner.players[1].BlendSpace, self.owner = None, None


def body():
    return types.SimpleNamespace(players=(types.SimpleNamespace(BlendSpace=object()),
                                          types.SimpleNamespace(BlendSpace=None)))


def players(anim):
    if anim.players is None:
        raise ValueError("Unexpected animation player count")
    return anim.players


lines: list[str] = []
carrier = Carrier()
slot = sprint_slot.SprintSlot(carrier, players, lambda left, right: left is not None and left is right,
                              lambda value: lambda: value, lines.append)
anim = body()
forward, backward = anim.players
slot.update(None, anim, 1, FORWARD, 0)
check("held turned, the slot gets the forward sprint, said", backward.BlendSpace is forward.BlendSpace
      and lines == ["forward sprint put in the backward slot, write 1"])
slot.update(None, anim, 1, FORWARD, 1)
check("already there, it is not written again", len(lines) == 1)
slot.update(None, anim, 1, CARRIER, 2)
check("let go, the forward sprint leaves before the carrier comes", backward.BlendSpace is carrier.run)
slot.update(None, anim, 1, FORWARD, 3)
check("held again, the carrier is stopped first and the forward sprint comes back",
      carrier.owner is None and backward.BlendSpace is forward.BlendSpace)
slot.update(None, anim, 1, NONE, 4)
check("nothing asked, the slot is empty again as the game leaves it", backward.BlendSpace is None)
other = object()
slot.update(None, anim, 1, FORWARD, 5)
backward.BlendSpace = other
slot.update(None, anim, 1, NONE, 6)
check("a slot something else changed meanwhile is left as it is", backward.BlendSpace is other)
backward.BlendSpace = None

new_anim = body()
slot.update(None, anim, 1, FORWARD, 7)
slot.update(None, new_anim, 2, NONE, 8)
check("a new body: the old body's slot is never touched again", backward.BlendSpace is forward.BlendSpace)
backward.BlendSpace = None
for frame in range(10):
    slot.update(None, new_anim, 2, FORWARD, 10 + frame)
    new_anim.players[1].BlendSpace = None
check("writes are said a few times, then only counted", len([line for line in lines if "write" in line]) == 5)
broken = types.SimpleNamespace(players=None)
slot.update(None, broken, 3, FORWARD, 30)
slot.update(None, broken, 3, FORWARD, 31)
check("a body whose layout is unknown is left alone, said once",
      lines.count("sprint slot left alone for this body: ValueError") == 1)
slot.update(None, new_anim, 4, FORWARD, 32)
check("the next body is tried again", new_anim.players[1].BlendSpace is new_anim.players[0].BlendSpace)
slot.stop()
check("stopping empties the slot and gives the count", new_anim.players[1].BlendSpace is None
      and lines[-1] == "forward sprint writes this session: 15")
slot.update(None, new_anim, 4, CARRIER, 40)
slot.anim_ref = lambda: None
slot.holding = True
slot.stop()
check("stopping stops the carrier too, and a body gone is not touched", carrier.owner is None)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
