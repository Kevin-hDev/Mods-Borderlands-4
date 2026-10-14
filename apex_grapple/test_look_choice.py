"""Tests look_choice.py: the look of each shot follows the settings, nothing while the rope is hidden; the grapple
gun's for the six hunters, one we do not know keeping the classic look with the page's sentence saying why; once the
grapple gun's look gives way it stays classic, the first cause kept for the window's sentence, each kind said once."""

import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

from apex_grapple import look_choice, look_settings, settings  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def hunter(definition: str) -> types.SimpleNamespace:
    return types.SimpleNamespace(GbxActorData=types.SimpleNamespace(GbxActorDef=f"FGbxDefPtr('{definition}')"))


vex, amon, other = hunter("Char_DarkSiren"), hunter("Char_Paladin"), hunter("Char_Newcomer")
check("at first, for Vex, the grapple gun's look, and nothing to say", look_choice.for_shot(vex) == look_choice.OURS
      and look_choice.notice() is None)
check("Amon too", look_choice.for_shot(amon) == look_choice.OURS and look_choice.notice() is None)
check("a hunter we do not know keeps the classic look, and the page says this hunter does not have it yet",
      look_choice.for_shot(other) == look_choice.CLASSIC and look_choice.notice() == look_choice.UNKNOWN_HUNTER)
check("back on Vex, nothing to say", look_choice.for_shot(vex) == look_choice.OURS and look_choice.notice() is None)
look_settings.look.value = look_settings.CLASSIC
check("the classic look when chosen", look_choice.for_shot(vex) == look_choice.CLASSIC)
settings.show_rope.value = False
check("no look at all while the rope is hidden, whatever the look", look_choice.for_shot(vex) is None)
settings.show_rope.value = True
look_settings.look.value = look_settings.GRAPPLE_GUN

look_choice.stop(look_choice.MISSING, "3 of our pieces missing")
look_choice.stop(look_choice.MISSING, "3 of our pieces missing")
look_choice.stop(look_choice.FAILED, "RuntimeError('refused')")
check("once it gave way, the classic look until the game restarts, the first cause kept for the window",
      look_choice.for_shot(vex) == look_choice.CLASSIC and look_choice.notice() == look_choice.MISSING)
check("each kind of cause said once in the log",
      sum("3 of our pieces missing" in line for line in state["errors"]) == 1
      and sum("refused" in line for line in state["errors"]) == 1)
settings.show_rope.value = False
check("and still nothing while the rope is hidden", look_choice.for_shot(vex) is None)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
