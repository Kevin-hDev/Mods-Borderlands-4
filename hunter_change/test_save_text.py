"""A game's text read and changed as bytes: the header of the game's layout (identifier, hunter, name, character
level, never the specialization's, never a key of the same name outside the state block, None rather than a guess or
an error); the game's id read from a text's beginning, its three answers: the id once its line is whole, undecided
while the beginning ends before the answer, not a game's text for a profile, a state block ending first, a later
block, a deeper line or an id not written as one; the same id as header() when the state block holds two; the tree
found byte for byte, none for a game that never started one, refused when not where the game writes it, when a
blank line or a line of a tab is in progression, or when a line of spaces or a tab would cut it; the tree's groups
and whose tree it is, Loveless's included; a tree block told from anything else; the tree removed, put back or
replaced, nothing else touched; the hunter and name changed on their own lines only, the same class and name
further down left alone, a name the game may not read back refused; the name following the hunter, a number kept,
any other name staying."""

import sys

import sdk_stubs

sdk_stubs.install()

import save_fixture as fx  # noqa: E402
from hunter_change import hunters, save_text  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def refused(action) -> bool:
    try:
        action()
    except ValueError:
        return True
    return False


VEX, RAFA, HARLOWE, AMON = (hunters.by_code(code) for code in ("DarkSiren", "ExoSoldier", "Gravitar", "Paladin"))
LOVELESS = hunters.by_code("CorpoHacker")

HEADER = (b"state: \n  char_guid: 0123456789ABCDEF0123456789ABCDEF\n  class: Char_Gravitar\n  char_name: Harlowe 2\n"
          b"  player_difficulty: Easy\n  experience: \n  - type: Specialization\n    level: 7\n    points: 0\n"
          b"  - type: Character\n    level: 52\n    points: 3910506\n  inventory: \n    items: \n"
          b"save_game_header: \n  guid: 76C11FD05C8997C7F3C9BCF1DA5A2AE7\n"
          b"progression: \n  class: Char_Paladin\n  char_name: Other\n")
found = save_text.header(HEADER)
check("the header gives the game's identifier, hunter, name and character level",
      found == {"game": "0123456789ABCDEF0123456789ABCDEF", "hunter": "Char_Gravitar", "name": "Harlowe 2", "level": 52})
check("a text without a state block, or a field missing, gives None",
      save_text.header(b"progression: \n  graphs: \n") is None
      and save_text.header(HEADER.replace(b"  class: Char_Gravitar\n", b"")) is None)
check("a text that is not UTF-8 gives None", save_text.header(b"state: \n  char_name: \xff\xfe\n") is None)


def answer(action):
    """What the action gives, or the error it raises."""
    try:
        return action()
    except ValueError as error:
        return error


check("a level not written in plain digits gives None, never an error",
      answer(lambda: save_text.header(HEADER.replace(b"    level: 52\n", "    level: ²\n".encode()))) is None)
check("an id not written as one gives None",
      save_text.header(HEADER.replace(b"0123456789ABCDEF", b"0123456789abcdef")) is None)

GAME = fx.game_text(fx.HARLOWE_GAME, "Gravitar", "Harlowe", fx.TREES["Gravitar"])
line_end = GAME.index(b"\n", GAME.index(b"  char_guid: ")) + 1
A_GAME = b"A" * 32
NOT_A_GAME, UNDECIDED = save_text.NoId.NOT_A_GAME, save_text.NoId.UNDECIDED
check("the game's id read from its text's beginning once its line is whole, the same header() reads",
      all(save_text.game_of(GAME[:size]) == fx.HARLOWE_GAME for size in (line_end, line_end + 7))
      and save_text.game_of(GAME, whole=True) == fx.HARLOWE_GAME
      and save_text.game_of(HEADER, whole=True) == found["game"]
      and save_text.game_of(b"state: \n  char_guid: " + A_GAME, whole=True) == A_GAME.decode())
check("undecided while the beginning ends before its line is whole, the first line's cut included",
      all(save_text.game_of(GAME[:size]) is UNDECIDED for size in range(line_end)))
check("a whole text cut inside its id line is not a game's",
      save_text.game_of(GAME[:line_end - 5], whole=True) is NOT_A_GAME)
check("a profile's text is not a game's, from its first line on",
      save_text.game_of(b"domains: \n") is NOT_A_GAME
      and save_text.game_of(b"domains: \n  local: \n    char_guid: " + A_GAME + b"\n") is NOT_A_GAME)
