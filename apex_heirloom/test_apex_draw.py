"""Tests the heirloom's draw: the draw our container holds in our own folder is played once on the arms, without
blending in, from the start and at the speed set, as the menu changes them; the heirloom hidden stops the draw at
once, and nothing else in the slot; a draw that cannot be found or played is said once and not tried again."""

import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import definition_fixture  # noqa: E402
import heirloom_stubs  # noqa: E402
from heirloom_stubs import sdk_stubs  # noqa: E402

heirloom_stubs.install()

from apex_heirloom import apex_draw  # noqa: E402
from apex_heirloom import apex_moves_timing as moves_timing  # noqa: E402
from fake_arms import Arms, pointer  # noqa: E402

fails: list[str] = []
said: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


definition = definition_fixture.load()
if definition is None:
    definition_fixture.skip("the animation played is the one the knife's Apex pose rebuilds as its draw")
else:
    apex = definition["pose"]["modes"]["apex"]
    drawn_from_below = [g["sequences"] for g in apex["animations"] if g.get("between", [None])[0] == "below"]
    check("the animation played is the one the knife's Apex pose rebuilds as its draw, from under the screen",
          drawn_from_below == [[apex_draw.DRAW]])

sequence = types.SimpleNamespace(Name="AS_UA_Equip")
loads: list[int] = []


def load() -> object:
    loads.append(1)
    return sequence


arms = Arms()
timing = moves_timing.Timing()
draw = apex_draw.Draw(load, timing, pointer, said.append)
draw.play(arms)
check("the draw plays once in the FullBody slot, without blending in, blends out briefly, and by default rises as "
      "Kevin set it in game: from 0.4 s in, at 0.8 times its speed",
      len(arms.played) == 1 and arms.played[0]["Asset"] is sequence and arms.played[0]["SlotNodeName"] == "FullBody"
      and arms.played[0]["LoopCount"] == 1 and arms.played[0]["InTimeToStartMontageAt"] == 0.4
      and arms.played[0]["BlendInTime"] == 0.0 and 0 < arms.played[0]["BlendOutTime"] <= 0.2
      and arms.played[0]["InPlayRate"] == 0.8)
check("the draw is said with its timing",
      said == ["heirloom drawn from 0.4 s at 0.8 times its speed"])
timing.start, timing.speed = 0.1, 1.5
draw.play(arms)
check("each weapon put away draws again, with the timing typed since",
      len(arms.played) == 2 and arms.played[1]["InTimeToStartMontageAt"] == 0.1
      and arms.played[1]["InPlayRate"] == 1.5)
latest, climb = arms.playing[-1], object()
arms.playing.append(climb)
said.clear()
draw.cancel(arms)
check("the heirloom hidden while the draw plays stops that draw at once, and leaves the slot's other montages",
      arms.stopped == [(0.0, latest)] and climb in arms.playing
      and said == ["draw stopped: the heirloom was hidden while it played"])
draw.cancel(arms)
draw.play(arms)
arms.playing.remove(arms.playing[-1])
draw.cancel(arms)
check("hidden again, or once the draw has ended, nothing more is stopped", len(arms.stopped) == 1 and len(said) == 2)

said.clear()
missing = apex_draw.Draw(lambda: None, timing, pointer, said.append)
missing.play(arms)
missing.play(arms)
check("a draw not found is said once, and nothing is played",
      len(said) == 1 and "not found" in said[0] and "without its draw" in said[0] and len(arms.played) == 3)

said.clear()
loads.clear()
broken = apex_draw.Draw(load, timing, pointer, said.append)
broken.play(Arms(ValueError("no such slot")))
broken.play(arms)
check("a draw the arms refuse is said once with the reason, and not tried again",
      len(said) == 1 and "ValueError: no such slot" in said[0] and len(arms.played) == 3 and len(loads) == 1)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
