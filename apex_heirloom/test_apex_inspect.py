"""Tests the heirloom's inspection: the chosen heirloom's own, by the name the catalog gives, played once in the arms'
FullBody slot, the draw's, at normal speed, from its start with no fade; pressed again while it plays, from its first
key with a short fade in, never a fade out; pressed after its end, from its start again; crouched, the one built on the
crouched rest, by its own name, the stance read at each press; the heirloom leaving the hand stops it at once, and
nothing else; a heirloom without an inspection plays nothing, said once; an inspection that cannot be found or played,
or a stance that cannot be read, is said once and not tried again; a line per press, bounded."""

import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import heirloom_stubs  # noqa: E402

heirloom_stubs.install()

from apex_heirloom import apex_inspect  # noqa: E402
from fake_arms import Arms, pointer  # noqa: E402

fails: list[str] = []
said: list[str] = []
raised: list[Exception] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def safely(action) -> None:
    """A press or a stop run as the key and the watch run it; what it raises is kept, a failure of its check."""
    try:
        action()
    except Exception as error:
        raised.append(error)


class OneGroup(Arms):
    """The arms as the engine plays a montage: a new one in the same slot group stops the one playing there."""

    def PlaySlotAnimationAsDynamicMontage(self, **options) -> tuple:
        self.playing.clear()
        return super().PlaySlotAnimationAsDynamicMontage(**options)


axe = apex_inspect.inspection("axe")
check("the axe has an inspection in the catalog, a press during it starting from a time within it",
      isinstance(axe, dict) and axe.get("animation") == "AS_UA_Inspect"
      and 0.0 < float(axe.get("again_at", 0.0)) < 5.0)
check("the knife has none", apex_inspect.inspection("jakobs_knife") is None)

sequence = types.SimpleNamespace(Name="AS_UA_Inspect")
loads: list[str] = []
chosen = ["axe"]
crouched = [False]


def load(name: str) -> object:
    loads.append(name)
    return sequence


def last(arms_played: Arms) -> dict:
    """The options of the last montage played, none when nothing was."""
    return arms_played.played[-1] if arms_played.played else {}


arms = OneGroup()
inspect = apex_inspect.Inspect(lambda: chosen[0], lambda: crouched[0], load, pointer, said.append)
again_at = float((axe or {}).get("again_at", -1.0))
inspect.play(arms)
first = arms.played[0] if arms.played else {}
check("a first press plays the chosen heirloom's inspection once, in the FullBody slot, at normal speed",
      loads == ["AS_UA_Inspect"] and first.get("Asset") is sequence and first.get("SlotNodeName") == "FullBody"
      and first.get("LoopCount") == 1 and first.get("InPlayRate") == 1.0 and first.get("BlendOutTriggerTime") == -1.0)
check("... from its start, with no fade in and no fade out: it starts from the rest and ends at it",
      first.get("InTimeToStartMontageAt") == 0.0 and first.get("BlendInTime") == 0.0
      and first.get("BlendOutTime") == 0.0)
check("... and says so", said == ["axe inspected from 0 s"])
inspect.play(arms)
again = arms.played[1] if len(arms.played) > 1 else {}
check("pressed again while it plays: from its first key, fading in in 0.1 s, still no fade out",
      len(arms.played) == 2 and again.get("InTimeToStartMontageAt") == again_at and again.get("BlendInTime") == 0.1
      and again.get("BlendOutTime") == 0.0 and said[-1] == f"axe inspected again from {again_at:g} s")
check("a press never waits: it plays at once, each press its own gesture", len(arms.playing) == 1)
inspect.play(arms)
check("and again while that one plays", len(arms.played) == 3 and last(arms).get("InTimeToStartMontageAt") == again_at)
arms.playing.clear()
inspect.play(arms)
check("pressed after its end: from its start again, with no fade",
      len(arms.played) == 4 and last(arms).get("InTimeToStartMontageAt") == 0.0
      and last(arms).get("BlendInTime") == 0.0)
arms.playing.clear()
crouched[0] = True
inspect.play(arms)
check("crouched: a press plays the inspection built on the crouched rest, from its start, and says so",
      axe is not None and loads[-1] == axe.get("crouched") == "AS_UA_Inspect_Crouch"
      and last(arms).get("InTimeToStartMontageAt") == 0.0 and said[-1] == "axe inspected crouched from 0 s")
