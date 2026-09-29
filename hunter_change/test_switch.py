"""Changing a game's hunter: a first change done, the save showing the new hunter under its name without a tree, nothing
else changed, the tree left kept byte for byte, the save backed up first, no temporary file left, the look chosen
forgotten, another game untouched; back to the first hunter, its tree put back and the very first text given, the tree
put back staying kept until its hunter leaves; "Continue" right after a change losing no tree; a hunter leaving without
a tree leaving none kept; refusals writing nothing (same or unknown hunter, a hunter the save does not show, a game
without a save, a game in two saves, a tree of another hunter or too large to keep, an unreadable trees file, a save
that does not reopen to the text prepared, a text prepared that does not show the change: two identical class or name
lines side by side, a tree put back that does not read back alone, a line of the old hunter's group left, another game),
the look chosen included; cut at each step as the conception's table says (no backup, the tree not kept, a tree not
dropped, a save held three times, held twice then free, read back different then restored, not restored and said, not
put back and said so, put back but held at its read back and said, not readable back then left as written), the look
chosen kept until the save reads back; a save held an instant while it is looked for; a temporary file left by a cut
removed; an unreadable or too deeply nested choices file left as it is, the change done; every step logged, each line
and error numbered, the start before the search's own lines, without path nor account."""

import os
import pathlib
import re
import shutil
import sys

import sdk_stubs

state = sdk_stubs.install()

import save_fixture as fx  # noqa: E402
from hunter_change import (backups, choices, file_replace, hunters, report, save_codec, save_places,  # noqa: E402
                           save_text, switch, trees)

fails: list[str] = []
G = fx.HARLOWE_GAME
documents, client = fx.saves_folder()
PLACES = [documents]
HARLOWE_TEXT = fx.game_text(G, "Gravitar", "Harlowe", fx.TREES["Gravitar"])
VEX_TEXT = fx.game_text(fx.VEX_GAME, "DarkSiren", "Vex", fx.TREES["DarkSiren"])
LOOK = "CorpoHacker"
pauses: list[float] = []
real_replace = os.replace


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def run(current: str, wanted: str, game: str = G) -> switch.Outcome:
    return switch.change(game, current, wanted, PLACES, sleep=pauses.append)


def text(slot: int = 4) -> bytes:
    return save_codec.decode((client / f"{slot}.sav").read_bytes(), fx.ACCOUNT)


def names() -> list[str]:
    return sorted(path.name for path in client.iterdir())


def backed_up() -> list[bytes]:
    return [path.read_bytes() for path in sorted(backups.folder().glob("*.sav"))] if backups.folder().is_dir() else []


def snapshot() -> tuple:
    kept, looks = (path.read_bytes() if path.exists() else None for path in (trees.path(), choices.path()))
    return {path.name: path.read_bytes() for path in client.iterdir()}, kept, looks, backed_up()


def fresh(look: bool = False) -> bytes:
    """The saves, trees, backups and choices before any change, with the look LOOK chosen in the Harlowe game when
    asked; the Harlowe save's bytes."""
    for path in client.iterdir():
        path.unlink()
    fx.put(client, 1, VEX_TEXT)
    original = fx.put(client, 4, HARLOWE_TEXT).read_bytes()
    trees.path().unlink(missing_ok=True)
    choices.path().unlink(missing_ok=True)
    if backups.folder().is_dir():
        for path in backups.folder().iterdir():
            path.unlink()
    for module in (trees, choices, report):
        getattr(module, "forget", getattr(module, "reset", None))()
    os.replace = real_replace
    state["errors"].clear()
    pauses.clear()
    if look:
        choices.choose(G, LOOK)
    return original


original = fresh(look=True)
# Closed with ACCOUNT in another account's folder: the search says it does not open, a line of its own in the log.
theirs = client.parents[2] / str(fx.OTHER) / "Profiles" / "client"
theirs.mkdir(parents=True)
fx.put(theirs, 1, VEX_TEXT)
state["logs"].clear()
outcome = run("Gravitar", "Paladin")
shutil.rmtree(theirs.parents[1])
after = text()
head = save_text.header(after)
check("a first change done, the new hunter without a tree yet", outcome.done and outcome.first_time)
check("the save shows the new hunter under its name, without a tree",
      (head["hunter"], head["name"]) == ("Char_Paladin", "Amon") and save_text.tree(after) is None)
