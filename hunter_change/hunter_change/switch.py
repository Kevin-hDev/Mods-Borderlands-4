"""Changes the hunter of a saved game by writing its save, in the order that never loses a game nor a tree
(conception-idee-2.md, « Dans quel ordre », validated by Kevin on 2026-09-28): each step starts only when the one
before succeeded, and a step cut short leaves at worst a spare backup or a tree kept twice, never a damaged game.

Callers run it at the title screen, on the game selected there, once the game has written it for the last time: the
game rewrites a save it holds in memory (essais 6 and 34). The title screen stands still for about a third of a
second (four openings or closings of about 80 ms, essai 36), plus about 2 ms per save to find the game.
"""

import secrets
import time
from dataclasses import dataclass
from pathlib import Path

from . import backups, choices, file_replace, held_file, hunters, report, save_codec, save_places, save_text, trees

DONE = "done"
REFUSALS = ("unknown_hunter", save_places.NO_SAVE, save_places.TWO_SAVES, save_places.SAVES_UNSURE,
            save_places.SAVE_DAMAGED, "not_this_hunter", "foreign_tree", "trees_unreadable", "prepare_failed")
FAILURES = ("backup_failed", "trees_failed", "write_failed", "unverified", "restored", "restore_failed")


@dataclass(frozen=True)
class Outcome:
    reason: str
    first_time: bool = False

    @property
    def done(self) -> bool:
        return self.reason == DONE


def change(game: str, current: str, wanted: str, places: list[Path] | None = None, sleep=time.sleep) -> Outcome:
    """Makes the game's save one of `wanted`, from `current` as the caller showed it."""
    operation = secrets.token_hex(3)

    def say(step: str) -> None:
        report.note(f"switch {operation}: {step}")

    def stop(reason: str) -> Outcome:
        say(f"stopped, {reason}")
        return Outcome(reason)

    old, new = hunters.by_code(current), hunters.by_code(wanted)
    if old is None or new is None or old == new:
        return stop("unknown_hunter")
    # Said before the search, so that its own lines read as this change's.
    say(f"started, {old.name} to {new.name}")
    save = save_places.find(game, places, sleep)
    if isinstance(save, save_places.Missing):
        return stop(save.why)
    head = save_text.header(save.text)
    if head is None or head["game"] != game or head["hunter"] != hunters.CHARACTER_PREFIX + old.code:
        return stop("not_this_hunter")
    try:
        leaving = save_text.tree(save.text)
    except ValueError:
        return stop("foreign_tree")
    if leaving is not None and not trees.keepable(game, old.code, leaving):
        return stop("foreign_tree")
    if not trees.readable():
        return stop("trees_unreadable")
    arriving = trees.kept(game, new.code)
    try:
        name = save_text.followed_name(head["name"], old, new)
        text = save_text.with_tree(save_text.with_hunter(save.text, new, name), arriving)
        if not _shows(text, game, new, name, arriving, old):
            raise ValueError("the text prepared does not show the change")
        sealed = save_codec.encode(text, save.account)
        if save_codec.decode(sealed, save.account) != text:
            raise ValueError("the closed save does not open to the text")
    except ValueError:
        return stop("prepare_failed")
    say(f"slot {save.slot} prepared")
    if backups.save(game, save.data) is None:
        return stop("backup_failed")
    say("backed up")
    # The state left, tree or none: a tree kept from an earlier stay of this hunter must not come back later.
    if not (trees.keep(game, old.code, leaving) if leaving is not None else trees.drop(game, old.code)):
        return stop("trees_failed")
    say("tree kept" if leaving is not None else "no tree to keep")
    failed = _replace(save.path, sealed, sleep)
    if failed is not None:
        report.error_once("switch:write",
                          f"switch {operation}: a save could not be written ({failed}), it is unchanged")
        return stop("write_failed")
    say("written")
    written = _written(save.path, sealed, sleep)
    if written is None:
        # Renamed whole, the save is the new one or the old one, both whole: nothing is put back over it.
        return stop("unverified")
    if not written:
        failed = _replace(save.path, save.data, sleep)
        restored = failed is None and _written(save.path, save.data, sleep) is True
        if not restored:
            put_back = f" nor could be put back ({failed})" if failed is not None else ""
            report.error_once("switch:restore", f"switch {operation}: a changed save did not read back{put_back}, "
                                                "its backup holds the game as it was")
        return stop("restored" if restored else "restore_failed")
    say("read back")
    if choices.chosen(game) is not None:
        choices.choose(game, None)
    say(f"done, {'tree put back' if arriving is not None else 'no tree yet'}")
    return Outcome(DONE, first_time=arriving is None)


def _shows(text: bytes, game: str, new: hunters.Hunter, name: str, arriving: bytes | None, old: hunters.Hunter) -> bool:
    """Whether the text prepared reads back as the change meant: the game, the new hunter and its name in its header,
    the tree put back alone, no line of the old hunter's group left. A save edited by hand can make a change miss
    silently, two identical class lines side by side for one (final review, 2026-09-29); ValueError when its tree
    cannot be read."""
    head = save_text.header(text) or {}
    meant = (game, hunters.CHARACTER_PREFIX + new.code, name)
    return ((head.get("game"), head.get("hunter"), head.get("name")) == meant
            and save_text.tree(text) == arriving and old.tree_group not in save_text.groups(text))


def _replace(path: Path, data: bytes, sleep) -> str | None:
    """The file replaced whole, through a temporary file renamed over it: None when it was, else the name of the error
    that stopped it, for the caller to say what the save now is, which differs between a change and a restore. The
    temporary file ends in file_replace.TEMPORARY_SUFFIX, not .sav, so the game never lists it."""
    try:
        held_file.patiently(lambda: file_replace.replace(path, data), sleep)
        return None
    except OSError as error:
        return type(error).__name__


def _written(path: Path, data: bytes, sleep) -> bool | None:
    """Whether the file read back holds these bytes, whose text was checked before writing; None while another
    program holds it."""
    try:
        return held_file.patiently(path.read_bytes, sleep) == data
    except OSError:
        return None
