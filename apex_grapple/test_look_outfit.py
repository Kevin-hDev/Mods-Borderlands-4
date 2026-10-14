"""Tests look_outfit.py: Vex's own long coat covers her hip, her Premium and Prison outfits do not; read anew each
time, so an outfit changed on the same character counts at once; said in the log when it changes; unreadable, the
holster stays hidden, the failure said once."""

import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

from apex_grapple import look_outfit  # noqa: E402
import vex_fixture  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def wearing(parts) -> None:
    character.Mesh = types.SimpleNamespace(GestaltMeshParts=[types.SimpleNamespace(Name=part) for part in parts])


PRISON = ("SKPart_DS_Body_01_Prison_UpperBody", "SKPart_DS_Body_01_Prison_LowerBody", "SK_DarkSiren_Base_Head")

character = types.SimpleNamespace()
wearing(vex_fixture.COAT)
check("her own long coat covers the hip", look_outfit.covers_hip(character))
check("said in the log with the parts", any("SKPart_DarkSiren_Jacket" in line and "stays hidden under it" in line
                                            for line in state["misc"]))
said = len(state["misc"])
check("asked again, the same answer, the log quiet", look_outfit.covers_hip(character) and len(state["misc"]) == said)
wearing(vex_fixture.PREMIUM)
check("the outfit changed on the same character: Premium does not cover it, said once",
      not look_outfit.covers_hip(character) and "shows on the hip" in state["misc"][-1])
wearing(PRISON)
check("nor does Prison", not look_outfit.covers_hip(character))


class Unreadable:
    @property
    def Mesh(self):
        raise RuntimeError("no mesh")


check("unreadable, the holster stays hidden, the failure said once",
      look_outfit.covers_hip(Unreadable()) and look_outfit.covers_hip(Unreadable())
      and sum("outfit could not be read" in line for line in state["errors"]) == 1)
look_outfit.forget()
said = len(state["misc"])
look_outfit.covers_hip(character)
check("forgotten, the next reading is said again", len(state["misc"]) == said + 1)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