check("nothing else changed", save_text.with_tree(
    save_text.with_hunter(after, hunters.by_code("Gravitar"), "Harlowe"), fx.TREES["Gravitar"]) == HARLOWE_TEXT)
check("the tree left kept byte for byte", trees.kept(G, "Gravitar") == fx.TREES["Gravitar"])
check("the save backed up first, as the game wrote it", backed_up() == [original])
check("no temporary file left next to the save", names() == ["1.sav", "4.sav"])
check("the look chosen in this game forgotten", choices.chosen(G) is None)
check("another game untouched", text(1) == VEX_TEXT)
lines = [line for line in state["logs"] if " switch " in line]
numbers = {re.search(r"switch (\w+):", line).group(1) for line in lines}
steps = ("started", "prepared", "backed up", "tree kept", "written", "read back", "done")
search_line = next((at for at, line in enumerate(state["logs"]) if "does not open" in line), 0)
check("every step logged, each line numbered, the start before the search's own, without path nor account",
      len(numbers) == 1 and all(any(step in line for line in lines) for step in steps)
      and " switch " in state["logs"][0] and "started" in state["logs"][0] and search_line > 0
      and not any(str(fx.ACCOUNT) in line or str(documents) in line for line in state["logs"] + state["errors"]))

# The game writes Amon's tree once the player builds it (essai 1); then back to Harlowe.
fx.put(client, 4, save_text.with_tree(after, fx.TREES["Paladin"]))
outcome = run("Paladin", "Gravitar")
check("back to the first hunter, its tree put back and the very first text given",
      outcome.done and not outcome.first_time and text() == HARLOWE_TEXT)
check("the tree put back stays kept until its hunter leaves, the one left is kept",
      trees.kept(G, "Gravitar") == fx.TREES["Gravitar"] and trees.kept(G, "Paladin") == fx.TREES["Paladin"])
# "Continue" without another game selected first: the game writes back the save it holds, Amon's (essai 8).
fx.put(client, 4, save_text.with_tree(after, fx.TREES["Paladin"]))
check('"Continue" right after a change loses no tree', run("Paladin", "Gravitar").done and text() == HARLOWE_TEXT)

fresh()
run("Gravitar", "Paladin")
trees.keep(G, "Paladin", fx.TREES["Paladin"])
check("a hunter leaving without a tree leaves none kept",
      run("Paladin", "Gravitar").done and trees.kept(G, "Paladin") is None)

fresh(look=True)
before = snapshot()
for label, args, reason in (("the same hunter", ("Gravitar", "Gravitar"), "unknown_hunter"),
                            ("an unknown hunter", ("Gravitar", "Echo4"), "unknown_hunter"),
                            ("a hunter the save does not show", ("Paladin", "DarkSiren"), "not_this_hunter")):
    check(f"{label} refused, nothing written", run(*args).reason == reason and snapshot() == before)
check("a game without a save refused, nothing written",
      run("Gravitar", "Paladin", game="E" * 32).reason == save_places.NO_SAVE and snapshot() == before)
fx.put(client, 7, save_codec.decode((client / "4.sav").read_bytes(), fx.ACCOUNT))
before = snapshot()
check("a game in two saves refused as two_saves, nothing written",
      run("Gravitar", "Paladin").reason == save_places.TWO_SAVES and snapshot() == before)
(client / "7.sav").unlink()
before = snapshot()
fx.put(client, 4, fx.game_text(G, "Gravitar", "Harlowe", fx.TREES["Paladin"]))
before = snapshot()
check("a tree of another hunter in the save refused, nothing written",
      run("Gravitar", "Paladin").reason == "foreign_tree" and snapshot() == before)
node = b"    - name: Progress_Grav_Node\n      points_spent: 1\n"
fx.put(client, 4, fx.game_text(G, "Gravitar", "Harlowe", fx.TREES["Gravitar"] + node * 2000))
before = snapshot()
try:
    too_large = run("Gravitar", "Paladin").reason
except ValueError:  # trees.keep refusing it after the backup: the refusal came too late
    too_large = "raised after the backup"
check("a tree too large to keep refused, nothing written", too_large == "foreign_tree" and snapshot() == before)
fresh(look=True)
real_encode = save_codec.encode
save_codec.encode = lambda plain, account: real_encode(plain + b"#", account)
before = snapshot()
check("a save that does not reopen to the text prepared refused, nothing written",
      run("Gravitar", "Paladin").reason == "prepare_failed" and snapshot() == before)
