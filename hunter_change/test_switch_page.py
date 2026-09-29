"""The HUNTER page's state: nowhere without a controller or with a new game selected, nothing read; in a game, the cards
with the played hunter; at the title screen, the cards with the hunter the save says, not the controller's; no card and
only why for a save missing or unreadable, a game in two saves, a hunter the mod does not know, an unreadable trees
file, a save of another hunter than the one played; busy while a change asked in a game runs, the save not read; the
save read again only when the place or the request changes, never at a poll that finds nothing new; in a game, a click
on another hunter asks for a confirmation telling whether its tree is kept, a click on the own hunter or an unknown code
doing nothing, no save written; cancel back to the cards; RETURN TO MAIN MENU asking leave.py for this game and change,
then busy at once, a refusal said on the cards, nothing asked outside the confirmation; at the title screen, a click
changing the save at once and saying so, a failed change said with the hunter unchanged or with no card, a change that
raises kept inside the page, said as an error and logged once without a path; the end of a change asked in a game said
once, in the game or at the title screen, for its own game only, with cards or without, never taken while busy; an end
of the change itself dropped unsaid once the game has written the save since, and still said when the save is not found
or the trees file cannot be read, with nothing to compare; leave's own ends, which carry no stamp, said once whatever
the game wrote since; the trees file read again at each reading, so that a file changed since is seen; a click or RETURN
TO MAIN MENU on a place changed since the last poll doing nothing but follow it, and no search when nothing changed; the
page's places carried to every search. No real save: every page gets the folder of save_fixture.py, and the Documents
folder is never asked."""

import sys
from types import SimpleNamespace

import sdk_stubs

state = sdk_stubs.install()

import fake_game  # noqa: E402
import save_fixture as fx  # noqa: E402
from hunter_change import hunters, leave, report, save_codec, save_places, save_text, switch, trees  # noqa: E402
from hunter_change.switch_page import (BUSY, CARDS, CONFIRM, NOWHERE, UNAVAILABLE, SwitchPage,  # noqa: E402
                                       View)

fails: list[str] = []
G = fx.HARLOWE_GAME
HARLOWE, AMON, VEX = hunters.by_code("Gravitar"), hunters.by_code("Paladin"), hunters.by_code("DarkSiren")
documents, client = fx.saves_folder()
PLACES = [documents]
asked_documents: list[int] = []


def documents_asked() -> list:
    """Never the real Documents folder: the fixture's, and the question counted."""
    asked_documents.append(1)
    return list(PLACES)


save_places.documents_candidates = documents_asked
real_find, real_change = save_places.find, switch.change
finds: list[str] = []
changes: list[tuple] = []
asks: list[tuple] = []
leave_state = SimpleNamespace(busy=False, accepts=True)
change_outcome = [switch.Outcome(switch.DONE)]


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def counted_find(*args, **kwargs):
    finds.append(args[0])
    return real_find(*args, **kwargs)


def fake_change(game: str, current: str, wanted: str, places=None, sleep=None) -> switch.Outcome:
    changes.append((game, current, wanted, places))
    return change_outcome[0]


def fake_ask(game: str, current: str, wanted: str) -> bool:
    """leave.ask as the page sees it: a request accepted makes leave busy."""
    asks.append((game, current, wanted))
    leave_state.busy = leave_state.busy or leave_state.accepts
    return leave_state.accepts


save_places.find = counted_find
# leave's last end is the module's own (leave.STATE.last), so that the page takes it as leave.py gives it.
leave.ask, leave.busy = fake_ask, (lambda: leave_state.busy)


def save_bytes(slot: int = 4) -> bytes:
    return (client / f"{slot}.sav").read_bytes()


def saved_hunter(slot: int = 4) -> str:
    return save_text.header(save_codec.decode(save_bytes(slot), fx.ACCOUNT))["hunter"]


def stamp_now(slot: int = 4) -> tuple[int, int]:
    """The save's stamp as the file stands now."""
    status = (client / f"{slot}.sav").stat()
    return status.st_mtime_ns, status.st_size


