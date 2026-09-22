"""Tests the menu: three lines that follow a grapple, and every setting shown exactly once."""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

from apex_grapple import menu, settings  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


visible = [line for line in menu.MENU if not getattr(line, "is_hidden", False)]
check("the menu has the three phases, controls and reset", len(visible) == 5)
check("named the way a player would say them",
      [line.display_name for line in visible] ==
      ["The shot", "The pull", "Letting go", "Grapple controls", "Restore defaults"])
check("each line says what it holds", all(line.description for line in visible))
check("controls opens the window directly, without another submenu",
      callable(getattr(visible[3], "on_press", None)) and not hasattr(visible[3], "children"))

shown = [option for line in menu.MENU[:3] for option in line.children]
check("every setting is on a line", len(shown) == len(settings.ALL))
check("none of them twice", len({option.identifier for option in shown}) == len(shown))
check("and none of them missing",
      {option.identifier for option in shown} == {option.identifier for option in settings.ALL})

check("the shot line holds the range, the reserve cost and the punch rule",
      {option.identifier for option in menu.shot.children} ==
      {"grapple_range", "hook_speed", "stamina_cost", "melee_wins", "punch_range", "keep_game_grapple",
       "show_rope"})
check("the pull line holds the two forces and their caps",
      {option.identifier for option in menu.pull.children} ==
      {"pull_strength", "pull_speed_cap", "rope_carry", "steer_strength", "steer_speed_cap"})
check("the letting go line holds every end of a pull",
      {option.identifier for option in menu.release.children} ==
      {"release_on_key_up", "arrival_distance", "longest_pull", "takeoff_lift", "ground_grace",
       "release_on_landing", "block_jump"})

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
