"""Tests a part of the mod: it runs while the mod is on and its switch is on, is started and stopped only when one of
the two changes it, never twice in a row; a switch about to change is followed by the value it gets; only an
explicit Off stops it, a malformed saved value keeping it."""

import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import heirloom_stubs  # noqa: E402

heirloom_stubs.install()
from apex_heirloom.parts import Part  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


calls: list[str] = []
switch = types.SimpleNamespace(value=True)
part = Part(switch, lambda: calls.append("start"), lambda: calls.append("stop"))

check("built stopped", not part.running and not calls)
part.follow(False)
check("the mod off: nothing to stop", not calls)
part.follow(True)
check("the mod on, the switch on: started", part.running and calls == ["start"])
part.follow(True)
check("not started twice", calls == ["start"])
part.follow(True, False)
check("the switch about to be Off: stopped, as the value it gets says", not part.running and calls == ["start", "stop"])
part.follow(True, False)
check("not stopped twice", calls == ["start", "stop"])
part.follow(True, True)
part.follow(False)
check("the switch On again starts it, the mod off stops it", calls == ["start", "stop", "start", "stop"])
switch.value = False
part.follow(True)
check("the mod on with the switch Off: it stays stopped", not part.running and calls[-1] == "stop" and len(calls) == 4)
switch.value = "yes"
part.follow(True)
check("a malformed saved value keeps the part", part.running and calls[-1] == "start")

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
