"""Tests the heirloom's put-away: the put-away our container holds in our own folder is played once on the arms from
its start, at the speed set, blending out at its end over the rise set, with the weapon hidden; it says when the hands
are down; the weapon shows again when they are, when the put-away is cut short, and when it fails; a put-away that
cannot be found or played is said once and not tried again."""

import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import definition_fixture  # noqa: E402
import heirloom_stubs  # noqa: E402
from heirloom_stubs import sdk_stubs  # noqa: E402

heirloom_stubs.install()

from apex_heirloom import apex_moves_timing as moves_timing  # noqa: E402
from apex_heirloom import apex_put_away  # noqa: E402
from fake_arms import Arms, pointer  # noqa: E402

fails: list[str] = []
said: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


class Weapon:
    def __init__(self, error: Exception | None = None) -> None:
        self.hidden: list[bool] = []
        self.error = error

    def SetActorHiddenInGame(self, hidden: bool) -> None:
        if self.error is not None and not hidden:
            raise self.error
        self.hidden.append(hidden)


definition = definition_fixture.load()
if definition is None:
    definition_fixture.skip("the animation played is the one the knife's Apex pose rebuilds as its put-away")
else:
    apex = definition["pose"]["modes"]["apex"]
    to_below = [g["sequences"] for g in apex["animations"] if g.get("between", [None, None])[1] == "below"]
    check("the animation played is the one the knife's Apex pose rebuilds as its put-away, to under the screen",
          to_below == [[apex_put_away.PUT_AWAY]])

sequence = types.SimpleNamespace(Name="AS_UA_Unequip", GetPlayLength=lambda: 0.3333)
loads: list[int] = []


def load() -> object:
    loads.append(1)
    return sequence


timing = moves_timing.Timing(away=0.8, rise=0.3)
arms, weapon = Arms(), Weapon()
put_away = apex_put_away.PutAway(load, timing, pointer, said.append)
lasting = put_away.start(arms, weapon)
played = arms.played[0] if arms.played else {}
check("the weapon is hidden and the put-away plays once in the FullBody slot, from its start, at the speed set, "
      "without blending in, and blends out at its very end over the rise set",
      weapon.hidden == [True] and played.get("Asset") is sequence and played.get("SlotNodeName") == "FullBody"
      and played.get("LoopCount") == 1 and played.get("InTimeToStartMontageAt") == 0.0
      and played.get("InPlayRate") == 0.8 and played.get("BlendInTime") == 0.0 and played.get("BlendOutTime") == 0.3
      and played.get("BlendOutTriggerTime") == 0.0)
check("it says in how long the hands are down: its length at the speed set",
      lasting is not None and abs(lasting - 0.3333 / 0.8) < 1e-9 and said[-1].startswith("heirloom put away"))
put_away.finish()
check("the hands down, the weapon shows again and the put-away blends out by itself",
      weapon.hidden == [True, False] and not arms.stopped)
put_away.finish()
check("finished twice, the weapon is shown once", weapon.hidden == [True, False])

weapon = Weapon()
put_away.start(arms, weapon)
latest, climb = arms.playing[-1], object()
arms.playing.append(climb)
put_away.cancel(arms)
check("cut short, the put-away stops at once, only it, and the weapon shows again",
      arms.stopped == [(0.0, latest)] and climb in arms.playing and weapon.hidden == [True, False])

said.clear()
missing = apex_put_away.PutAway(lambda: None, timing, pointer, said.append)
weapon = Weapon()
check("a put-away not found plays nothing, hides no weapon, and is said once",
      missing.start(arms, weapon) is None and missing.start(arms, weapon) is None and not weapon.hidden
      and len(said) == 1 and "without its put-away" in said[0])

said.clear()
loads.clear()
broken = apex_put_away.PutAway(load, timing, pointer, said.append)
weapon = Weapon()
check("a put-away the arms refuse shows the weapon again, is said once with the reason, and is not tried again",
      broken.start(Arms(ValueError("no such slot")), weapon) is None and weapon.hidden == [True, False]
      and broken.start(arms, Weapon()) is None and len(loads) == 1 and len(said) == 1
      and "ValueError: no such slot" in said[0])

said.clear()
stubborn = Weapon(RuntimeError("gone"))
put_away = apex_put_away.PutAway(load, timing, pointer, said.append)
put_away.start(arms, stubborn)
put_away.finish()
check("a weapon that cannot be shown again is said", any("could not be shown again" in line for line in said))

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
