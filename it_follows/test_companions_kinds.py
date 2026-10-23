"""Tests the companions a team is made of (companions/kinds.py): the six hunters first, each Lemmy wearing the look of
that name (hunters.py), then the four allies, each born as itself; every companion known by its name, the names
unique; a hunter's look one hunters.py knows."""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

sdk_stubs.install()

from it_follows.companions import hunters, kinds  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


LEMMY = "Char_GunToter_Shatter2_Lemmy"
check("the six hunters: Lemmy, each in a hunter's look, by that hunter's name", kinds.HUNTERS == tuple(
      (LEMMY, name, name) for name in ("Loveless", "Rafa", "Vex", "Amon", "Harlowe", "C4SH"))
      and kinds.LEMMY == LEMMY)
check("each hunter's look known to hunters.py", all(kind.look in hunters.BY_NAME for kind in kinds.HUNTERS))
check("the four allies, each born as itself, never dressed", [(kind.name, kind.look) for kind in kinds.ALLIES] == [
      ("Decrepit Frame", None), ("Crankus", None), ("Brine Type M", None), ("Abomination", None)]
      and len({kind.definition for kind in kinds.ALLIES}) == 4
      and LEMMY not in {kind.definition for kind in kinds.ALLIES})
check("all of them, hunters first, each known by a name of its own", kinds.ALL == kinds.HUNTERS + kinds.ALLIES
      and len(kinds.BY_NAME) == len(kinds.ALL) == 10 and all(kinds.BY_NAME[kind.name] is kind for kind in kinds.ALL))

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
