"""Tests the menu: three lines that follow a grapple, the hold mode, and every setting shown exactly once."""

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
check("the menu has the three phases, the look, the hold mode, controls and reset", len(visible) == 7)
check("named the way a player would say them",
      [line.display_name for line in visible] ==
      ["The shot", "The pull", "Letting go", "Look", "Hold to grapple", "Grapple controls", "Restore defaults"])
check("each line says what it holds", all(line.description for line in visible))
check("controls opens the window directly, without another submenu",
      callable(getattr(visible[5], "on_press", None)) and not hasattr(visible[5], "children"))

shown = [option for line in menu.MENU[:5] for option in line.children]
check("every setting is on a line", len(shown) == len(settings.ALL))
check("none of them twice", len({option.identifier for option in shown}) == len(shown))
check("and none of them missing",
      {option.identifier for option in shown} == {option.identifier for option in settings.ALL})

check("the shot line holds the range, the reserve cost and the punch rule",
      {option.identifier for option in menu.shot.children} ==
      {"grapple_range", "hook_speed", "stamina_cost", "melee_wins", "punch_range", "keep_game_grapple"})
check("the look line holds the rope's switch, then the look and its rows, in the sketch's order",
      [option.identifier for option in menu.look.children] ==
      ["show_rope", "look", "rope_look", "glow_face", "rope_thickness", "rope_light", "rope_colour", "rope_movement",
       "hook_size", "holster", "game_rope_colour"])
check("every look row greys while the rope is hidden",
      set(menu.DEPENDS_ON) == {option.identifier for option in menu.look.children[1:]}
      and all(rule == (("show_rope",),) for rule in menu.DEPENDS_ON.values()))
OURS = {"rope_look", "rope_thickness", "rope_light", "rope_colour", "rope_movement", "hook_size", "holster"}
check("the grapple gun's rows grey with the classic look, the look's own row does not",
      set(menu.ACTIVE_WHEN) == OURS | {"glow_face", "game_rope_colour"}
      and all(menu.ACTIVE_WHEN[name]({"look": "GRAPPLE_GUN"}) and not menu.ACTIVE_WHEN[name]({"look": "CLASSIC"})
              for name in OURS))
face, game_rope = menu.ACTIVE_WHEN["glow_face"], menu.ACTIVE_WHEN["game_rope_colour"]
check("the glow's face counts with our look's glow only, the game rope's colour with the classic look only",
      face({"look": "GRAPPLE_GUN", "rope_look": "C"}) and not face({"look": "GRAPPLE_GUN", "rope_look": "A"})
      and not face({"look": "CLASSIC", "rope_look": "C"})
      and game_rope({"look": "CLASSIC"}) and not game_rope({"look": "GRAPPLE_GUN"}))
check("the colours choose on arrows", menu.ARROWS == {"rope_colour", "game_rope_colour"})
check("the look page says nothing while the grapple gun's look can play", menu.NOTICES["look"]() is None)
check("the hold line holds the two switches and the hold time, which the window shows with the keys",
      [option.identifier for option in menu.hold.children] == ["keyboard_hold", "controller_hold", "hold_time"])
check("the pull line holds the two forces and their caps",
      {option.identifier for option in menu.pull.children} ==
      {"pull_strength", "pull_speed_cap", "rope_carry", "steer_strength", "steer_speed_cap"})
check("the letting go line holds every end of a pull",
      {option.identifier for option in menu.release.children} ==
      {"release_on_key_up", "arrival_distance", "longest_pull", "takeoff_lift", "ground_grace",
       "release_on_landing", "block_jump"})

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