inspect.play(arms)
check("... pressed again while it plays, still crouched: that one again, from its first key",
      loads[-1] == "AS_UA_Inspect_Crouch" and last(arms).get("InTimeToStartMontageAt") == again_at)
crouched[0] = False
inspect.play(arms)
check("stood up while it plays: a press plays the standing one, from its first key",
      loads[-1] == "AS_UA_Inspect" and last(arms).get("InTimeToStartMontageAt") == again_at)

latest, draw = (arms.playing[-1] if arms.playing else None), object()
arms.playing.append(draw)
said.clear()
inspect.cancel(arms)
check("the heirloom leaving the hand while it plays stops it at once, and leaves the arms' other montages",
      arms.stopped == [(0.0, latest)] and draw in arms.playing
      and said == ["inspection stopped: the heirloom left the empty hand while it played"])
inspect.cancel(arms)
check("stopped once, nothing more to stop", len(arms.stopped) == 1 and len(said) == 1)
arms.playing.remove(draw)
inspect.play(arms)
check("after a stop, a press plays it from its start", last(arms).get("InTimeToStartMontageAt") == 0.0)
arms.playing.clear()
inspect.cancel(arms)
check("ended by itself, nothing is stopped", len(arms.stopped) == 1)

said.clear()
loads.clear()
chosen[0] = "jakobs_knife"
played = len(arms.played)
inspect.play(arms)
inspect.play(arms)
check("a heirloom without an inspection plays nothing and loads nothing, said once",
      len(arms.played) == played and loads == [] and len(said) == 1 and "has no inspection" in said[0])
chosen[0] = "axe"
inspect.play(arms)
check("the axe chosen again: its inspection plays", len(arms.played) == played + 1)

said.clear()
missing = apex_inspect.Inspect(lambda: "axe", lambda: False, lambda _name: None, pointer, said.append)
safely(lambda: missing.play(arms))
safely(lambda: missing.play(arms))
check("an inspection not in the game is said once, and nothing is played",
      not raised and len(said) == 1 and "AS_UA_Inspect was not found" in said[0] and "no inspection until" in said[0]
      and len(arms.played) == played + 1)

said.clear()
loads.clear()
refusing = OneGroup(ValueError("no such slot"))
broken = apex_inspect.Inspect(lambda: "axe", lambda: False, load, pointer, said.append)
safely(lambda: broken.play(refusing))
safely(lambda: broken.play(arms))
check("an inspection the arms refuse is said once with the reason, and not tried again",
      not raised and len(said) == 1 and "ValueError: no such slot" in said[0] and len(loads) == 1
      and len(arms.played) == played + 1)


def unreadable_stance() -> bool:
    raise AttributeError("no bIsCrouched")


said.clear()
loads.clear()
blind = apex_inspect.Inspect(lambda: "axe", unreadable_stance, load, pointer, said.append)
safely(lambda: blind.play(arms))
safely(lambda: blind.play(arms))
check("a stance that cannot be read is said once with the reason, nothing loaded nor played, and not tried again",
      not raised and len(said) == 1 and "AttributeError: no bIsCrouched" in said[0] and loads == []
      and len(arms.played) == played + 1)


class Unreadable(OneGroup):
    def Montage_IsPlaying(self, montage: object) -> bool:
        raise RuntimeError("montage gone")


said.clear()
unreadable = Unreadable()
fragile = apex_inspect.Inspect(lambda: "axe", lambda: False, load, pointer, said.append)
safely(lambda: fragile.play(unreadable))
safely(lambda: fragile.play(unreadable))
check("arms that cannot tell whether it plays: said once, never raised", not raised and len(said) == 2
      and "RuntimeError: montage gone" in said[1] and len(unreadable.played) == 1)
said.clear()
safely(lambda: fragile.cancel(unreadable))
check("... and a stop they refuse is said, never raised",
      not raised and len(said) == 1 and "could not be stopped (RuntimeError: montage gone)" in said[0])

said.clear()
chatty = apex_inspect.Inspect(lambda: "axe", lambda: False, load, pointer, said.append)
for _ in range(apex_inspect.MAX_TOLD + 20):
    chatty.play(OneGroup())
check("a line per press, bounded: many presses do not fill the log", len(said) == apex_inspect.MAX_TOLD)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
