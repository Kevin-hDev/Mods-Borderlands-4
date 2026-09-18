"""Tests what a file carries: the full pack takes everything, a separate file only its own movements and lines."""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

from apex_movement import menu, movements, pack  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


check("the sources build the full pack", pack.CARRIES == () and pack.NAME == "Apex Movement")
check("the full pack carries every movement", all(pack.carries(m.name) for m in movements.MOVEMENTS))
check("and shows every menu line", len(menu.carried()) == len(menu.ALL))

# A separate file, as the deploy tool writes it.
pack.CARRIES = ("Wall climb",)
check("a separate file carries its own movement", pack.carries("Wall climb"))
check("and no other", not pack.carries("Slides") and not pack.carries("Auto sprint"))
check("its modules come with it", pack.carries_module("climb_aim") and pack.carries_module("wall_sense"))
check("another movement's modules do not", not pack.carries_module("slide_physics"))
check("shared modules are in every file", pack.carries_module("game") and pack.carries_module("frame"))
check("the jump lines come only with the heavier fall, so two files never write a jump twice",
      not pack.carries_module("jump_report"))

lines = [group.identifier for group in menu.carried()]
check("it shows its own menu line", lines == ["wall_climb_menu"])

# The Axle slide shares the Slides movement, so it follows it: one file, both lines.
pack.CARRIES = ("Slides",)
check("a movement with two lines brings both", [group.identifier for group in menu.carried()]
      == ["slides_menu", "axle_slide_menu"])

pack.CARRIES = ("Slides", "Dash")
check("a file may carry several movements", pack.carries("Slides") and pack.carries("Dash"))
check("and shows all their lines", [group.identifier for group in menu.carried()]
      == ["slides_menu", "axle_slide_menu", "dash_menu"])

pack.CARRIES = ("Typo In A Name",)
check("a name that matches no movement carries nothing rather than everything", not pack.carries("Slides"))
check("and shows no movement line", [group.identifier for group in menu.carried()] == [])

pack.CARRIES = ()
check("every movement name in the menu map exists", all(
    any(group.identifier in m.menu_groups for m in movements.MOVEMENTS) for group in menu.ALL))

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
