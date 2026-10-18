"""Tests coop_trust.py: a co-op host's trust in a guest's own game, on from a rope to the first frame on the ground
after it, at most LONGEST_NS after the rope, held every frame against another writer, put back off (never as found)
on the character it was put on, said only on the frames it changes."""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

sdk_stubs.install()

from apex_grapple import coop_trust  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


MS = 1_000_000
guest = sdk_stubs.FakeCharacter()
movement = guest.CharacterMovement


def switches(target=movement) -> tuple:
    return tuple(getattr(target, name) for name in coop_trust.SWITCHES)


trust = coop_trust.Trust()
check("the engine's two switches are the ones asked", set(coop_trust.SWITCHES) == {
    "bIgnoreClientMovementErrorChecksAndCorrection", "bServerAcceptClientAuthoritativePosition"})
check("no rope yet: nothing written, nothing said", trust.step(guest, False, 0) is None and switches() == (False, False))
check("a rope told: the guest's own game keeps its place, said once", trust.step(guest, True, 10 * MS) == "on"
      and switches() == (True, True))
check("and not said again while the rope lasts", trust.step(guest, True, 20 * MS) is None)
movement.MovementMode = sdk_stubs.Mode("MOVE_Falling")
movement.bServerAcceptClientAuthoritativePosition = False
check("the rope over, in the air: still on, and held against another writer",
      trust.step(guest, False, 30 * MS) is None and switches() == (True, True))
movement.MovementMode = sdk_stubs.Mode("MOVE_Walking")
check("landed: off, said once", trust.step(guest, False, 40 * MS) == "off" and switches() == (False, False))
check("and the window is closed", not trust.on and trust.step(guest, False, 50 * MS) is None)

movement.bIgnoreClientMovementErrorChecksAndCorrection = True
trust.step(guest, True, 60 * MS)
trust.step(guest, False, 70 * MS)
check("found on (the other mod's window), put back off all the same", switches() == (False, False))

movement.MovementMode = sdk_stubs.Mode("MOVE_Falling")
trust.step(guest, True, 100 * MS)
check("never landing, on up to the longest", trust.step(guest, False, 100 * MS + coop_trust.LONGEST_NS) is None
      and switches() == (True, True))
check("past it, off", trust.step(guest, False, 101 * MS + coop_trust.LONGEST_NS) == "off" and switches() == (False, False))

trust.step(guest, True, 200 * MS)
other = sdk_stubs.FakeCharacter()
check("a new character for the same guest: the old one given back, the new one on",
      trust.step(other, True, 210 * MS) == "on" and switches() == (False, False) and switches(other.CharacterMovement) == (True, True))
trust.give_back()
check("given back at once, wherever the guest is", switches(other.CharacterMovement) == (False, False) and not trust.on)

trust.step(guest, True, 300 * MS)
guest.destroyed = True
trust.give_back()
check("a character the game destroyed is only forgotten", not trust.on)
guest.destroyed = False
movement.MovementMode = sdk_stubs.Mode("MOVE_Walking")

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