no_id = GAME.replace(f"  char_guid: {fx.HARLOWE_GAME}\n".encode(), b"")
state_end = no_id.index(b"save_game_header: \n")
check("a state block ending before any id line is not a game's, once that end is whole in the beginning",
      save_text.game_of(no_id[:state_end]) is UNDECIDED
      and save_text.game_of(no_id[:state_end + len(b"save_game_header: \n")]) is NOT_A_GAME
      and save_text.game_of(no_id, whole=True) is NOT_A_GAME)
check("a char_guid only in a later block, or deeper in the state block, is not the game's",
      save_text.game_of(no_id.replace(b"save_game_header: \n", b"save_game_header: \n  char_guid: " + A_GAME + b"\n"),
                        whole=True) is NOT_A_GAME
      and save_text.game_of(no_id.replace(b"    level: 52\n", b"    char_guid: " + A_GAME + b"\n"),
                            whole=True) is NOT_A_GAME)
check("a lower-case id, or one of another length, is not a game's",
      save_text.game_of(GAME.replace(fx.HARLOWE_GAME.encode(), fx.HARLOWE_GAME.lower().encode())) is NOT_A_GAME
      and save_text.game_of(GAME.replace(fx.HARLOWE_GAME.encode(), fx.HARLOWE_GAME[:31].encode())) is NOT_A_GAME)
twice = GAME.replace(b"  class: Char_Gravitar\n", b"  class: Char_Gravitar\n  char_guid: " + A_GAME + b"\n")
check("two ids in the state block: game_of and header() both name the first",
      save_text.game_of(twice) == fx.HARLOWE_GAME and (save_text.header(twice) or {}).get("game") == fx.HARLOWE_GAME)

WITH = fx.game_text(fx.HARLOWE_GAME, "Gravitar", "Harlowe", fx.TREES["Gravitar"])
WITHOUT = fx.game_text(fx.HARLOWE_GAME, "Gravitar", "Harlowe", None)
check("the tree is found byte for byte", save_text.tree(WITH) == fx.TREES["Gravitar"])
check("a game that never started a tree has none", save_text.tree(WITHOUT) is None)
late = WITHOUT.replace(b"  point_pools: \n", b"  point_pools: \n" + fx.TREES["Gravitar"])
check("a tree not first in progression is refused, not doubled", refused(lambda: save_text.tree(late)))
check("a tree field written another way is refused",
      refused(lambda: save_text.tree(WITH.replace(b"  graphs: \n", b"  graphs:\n"))))
check("a text without progression, or with two, is refused",
      refused(lambda: save_text.tree(b"state: \n  class: Char_Gravitar\n"))
      and refused(lambda: save_text.tree(WITH + b"progression: \n")))
gap_in_tree = WITH.replace(b"    - name: Progress_Grav_Trunk\n", b"\n    - name: Progress_Grav_Trunk\n")
check("a blank line inside the tree is refused, the tree not cut there",
      refused(lambda: save_text.tree(gap_in_tree)) and refused(lambda: save_text.with_tree(gap_in_tree, None)))
gap_before_tree = WITHOUT.replace(b"    characterprogresspoints: 51\n",
                                  b"    characterprogresspoints: 51\n\n" + fx.TREES["Gravitar"])
check("a tree after a blank line is refused, not written twice",
      refused(lambda: save_text.tree(gap_before_tree))
      and refused(lambda: save_text.with_tree(gap_before_tree, fx.TREES["Gravitar"])))
tab_before_tree = gap_before_tree.replace(b"51\n\n", b"51\n\t\n")
check("a tree after a line of a tab is refused, not written twice",
      refused(lambda: save_text.tree(tab_before_tree))
      and refused(lambda: save_text.with_tree(tab_before_tree, fx.TREES["Gravitar"])))
for label, line in (("two spaces", b"  \n"), ("one space", b" \n"), ("a tab", b"\t\n")):
    spaced = WITH.replace(b"    - name: Progress_Grav_Trunk\n", line + b"    - name: Progress_Grav_Trunk\n")
    spaced_tree = fx.TREES["Gravitar"].replace(b"    - name: Grav\n", line + b"    - name: Grav\n")
    check(f"a line of {label} inside the tree is refused, the tree not cut there",
          refused(lambda: save_text.tree(spaced)) and refused(lambda: save_text.with_tree(spaced, None))
          and not save_text.valid_tree(spaced_tree))