def end(reason: str, stamp: tuple[int, int] | None = None, game: str = G, current: str = "Gravitar") -> leave.Result:
    """The end of a request for Amon, as leave.py keeps it."""
    return leave.Result(game, current, "Paladin", switch.Outcome(reason), stamp)


def rewritten(code: str) -> None:
    """The save written again by the game, the same game and hunter, another size."""
    fx.put(client, 4, fx.full_size(fx.game_text(G, code, hunters.by_code(code).name, fx.TREES.get(code))))


def fresh(code: str | None = "Gravitar") -> None:
    """The Harlowe game's save showing `code` (none when None) in slot 4, no trees file, no request, the fakes back."""
    for path in client.iterdir():
        path.unlink()
    if code is not None:
        fx.put(client, 4, fx.game_text(G, code, hunters.by_code(code).name, fx.TREES.get(code)))
    trees.path().unlink(missing_ok=True)
    trees.forget()
    leave_state.busy, leave_state.accepts, leave.STATE.last = False, True, None
    report.reset()
    state["errors"].clear()
    change_outcome[0] = switch.Outcome(switch.DONE)
    switch.change = fake_change
    for recorded in (finds, changes, asks):
        recorded.clear()


def click_raises(page: SwitchPage, code: str) -> bool:
    """Whether the click let an exception out to the window."""
    try:
        page.click(code)
    except Exception:
        return True
    return False


def playing(code: str = "Gravitar", game: str = G) -> None:
    fake_game.load(state, code, game)


def title(game: str = G, played: str | None = None) -> None:
    """The title screen with this game selected: a controller without a character; `played` names a character
    definition the player state would still hold."""
    extra = {"ReplicatedCharacterDef": f"Char_{played}"} if played else {}
    state["pc"] = SimpleNamespace(OakCharacter=None,
                                  PlayerState=SimpleNamespace(ActiveCharGuid=fake_game.id_words(game), **extra))


# 1. Nowhere.
fresh()
state["pc"] = None
page = SwitchPage(PLACES)
check("no controller: nowhere, no save read", page.view == View(NOWHERE) and finds == [])
title("0" * 32)
check("a new game selected, without an id: nowhere, no save read",
      SwitchPage(PLACES).view == View(NOWHERE) and finds == [])

# 2. In a game.
fresh()
playing()
view = SwitchPage(PLACES).view
check("in a game with its save: the cards, in the game, the played hunter",
      view.kind == CARDS and view.in_game and view.current == HARLOWE and view.said is None)

# 3. At the title screen, the save's hunter.
fresh("Paladin")
title(played="Gravitar")
view = SwitchPage(PLACES).view
check("at the title screen: the cards, not in the game, the hunter the save says and not the controller's",
      view.kind == CARDS and not view.in_game and view.current == AMON)

# 4. Unavailable, and why.
fresh(None)
title()
view = SwitchPage(PLACES).view
check("no save: no card, why no_save", view.kind == UNAVAILABLE and view.why == "no_save" and not view.in_game)
fresh()
(client / "4.sav").write_bytes(b"not a save")
playing()
view = SwitchPage(PLACES).view
check("a save that does not open: no card, why no_save", view.kind == UNAVAILABLE and view.why == "no_save")
fresh()
fx.put(client, 7, save_codec.decode(save_bytes(), fx.ACCOUNT))
playing()
view = SwitchPage(PLACES).view
check("a game in two saves: no card, why two_saves",
      view.kind == UNAVAILABLE and view.why == save_places.TWO_SAVES)
fresh(None)
fx.put(client, 4, fx.game_text(G, "Echo4", "Echo", None))
title()
view = SwitchPage(PLACES).view
check("a save whose hunter the mod does not know: no card, why unknown_hunter",
      view.kind == UNAVAILABLE and view.why == "unknown_hunter")
fresh()
trees.path().write_text("{", encoding="utf-8")
trees.forget()
title()
view = SwitchPage(PLACES).view
check("an unreadable trees file: no card, why trees_unreadable",
      view.kind == UNAVAILABLE and view.why == "trees_unreadable")
fresh("Paladin")
playing("Gravitar")
view = SwitchPage(PLACES).view
check("in a game, a save of another hunter than the one played: no card, why not_this_hunter",
      view.kind == UNAVAILABLE and view.why == "not_this_hunter" and view.in_game)

