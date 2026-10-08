"""The choices file: nothing chosen and nothing written without one; a choice kept in memory and on disk with its
version, the body and head of the game's own skins unless others are named; read back from the file; a game of
version 1 read with the game's own skins, an unknown skin read as the game's own; the own look chosen removes the
game; bounded, the game chosen longest ago forgotten first; read tolerantly (unknown fields ignored, bad entries
skipped, a newer version's entries read); an unreadable, oversized or too deeply nested file taken as empty and said
once; written whole through a temporary file, a failed write said and the choice kept for the session; an id, hunter
or skin the mod does not know refused."""

import json
import os
import sys

import sdk_stubs

state = sdk_stubs.install()

from hunter_change import choices, file_replace, report  # noqa: E402

fails: list[str] = []
RAFA, HARLOWE = "4F3ED67C7CDBB85DD75426BD679FD6BC", "8107146506D5906AD9BCCD4479661B4D"


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def stored() -> dict:
    return json.loads(choices.path().read_text(encoding="utf-8"))


def fresh(content: str | None = None) -> None:
    """The file as another run left it, and the mod starting again."""
    if content is None:
        choices.path().unlink(missing_ok=True)
    else:
        choices.path().write_text(content, encoding="utf-8")
    choices.forget()
    report.reset()
    state["errors"].clear()


check("the file in the mods' settings folder", choices.path().parent == state["settings_dir"])
check("nothing chosen and nothing written without a file", choices.chosen(RAFA) is None and not choices.path().exists())

check("a choice kept in memory, with the game's own skins unless others are named",
      choices.choose(RAFA, "CorpoHacker") and choices.chosen(RAFA) == ("CorpoHacker", "default", "default")
      and choices.chosen(RAFA).hunter == "CorpoHacker")
check("a choice kept on disk with the file's version", stored() == {"version": 2, "games": [
    {"game": RAFA, "hunter": "CorpoHacker", "body": "default", "head": "default"}]})
choices.choose(RAFA, "CorpoHacker", "premium", "prison")
choices.forget()
check("read back from the file with its body and head",
      choices.chosen(RAFA) == choices.Choice("CorpoHacker", "premium", "prison"))
choices.choose(HARLOWE, "Paladin")
choices.choose(RAFA, None)
check("the own look chosen removes the game", choices.chosen(RAFA) is None
      and stored()["games"] == [{"game": HARLOWE, "hunter": "Paladin", "body": "default", "head": "default"}])

fresh(json.dumps({"version": 1, "games": [{"game": RAFA, "hunter": "CorpoHacker"},
                                          {"game": HARLOWE, "hunter": "Paladin", "body": "gold", "head": 3}]}))
check("a game of version 1 read with the game's own skins, an unknown skin read as the game's own",
      choices.chosen(RAFA) == ("CorpoHacker", "default", "default")
      and choices.chosen(HARLOWE) == ("Paladin", "default", "default") and not state["errors"])

fresh()
games = [f"{index:032X}" for index in range(1, choices.MAX_GAMES + 1)]
for game in games:
    choices.choose(game, "Gravitar")
choices.choose(games[0], "Paladin")
choices.choose(RAFA, "CorpoHacker")
kept = [entry["game"] for entry in stored()["games"]]
check("bounded, the game chosen longest ago forgotten first", len(kept) == choices.MAX_GAMES
      and games[1] not in kept and kept[-2:] == [games[0], RAFA] and choices.chosen(games[1]) is None)
check("a full file with its body and head well under half the size the mod reads",
      choices.choose(RAFA, "CorpoHacker", "premium", "premium")
      and len(choices.path().read_bytes()) < choices.MAX_BYTES // 2)

fresh(json.dumps({"version": 3, "note": "newer", "games": [
    {"game": RAFA, "hunter": "CorpoHacker", "since": 12}, {"game": "not-an-id", "hunter": "Paladin"},
    {"game": HARLOWE, "hunter": "Echo4"}, {"game": HARLOWE.lower(), "hunter": "Paladin"}, "odd", {"hunter": "x"}]}))
check("read tolerantly: unknown fields ignored, bad entries skipped, a newer version's entries read",
      choices.chosen(RAFA).hunter == "CorpoHacker" and choices.chosen(HARLOWE) is None and not state["errors"])

fresh("{ not json")
check("an unreadable file taken as empty and said once", choices.chosen(RAFA) is None
      and choices.chosen(HARLOWE) is None and len(state["errors"]) == 1 and "choices" in state["errors"][0])
fresh(json.dumps({"version": 1, "games": "none"}))
check("a file of another shape taken as empty and said", choices.chosen(RAFA) is None and len(state["errors"]) == 1)
fresh(" " * (choices.MAX_BYTES + 1))
check("an oversized file taken as empty and said", choices.chosen(RAFA) is None and len(state["errors"]) == 1)
fresh("[" * 5000)
try:
    deep = choices.chosen(RAFA) is None and len(state["errors"]) == 1
except RecursionError:
    deep = False
check("a file nested too deep to read taken as empty and said", deep)

fresh()
choices.choose(RAFA, "CorpoHacker")
check("written whole through a temporary file",
      not choices.path().with_name(choices.path().name + file_replace.TEMPORARY_SUFFIX).exists())
real_replace = os.replace
os.replace = lambda *_args: (_ for _ in ()).throw(OSError("disk full"))
written = choices.choose(HARLOWE, "Paladin")
os.replace = real_replace
check("a failed write said and the choice kept for the session",
      not written and choices.chosen(HARLOWE).hunter == "Paladin" and len(state["errors"]) == 1
      and [entry["game"] for entry in stored()["games"]] == [RAFA])

refused = []
for game, hunter, body, head in ((RAFA.lower(), "Paladin", "default", "default"),
                                 ("../x", "Paladin", "default", "default"), (RAFA, "Echo4", "default", "default"),
                                 (RAFA, "", "default", "default"), (RAFA, "Paladin", "gold", "default"),
                                 (RAFA, "Paladin", "default", None)):
    try:
        choices.choose(game, hunter, body, head)
    except ValueError:
        refused.append(game)
check("an id, hunter or skin the mod does not know refused", len(refused) == 6)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