check("a tree's groups", save_text.groups(fx.TREES["DarkSiren"]) == {"ProgressGroup_DarkSiren"})
check("a hunter's tree belongs to it and to no other",
      save_text.belongs(fx.TREES["Gravitar"], HARLOWE) and not save_text.belongs(fx.TREES["Gravitar"], AMON)
      and not save_text.belongs(fx.TREES["Gravitar"], LOVELESS))
mixed = fx.TREES["Gravitar"] + fx.TREES["Paladin"][len(b"  graphs: \n"):]
check("a tree of two groups belongs to nobody", not any(save_text.belongs(mixed, hunter) for hunter in hunters.HUNTERS))
loveless = fx.TREES["Paladin"].replace(b"ProgressGroup_Paladin", b"ProgressGroup_Corpohacker")
check("Loveless's tree belongs to her, to no other",
      save_text.belongs(loveless, LOVELESS) and not save_text.belongs(loveless, AMON)
      and not save_text.belongs(loveless.replace(b"Corpohacker", b"CorpoHacker"), LOVELESS))
ungrouped = fx.TREES["Paladin"].replace(b"    group_def_name: ProgressGroup_Paladin\n", b"")
check("a graph without its group belongs to nobody", not save_text.belongs(ungrouped + fx.TREES["Paladin"][11:], AMON))

check("a tree block from a save is one", save_text.valid_tree(fx.TREES["DarkSiren"]))
check("anything else is not", not save_text.valid_tree(b"  graphs: \n")
      and not save_text.valid_tree(fx.TREES["Paladin"] + b"missions: \n")
      and not save_text.valid_tree(fx.TREES["Paladin"][2:])
      and not save_text.valid_tree(fx.TREES["Paladin"].rstrip(b"\n"))
      and not save_text.valid_tree(fx.TREES["Paladin"].replace(b"Calamity", b"\xff")))

check("the tree removed, nothing else touched", save_text.with_tree(WITH, None) == WITHOUT)
check("the tree put back gives the very text", save_text.with_tree(WITHOUT, fx.TREES["Gravitar"]) == WITH)
check("a tree replaced by another",
      save_text.with_tree(WITH, fx.TREES["Paladin"]) == WITHOUT.replace(
          b"progression: \n", b"progression: \n" + fx.TREES["Paladin"]))
check("removing no tree changes nothing", save_text.with_tree(WITHOUT, None) == WITHOUT)
check("something that is not a tree is not put in", refused(lambda: save_text.with_tree(WITHOUT, b"  graphs: \n")))

changed = save_text.with_hunter(WITH, AMON, "Amon")
lines = [(a, b) for a, b in zip(WITH.split(b"\n"), changed.split(b"\n")) if a != b]
check("the hunter and name changed on their own lines only",
      lines == [(b"  class: Char_Gravitar", b"  class: Char_Paladin"), (b"  char_name: Harlowe", b"  char_name: Amon")])
twin = WITH.replace(b"  class: Char_Decoy\n", b"  class: Char_Gravitar\n  char_name: Harlowe\n")
check("the same class and name further down are not touched",
      not refused(lambda: save_text.with_hunter(twin, AMON, "Amon"))
      and save_text.with_hunter(twin, AMON, "Amon") == twin.replace(
          b"  class: Char_Gravitar\n  char_name: Harlowe\n", b"  class: Char_Paladin\n  char_name: Amon\n", 1))
kept_name = save_text.with_hunter(WITH, AMON, "Harlowe")
check("the same name leaves its line", kept_name == WITH.replace(b"  class: Char_Gravitar\n", b"  class: Char_Paladin\n"))
check("a name the game may not read back is refused",
      refused(lambda: save_text.with_hunter(WITH, AMON, "Amon: 2"))
      and refused(lambda: save_text.with_hunter(WITH, AMON, "Amon ")))
check("a text without a header is refused", refused(lambda: save_text.with_hunter(b"progression: \n", AMON, "Amon")))

check("the hunter's own name follows the hunter", save_text.followed_name("Vex", VEX, RAFA) == "Rafa")
check("a number is kept", save_text.followed_name("Amon 2", AMON, RAFA) == "Rafa 2")
check("any other name stays", save_text.followed_name("Mon perso", VEX, RAFA) == "Mon perso"
      and save_text.followed_name("Vexy", VEX, RAFA) == "Vexy"
      and save_text.followed_name("Vex 1234", VEX, RAFA) == "Vex 1234"
      and save_text.followed_name("Rafa", VEX, AMON) == "Rafa")

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