# 5. Busy.
fresh()
playing()
leave_state.busy = True
leave.STATE.last = end(leave.GAVE_UP)
page = SwitchPage(PLACES)
check("a change asked in a game running: busy, the save not read, the last end not taken",
      page.view == View(BUSY, True) and finds == [] and leave.STATE.last == end(leave.GAVE_UP))
page.click("Paladin")
check("a click while busy does nothing", page.view == View(BUSY, True) and changes == [] and asks == [])

# 6. Following the game.
fresh()
playing()
page = SwitchPage(PLACES)
finds.clear()
check("a poll with nothing new: no change, the save not read again", page.follow() is False and finds == [])
check("polled again: still nothing read", page.follow() is False and finds == [])
state["pc"] = None
check("the game left, loading: changed, nowhere, nothing read",
      page.follow() is True and page.view == View(NOWHERE) and finds == [])
title()
changed = page.follow()
check("then the title screen: changed, the save read once",
      changed is True and page.view.kind == CARDS and not page.view.in_game and len(finds) == 1)
check("then a poll with nothing new: not read again", page.follow() is False and len(finds) == 1)
leave_state.busy = True
check("a request starting at the same place: changed, busy, nothing read",
      page.follow() is True and page.view == View(BUSY) and len(finds) == 1)
leave_state.busy = False
check("the request ended: changed back, the save read once",
      page.follow() is True and page.view.kind == CARDS and len(finds) == 2)

# 7. A click in a game.
fresh()
playing()
before = save_bytes()
page = SwitchPage(PLACES)
page.click("Paladin")
view = page.view
check("in a game, a click on Amon: the confirmation, Amon wanted, no tree kept",
      view.kind == CONFIRM and view.in_game and view.current == HARLOWE and view.wanted == AMON and not view.kept)
check("the confirmation writes nothing and asks nothing yet", changes == [] and asks == [] and save_bytes() == before)
fresh()
playing()
check("Amon's tree kept for this game first", trees.keep(G, "Paladin", fx.TREES["Paladin"]))
page = SwitchPage(PLACES)
page.click("Paladin")
check("a click on Amon then: the confirmation says his tree is kept", page.view.kind == CONFIRM and page.view.kept)
fresh()
playing()
page = SwitchPage(PLACES)
cards = page.view
page.click("Gravitar")
check("a click on the own hunter: nothing changes", page.view == cards and changes == [] and asks == [])
page.click("Nobody")
check("an unknown code: nothing changes", page.view == cards and changes == [] and asks == [])

# 8. Cancel and RETURN TO MAIN MENU.
fresh()
playing()
page = SwitchPage(PLACES)
page.click("Paladin")
page.cancel()
check("cancel from the confirmation: the cards, the same hunter",
      page.view.kind == CARDS and page.view.current == HARLOWE and page.view.in_game and page.view.said is None)
page.click("Paladin")
check("RETURN TO MAIN MENU: leave.py asked this game and change, the window to close",
      page.leave() is True and asks == [(G, "Gravitar", "Paladin")] and changes == [])
check("the change asked: the page busy at once", page.view == View(BUSY, True))
page.cancel()
again = page.leave()
page.click("Paladin")
check("then cancel, a second RETURN TO MAIN MENU and a click: nothing, still busy, asked once",
      again is False and page.view == View(BUSY, True) and len(asks) == 1 and changes == [])
fresh()
playing()
leave_state.accepts = False
page = SwitchPage(PLACES)
page.click("Paladin")
refused = page.leave()
view = page.view
check("leave.py refusing: False, the cards saying no_return for Amon",
      refused is False and view.kind == CARDS and view.current == HARLOWE and view.said is not None
      and view.said.reason == leave.NO_RETURN and view.said_to == AMON)
fresh()
playing()
page = SwitchPage(PLACES)
check("RETURN TO MAIN MENU outside the confirmation: False, nothing asked", page.leave() is False and asks == [])

# 9. A click at the title screen, the real change.
fresh()
title()
switch.change = real_change
page = SwitchPage(PLACES)
page.click("Paladin")
view = page.view
check("at the title screen, a click on Amon: the save says Amon",
      saved_hunter() == "Char_Paladin" and asks == [])