save_codec.encode = real_encode
for label, line in (("class", b"  class: Char_Gravitar\n"), ("name", b"  char_name: Harlowe\n")):
    fresh(look=True)
    fx.put(client, 4, HARLOWE_TEXT.replace(line, line * 2))
    before = snapshot()
    check(f"two identical {label} lines side by side refused, nothing written",
          run("Gravitar", "Paladin").reason == "prepare_failed" and snapshot() == before)
fresh(look=True)
trees.keep(G, "Paladin", fx.TREES["Paladin"])
fx.put(client, 4, fx.game_text(G, "Gravitar", "Harlowe", b"  - name: Progress_Stray\n"))
before = snapshot()
check("a tree put back that does not read back alone refused, nothing written",
      run("Gravitar", "Paladin").reason == "prepare_failed" and snapshot() == before)
fresh(look=True)
rest = b"  note: 1\n  - name: progress_graph_grav_more\n    group_def_name: progress_group_gravitar\n"
fx.put(client, 4, fx.game_text(G, "Gravitar", "Harlowe", fx.TREES["Gravitar"] + rest))
before = snapshot()
check("a line of the old hunter's group left after its tree refused, nothing written",
      run("Gravitar", "Paladin").reason == "prepare_failed" and snapshot() == before)
fresh(look=True)
real_with_hunter = save_text.with_hunter
save_text.with_hunter = lambda text, hunter, name: real_with_hunter(text, hunter, name).replace(
    G.encode(), fx.VEX_GAME.encode())
before = snapshot()
try:
    other_game = run("Gravitar", "Paladin").reason
finally:
    save_text.with_hunter = real_with_hunter
check("a text prepared showing another game refused, nothing written",
      other_game == "prepare_failed" and snapshot() == before)
fresh(look=True)
trees.path().write_text("{ not json", encoding="utf-8")
trees.forget()
before = snapshot()
check("an unreadable trees file blocks the change, nothing written",
      run("Gravitar", "Paladin").reason == "trees_unreadable" and snapshot() == before)

fresh(look=True)
if backups.folder().is_dir():
    backups.folder().rmdir()  # emptied by fresh(): a file in its place makes the copy fail
backups.folder().parent.mkdir(parents=True, exist_ok=True)
backups.folder().write_bytes(b"")
check("no backup: nothing changed, the look kept", run("Gravitar", "Paladin").reason == "backup_failed"
      and text() == HARLOWE_TEXT and trees.kept(G, "Gravitar") is None and choices.chosen(G) == LOOK)
backups.folder().unlink()

fresh(look=True)
real_keep = trees.keep
trees.keep = lambda *_args: False
check("the tree not kept: the save unchanged, a spare backup, the look kept",
      run("Gravitar", "Paladin").reason == "trees_failed" and text() == HARLOWE_TEXT and backed_up() == [original]
      and choices.chosen(G) == LOOK)
trees.keep = real_keep

fresh(look=True)
treeless = fx.put(client, 4, fx.game_text(G, "Gravitar", "Harlowe", None)).read_bytes()
real_drop = trees.drop
trees.drop = lambda *_args: False
check("no tree left and none dropped: the save unchanged, a spare backup, the look kept",
      run("Gravitar", "Paladin").reason == "trees_failed" and (client / "4.sav").read_bytes() == treeless
      and backed_up() == [treeless] and choices.chosen(G) == LOOK)
trees.drop = real_drop


def in_client(target: object) -> bool:
    return pathlib.Path(target).parent == client


fresh(look=True)
os.replace = lambda source, target: ((_ for _ in ()).throw(PermissionError("held")) if in_client(target)
                                     else real_replace(source, target))
since = len(state["logs"])
outcome = run("Gravitar", "Paladin")
os.replace = real_replace
number = re.search(r"switch (\w+):", state["logs"][since]).group(1)
check("a save held three times: not written and said with the change's number, the tries 0.1 then 0.2 s apart, "
      "the look kept", outcome.reason == "write_failed" and text() == HARLOWE_TEXT and pauses == [0.1, 0.2]
      and any(f"switch {number}: a save could not be written" in error for error in state["errors"])
      and choices.chosen(G) == LOOK)
check("no temporary file left after a failed write", names() == ["1.sav", "4.sav"])

fresh()
held = [2]


def held_twice(source, target):
    if in_client(target) and held[0]:
        held[0] -= 1
        raise PermissionError("held")
    return real_replace(source, target)


