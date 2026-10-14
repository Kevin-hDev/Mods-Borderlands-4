"""Tests look_weapon.py: a pistol's body ends in PS; every other weapon is a long gun; no weapon in hand, nothing."""

import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

sdk_stubs.install()

from apex_grapple import look_weapon  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def holding(body: str | None) -> types.SimpleNamespace:
    weapon = None if body is None else types.SimpleNamespace(BodyData=types.SimpleNamespace(Name=body))
    return types.SimpleNamespace(ActiveWeapons=types.SimpleNamespace(Slots=[types.SimpleNamespace(Weapon=weapon)]))


check("a pistol, as trial 1 read the Order pistol's body",
      look_weapon.kind(holding("Body_ORD_PS")) == look_weapon.PISTOL)
check("the long guns, and anything else",
      all(look_weapon.kind(holding(body)) == look_weapon.LONG
          for body in ("Body_JAK_AR", "Body_BOR_SR", "Body_MAL_SG", "Body_TOR_HW", "Body_PSX", "")))
check("no weapon in hand", look_weapon.kind(holding(None)) is None)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
