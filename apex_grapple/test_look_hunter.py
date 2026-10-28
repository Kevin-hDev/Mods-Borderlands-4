"""Tests look_hunter.py: the hunter is told by the first name of their definition, as the log shows it, read once per
character and said in the log; Loveless, whose definition names Vex further in, is Loveless; a hunter we do not know,
or a definition the game will not give, is none, the failure said once."""

import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

from apex_grapple import look_hunter  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


class Hunter:
    def __init__(self, definition: str | None) -> None:
        self.definition, self.reads = definition, 0

    @property
    def GbxActorData(self):
        self.reads += 1
        if self.definition is None:
            raise RuntimeError("unreadable")
        return types.SimpleNamespace(GbxActorDef=self.definition)


def written(name: str, further: str = "") -> str:
    """A definition as the log of 2026-10-14 wrote Loveless's."""
    return f"FGbxDefPtr('Char_{name}', 'GbxActorDef', {{SpawnDetails: {{}}{further}}})"


vex = Hunter(written("DarkSiren"))
check("Vex, by her class", look_hunter.of(vex) == "DarkSiren" and look_hunter.of(vex) == "DarkSiren" and vex.reads == 1)
check("said in the log", any("hunter: DarkSiren, the grapple gun" in line for line in state["misc"]))
loveless = Hunter(written("CorpoHacker", ", Source: {NexusDefPtr: FGbxDefPtr('Char_DarkSiren', 'GbxActorDef', None)}"))
check("Loveless, though her definition names Vex further in", look_hunter.of(loveless) == "CorpoHacker")
check("the six hunters are known",
      [look_hunter.of(Hunter(written(name))) for name in
       ("DarkSiren", "CorpoHacker", "ExoSoldier", "Gravitar", "Paladin", "RoboDealer")]
      == ["DarkSiren", "CorpoHacker", "ExoSoldier", "Gravitar", "Paladin", "RoboDealer"])
check("a hunter we do not know is none, and said so",
      look_hunter.of(Hunter(written("Newcomer"))) is None
      and any("hunter: Newcomer, the classic look only" in line for line in state["misc"]))
lost = Hunter(None)
check("an unreadable definition is none, the failure said once",
      look_hunter.of(lost) is None and look_hunter.of(Hunter(None)) is None
      and sum("hunter could not be read" in line for line in state["errors"]) == 1)
look_hunter.forget()
check("forgotten, the character is read again", look_hunter.of(vex) == "DarkSiren" and vex.reads == 2)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
