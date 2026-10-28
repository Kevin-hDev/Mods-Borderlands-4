"""Tests the window in which a co-op host takes a guest's place: from a gesture's frame to the landing after it, at most
LONGEST_NS after the gesture, one window per movement."""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

from apex_movement import guest_trust, guests  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


MS = 1_000_000
guest = sdk_stubs.FakeCharacter("Guest", local=False)
movement = guest.CharacterMovement
memo: dict = {}


def trust(now_ns: int, key: str, active: bool) -> dict:
    return guest_trust.until_landing(guests.GuestFrame(guest, now_ns, lambda field: None, memo), key, active)


check("no gesture yet, the host corrects the guest", trust(0, "slide", False) == {})
check("the engine's two switches are what is asked",
      set(guest_trust.SWITCHES) == {"bIgnoreClientMovementErrorChecksAndCorrection",
                                    "bServerAcceptClientAuthoritativePosition"}
      and all(value is True for value in guest_trust.SWITCHES.values()))
check("during the gesture, the host takes the guest's place", trust(10 * MS, "slide", True) == guest_trust.SWITCHES)
check("the switches handed out are a copy, the rule's own left whole",
      trust(11 * MS, "slide", True) is not guest_trust.SWITCHES)
movement.MovementMode = sdk_stubs.Mode("MOVE_Falling")
check("the gesture over, in the air, still", trust(20 * MS, "slide", False) == guest_trust.SWITCHES)
check("another movement's window is its own", trust(20 * MS, "climb", False) == {})
movement.MovementMode = sdk_stubs.Mode("MOVE_Walking")
check("landed, the host corrects the guest again", trust(30 * MS, "slide", False) == {})
check("and the window is closed", "slide" not in memo)

check("a gesture on the ground opens it", trust(40 * MS, "slide", True) == guest_trust.SWITCHES)
check("and over on the ground, closes it at once", trust(50 * MS, "slide", False) == {})

trust(60 * MS, "climb", True)
movement.MovementMode = sdk_stubs.Mode("MOVE_Falling")
check("never landing, still in the window up to its longest",
      trust(60 * MS + guest_trust.LONGEST_NS, "climb", False) == guest_trust.SWITCHES)
check("past it, the host corrects the guest again", trust(61 * MS + guest_trust.LONGEST_NS, "climb", False) == {})
movement.MovementMode = sdk_stubs.Mode("MOVE_Walking")

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