check("the cards with Amon, saying done for Amon",
      view.kind == CARDS and not view.in_game and view.current == AMON and view.said is not None
      and view.said.reason == switch.DONE and view.said_to == AMON)

# 10. A failed change at the title screen.
fresh()
title()
change_outcome[0] = switch.Outcome("write_failed")
page = SwitchPage(PLACES)
page.click("Paladin")
view = page.view
check("a change that fails: the cards, the hunter unchanged, write_failed said",
      changes == [(G, "Gravitar", "Paladin", PLACES)] and view.kind == CARDS and view.current == HARLOWE
      and view.said is not None and view.said.reason == "write_failed")
fresh()
title()


def raising_change(game: str, current: str, wanted: str, places=None, sleep=None) -> switch.Outcome:
    changes.append((game, current, wanted, places))
    raise PermissionError(13, "Access is denied", str(client / "4.sav"))


switch.change = raising_change
page = SwitchPage(PLACES)
raised = click_raises(page, "Paladin")
view = page.view
check("a change that raises: kept inside the page, the cards, the hunter unchanged, an error said for Amon",
      not raised and view.kind == CARDS and view.current == HARLOWE and view.said == switch.Outcome(leave.ERROR)
      and view.said_to == AMON)
raised = click_raises(page, "Paladin")
check("the error written once in the log, without path nor account number",
      not raised and len(changes) == 2 and len(state["errors"]) == 1
      and "the change stopped after an error" in state["errors"][0]
      and str(documents) not in state["errors"][0] and str(fx.ACCOUNT) not in state["errors"][0])
fresh()
title()


def change_losing_save(game: str, current: str, wanted: str, places=None, sleep=None) -> switch.Outcome:
    changes.append((game, current, wanted, places))
    (client / "4.sav").unlink()
    return switch.Outcome("restore_failed")


switch.change = change_losing_save
page = SwitchPage(PLACES)
page.click("Paladin")
view = page.view
check("a change that fails and leaves no save found: no card, why no_save, restore_failed still said for Amon",
      view.kind == UNAVAILABLE and view.why == "no_save" and view.said is not None
      and view.said.reason == "restore_failed" and view.said_to == AMON)

# 11. The end of a change asked in a game.
fresh("Paladin")
title()
leave.STATE.last = end(switch.DONE, stamp_now())
page = SwitchPage(PLACES)
view = page.view
check("at the title screen, a done end whose save is as the change left it: said, for its wanted hunter, taken",
      view == View(CARDS, False, AMON, said=switch.Outcome(switch.DONE), said_to=AMON) and leave.STATE.last is None)
state["pc"] = None
page.follow()
title()
page.follow()
check("said once: not again at the next reading, after a load and back, nor on a page opened again",
      page.view == View(CARDS, False, AMON) and SwitchPage(PLACES).view == View(CARDS, False, AMON))
fresh("Paladin")
title()
leave.STATE.last = end(switch.DONE, stamp_now())
rewritten("Paladin")
view = SwitchPage(PLACES).view
check("the review's case, a done end whose save the game wrote since: not said, the plain title-screen view, the end "
      "taken all the same", view == View(CARDS, False, AMON) and leave.STATE.last is None)
fresh("Paladin")
playing("Paladin")
leave.STATE.last = end(switch.DONE, stamp_now())
rewritten("Paladin")
view = SwitchPage(PLACES).view
check("in a game, a done end whose save the game wrote since, the game loaded: not said, the plain cards, taken",
      view == View(CARDS, True, AMON) and leave.STATE.last is None)
fresh()
playing()
leave.STATE.last = end(leave.NO_RETURN)
view = SwitchPage(PLACES).view
check("in a game, a no_return end, which has no stamp: said in the cards in the game, for its wanted hunter, taken",
      view == View(CARDS, True, HARLOWE, said=switch.Outcome(leave.NO_RETURN), said_to=AMON)
      and leave.STATE.last is None)