os.replace = held_twice
outcome = run("Gravitar", "Paladin")
os.replace = real_replace
check("a save held twice then free: written", outcome.done and pauses == [0.1, 0.2]
      and save_text.header(text())["hunter"] == "Char_Paladin")

fresh(look=True)
garbled = [1]


def garble_once(source, target):
    real_replace(source, target)
    if in_client(target) and garbled[0]:
        garbled[0] -= 1
        pathlib.Path(target).write_bytes(b"x" * 16)


os.replace = garble_once
outcome = run("Gravitar", "Paladin")
os.replace = real_replace
check("read back different: the save restored as it was, the look kept", outcome.reason == "restored"
      and (client / "4.sav").read_bytes() == original and choices.chosen(G) == LOOK)


def garble_always(source, target):
    real_replace(source, target)
    if in_client(target):
        pathlib.Path(target).write_bytes(b"x" * 16)


fresh(look=True)
os.replace = garble_always
outcome = run("Gravitar", "Paladin")
os.replace = real_replace
check("not restored: said, and the backup holds the save, the look kept", outcome.reason == "restore_failed"
      and backed_up() == [original] and any("did not read back" in error for error in state["errors"])
      and choices.chosen(G) == LOOK)


def garble_then_hold(source, target):
    if in_client(target) and saves_written[0]:
        raise PermissionError("held")
    real_replace(source, target)
    if in_client(target):
        saves_written[0] += 1
        pathlib.Path(target).write_bytes(b"x" * 16)


fresh()
saves_written = [0]
os.replace = garble_then_hold
outcome = run("Gravitar", "Paladin")
os.replace = real_replace
check("not put back: said as it is, never as a save unchanged", outcome.reason == "restore_failed"
      and (client / "4.sav").read_bytes() == b"x" * 16 and backed_up() == [original]
      and any("did not read back" in error for error in state["errors"])
      and not any("unchanged" in error for error in state["errors"]))

fresh(look=True)
real_read = pathlib.Path.read_bytes
pathlib.Path.read_bytes = lambda path: ((_ for _ in ()).throw(PermissionError("held")) if path == client / "4.sav"
                                        else real_read(path))
outcome = run("Gravitar", "Paladin")
pathlib.Path.read_bytes = real_read
check("not readable back: left as written, nothing put back over it, the look kept", outcome.reason == "unverified"
      and pauses == [0.1, 0.2] and save_text.header(text())["hunter"] == "Char_Paladin" and choices.chosen(G) == LOOK)

fresh(look=True)
garbled = [1]
reads = [0]


def restored_held(path):
    """The changed save read back once, garbled; the save put back then held at its own read back."""
    if path == client / "4.sav":
        reads[0] += 1
        if reads[0] > 1:
            raise PermissionError("held")
    return real_read(path)


os.replace, pathlib.Path.read_bytes = garble_once, restored_held
try:
    outcome = run("Gravitar", "Paladin")
finally:
    os.replace, pathlib.Path.read_bytes = real_replace, real_read
check("the save put back held at its read back: not taken for restored, said, the look kept",
      outcome.reason == "restore_failed" and (client / "4.sav").read_bytes() == original
      and any("did not read back" in error for error in state["errors"]) and choices.chosen(G) == LOOK)

fresh()
real_read = save_places._read
held_once = [1]


def read_held_once(path):
    if path == client / "4.sav" and held_once[0]:
        held_once[0] -= 1
        raise PermissionError("held")
    return real_read(path)


save_places._read = read_held_once
outcome = run("Gravitar", "Paladin")
save_places._read = real_read
check("a save held an instant while it is looked for: found, the pause through the caller's sleep",
      outcome.done and pauses == [0.1])

fresh()
(client / ("4.sav" + file_replace.TEMPORARY_SUFFIX)).write_bytes(b"cut")
check("a temporary file left by a cut removed by the next write", run("Gravitar", "Paladin").done
      and names() == ["1.sav", "4.sav"])

for label, content in (("an unreadable choices file", "{ not json"), ("a choices file nested too deep", "[" * 5000)):
    fresh()
    choices.path().write_text(content, encoding="utf-8")
    choices.forget()
    try:
        done = run("Gravitar", "Paladin").done
    except RecursionError:
        done = False
    check(f"{label} left as it is, the change done", done
          and choices.path().read_text(encoding="utf-8") == content)
choices.path().unlink()

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
