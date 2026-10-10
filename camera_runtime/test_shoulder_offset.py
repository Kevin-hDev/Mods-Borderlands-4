"""The shoulder given to the game keeps the native camera's transitions: a swap glides, aiming and the vehicle cut at
once, climbing and Orbit glide out and back in the modes they allow, and the framing's spacing and height grow with
it."""

import sys
from types import SimpleNamespace as NS

from apex_camera_runtime.constants import CLIMB_MODE, THIRD_PERSON_RIGHT as RIGHT, THIRD_PERSON_UP as UP
from apex_camera_runtime.shoulder_offset import ShoulderOffset, framing_share

fails = []


def check(label, condition):
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def near(a, b):
    return all(abs(x - y) < 1e-6 for x, y in zip(a, b))


clock = [0]
MS = 1_000_000


def at(ms):
    clock[0] = int(ms * MS)


def fresh():
    at(0)
    shoulder = ShoulderOffset(clock=lambda: clock[0])
    shoulder.show(RIGHT)
    return shoulder


def manager(mode):
    return NS(GetActorCameraMode=lambda _actor: mode)


shoulder = fresh()
check("the first side stands at once", near(shoulder.place(0.0, 0.0), (RIGHT, UP)))
check("the framing's spacing widens it and its height lifts it, by the sideways distance",
      near(shoulder.place(0.5, 0.1), (RIGHT * 1.5, UP + 0.1 * RIGHT)))
check("what the game gets is kept for the automatic shoulder", shoulder.applied == (RIGHT * 1.5, UP + 0.1 * RIGHT, 0))
shoulder.withhold()
check("and dropped when the game gets none", shoulder.applied is None)

shoulder.transition_duration(0.4)
shoulder.show(-RIGHT)
check("a swap starts on the side shown", near(shoulder.place(0.0, 0.0), (RIGHT, UP)))
at(200)
check("halfway through its time it crosses the middle, the height kept", near(shoulder.place(0.0, 0.0), (0.0, UP)))
check("a swap is not a glide other code waits for", not shoulder.transition_active())
at(400)
check("and lands on the other side", near(shoulder.place(0.0, 0.0), (-RIGHT, UP)))

shoulder = fresh()
shoulder.transition_duration(0.4)
shoulder.show(-RIGHT)
at(100)
shoulder.transition_duration(0.0)
check("a swap time set to nothing ends the swap at once", near(shoulder.place(0.0, 0.0), (-RIGHT, UP)))

shoulder = fresh()
shoulder.suspend(True)
check("aiming takes the shoulder away at once", near(shoulder.place(0.5, 0.1), (0.0, 0.0)))
shoulder.show(-RIGHT)
shoulder.suspend(False)
check("and gives it back at once, on a side chosen meanwhile", near(shoulder.place(0.0, 0.0), (-RIGHT, UP)))

shoulder = fresh()
shoulder.suspend(True, 0.2, climbing=True)
at(100)
check("climbing glides it out", near(shoulder.place(0.0, 0.0), (RIGHT / 2, UP / 2)))
check("and other code can wait for that glide", shoulder.transition_active())
check("climbing's own mode shows it meanwhile", shoulder.allows(manager(CLIMB_MODE), None))
at(200)
check("until it is gone", near(shoulder.place(0.0, 0.0), (0.0, 0.0)) and not shoulder.transition_active())
shoulder.suspend(True, 0.2, climbing=True)
check("the same state again starts no glide", not shoulder.transition_active())
shoulder.suspend(False, 0.2)
at(300)
check("it glides back when climbing ends", near(shoulder.place(0.0, 0.0), (RIGHT / 2, UP / 2)))
check("and climbing's mode no longer shows it", not shoulder.allows(manager(CLIMB_MODE), None))

shoulder = fresh()
answers = [True]
shoulder.suspend(True, 0.2, permission=lambda _manager, _actor: answers[0])
check("during Orbit's glide its permission names the modes", shoulder.allows(manager("Orbit"), None))
answers[0] = False
check("including refusing ThirdPerson", not shoulder.allows(manager("ThirdPerson"), None))
answers[0] = None
check("a permission without an answer leaves the usual modes", shoulder.allows(manager("ThirdPerson"), None))
at(250)
check("once the glide is over the permission is dropped",
      not shoulder.allows(manager("Orbit"), None) and shoulder.permission is None)
shoulder.suspend(False)
check("a cut without time carries no permission", shoulder.permission is None)

shoulder = fresh()
check("a shoulder outside the native limits is refused",
      not shoulder.show(float("nan")) and not shoulder.show(True) and not shoulder.show(150.5)
      and shoulder.right == RIGHT)
for label, call in (("an invalid swap time", lambda: shoulder.transition_duration(-0.1)),
                    ("a swap time past the menu's limit", lambda: shoulder.transition_duration(1.5)),
                    ("an invalid suspension", lambda: shoulder.suspend("yes")),
                    ("an invalid glide time", lambda: shoulder.suspend(True, float("inf")))):
    try:
        call()
        check(f"{label} is refused", False)
    except ValueError:
        check(f"{label} is refused", True)
shoulder.reset()
check("a reset forgets the side and every glide", shoulder.right == 0.0 and not shoulder.suspended
      and shoulder.applied is None and shoulder.permission is None)

check("a mod without the framing gives no spacing", framing_share(NS()) == (0.0, 0.0))
check("the framing's choices are fractions",
      framing_share(NS(framing_values=lambda: ((15, False), (50, True), (-10, False)))) == (0.5, -0.1))
check("an invalid choice counts as none, the framing refusing it too",
      framing_share(NS(framing_values=lambda: ((15, False), (51, True), (0, False)))) == (0.0, 0.0))
check("an unreadable snapshot gives none", framing_share(NS(framing_values=lambda: ((15, False),))) == (0.0, 0.0)
      and framing_share(NS(framing_values=lambda: ((15, False), 50, (0, False)))) == (0.0, 0.0))

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