check("then not again on a page opened again", SwitchPage(PLACES).view == View(CARDS, True, HARLOWE))
fresh()
playing()
leave.STATE.last = end(leave.LOADED)
rewritten("Gravitar")
view = SwitchPage(PLACES).view
check("in a game, a loaded end, the save written again at the load: said once in the cards, for its wanted hunter",
      view == View(CARDS, True, HARLOWE, said=switch.Outcome(leave.LOADED), said_to=AMON)
      and SwitchPage(PLACES).view == View(CARDS, True, HARLOWE))
fresh()
title()
leave.STATE.last = end(leave.GAVE_UP)
rewritten("Gravitar")
view = SwitchPage(PLACES).view
check("at the title screen, a gave_up end after the signal, the save written again since: said once, for Amon",
      view == View(CARDS, False, HARLOWE, said=switch.Outcome(leave.GAVE_UP), said_to=AMON)
      and SwitchPage(PLACES).view == View(CARDS, False, HARLOWE))
other = end(switch.DONE, None, fx.VEX_GAME, "DarkSiren")
for place in (playing, title):
    leave.STATE.last = other
    place()
    view = SwitchPage(PLACES).view
    check(f"{place.__name__}: the end of a request for another game, nothing said, kept for that game",
          view.kind == CARDS and view.said is None and view.said_to is None and leave.STATE.last is other)
fresh()
title()
leave.STATE.last = end("unverified", stamp_now())
(client / "4.sav").unlink()
view = SwitchPage(PLACES).view
check("an end of the change whose save is not found since: nothing to compare, said with no card",
      view.kind == UNAVAILABLE and view.why == "no_save" and view.said == switch.Outcome("unverified")
      and view.said_to == AMON and leave.STATE.last is None)
fresh()
trees.path().write_text("{", encoding="utf-8")
title()
leave.STATE.last = end("trees_unreadable", (1, 1))
view = SwitchPage(PLACES).view
check("an end with an unreadable trees file, its stamp not the save's: nothing compared, said with it",
      view.kind == UNAVAILABLE and view.why == "trees_unreadable"
      and view.said == switch.Outcome("trees_unreadable") and view.said_to == AMON)

# 12. The trees file read again at each reading.
fresh()
title()
page = SwitchPage(PLACES)
check("a readable trees file read", page.view.kind == CARDS)
trees.path().write_text("{", encoding="utf-8")
check("the file made unreadable since: the page opened again sees it",
      SwitchPage(PLACES).view == View(UNAVAILABLE, why="trees_unreadable"))
trees.path().unlink()
state["pc"] = None
page.follow()
title()
page.follow()
check("the file repaired since: the page following the game sees it", page.view.kind == CARDS)

# 13. A click or RETURN TO MAIN MENU on a place that changed since the last poll.
fresh()
playing()
page = SwitchPage(PLACES)
finds.clear()
page.click("Paladin")
page.leave()
check("the same place: the click and RETURN TO MAIN MENU act without a search", len(asks) == 1 and finds == [])
fresh()
title()
page = SwitchPage(PLACES)
playing()
page.click("Paladin")
check("a game loaded since the last poll: the click changes nothing, the page follows the game",
      changes == [] and page.view.kind == CARDS and page.view.in_game and page.view.current == HARLOWE)
fresh()
fx.put(client, 1, fx.game_text(fx.VEX_GAME, "DarkSiren", "Vex", fx.TREES["DarkSiren"]))
title()
page = SwitchPage(PLACES)
title(fx.VEX_GAME)
page.click("Paladin")
check("another game selected since: the click changes nothing, the page shows that game's hunter",
      changes == [] and page.view.kind == CARDS and page.view.current == VEX and not page.view.in_game)
fresh()
title()
page = SwitchPage(PLACES)
leave_state.busy = True
page.click("Paladin")
check("a request started since: the click changes nothing, the page busy", changes == [] and page.view == View(BUSY))
fresh()
playing()
page = SwitchPage(PLACES)
page.click("Paladin")
title()
left = page.leave()
check("the game left since the confirmation: RETURN TO MAIN MENU asks nothing, the page follows",
      left is False and asks == [] and page.view.kind == CARDS and not page.view.in_game)

check("the page's places carried to every search: the Documents folder never asked", asked_documents == [])

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
