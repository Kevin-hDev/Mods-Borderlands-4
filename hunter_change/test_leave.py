"""The hunter change asked in a game: refused, nothing started, for an unknown or the same hunter, a game id not a
game's, zero or two live game modes, a request already in progress, a clock or a hook that does not start (the clock
stopped again); accepted, the hook on and the clock started, the return called at the first tick only and said before;
a hook that does not stop leaving the clock stopped and the next request free; no return when the tick finds not
exactly one live mode or the call raises; the title screen's signal ignored before the call, while a character is
played, and on another game (said once), the right one still taken after them; the save changed once it stays still
SETTLE_S after the signal, the wait started again at each write, not at 1.9 s, nor while it cannot be read (said
once); given up without writing past AFTER_CALL_S without the signal or with a save still moving, past AFTER_SIGNAL_S
with a save still moving; ended as loaded, writing nothing, with a game loaded or loading meanwhile (a character, or no
controller); another game selected meanwhile not a reason; no save found, or the game in two saves, nothing written
and the reason kept; an end of the change itself
(done, error inside it) with the stamp of the save as the change left it, taken after the change wrote it, and leave's
own ends (no_return, gave_up, loaded) with none, the save known or not; cancelled, nothing written, the last end kept,
one clock for the session; a tick that raises gives up, said once; an error inside the change itself ends as error;
the last end taken once by its game's page, kept for another game's;
every line of a request numbered alike, no path nor account number in the log. No real timer and no real save: the
clock, the game modes and the change are the test's, the saves those of save_fixture.py."""

import importlib
import re
import sys
from types import SimpleNamespace

import sdk_stubs

state = sdk_stubs.install()

import fake_game  # noqa: E402
import save_fixture as fx  # noqa: E402
from hunter_change import leave, report, save_places, switch  # noqa: E402
from hunter_change.pack import NAME  # noqa: E402

fails: list[str] = []
G, CURRENT, WANTED = fx.HARLOWE_GAME, "Gravitar", "Paladin"
HARLOWE = fx.game_text(G, CURRENT, "Harlowe", fx.TREES["Gravitar"])
# Closed, 320 bytes where HARLOWE's save is 336 and its full-size one 12480: the change always writes another size.
AMON = fx.game_text(G, WANTED, "Amon", fx.TREES["Paladin"])
documents, client = fx.saves_folder()
path = client / "4.sav"
empty_documents = fx.saves_folder()[0]
places = [documents]
# The search without places asks this: never the real Documents folder.
save_places.documents_candidates = lambda: list(places)
LINE = re.compile(rf"\[{re.escape(NAME)}\] leave ([0-9a-f]{{6}}): ")
clock = [0.0]
modes: list = []
timers: list = []
changes: list = []
written: list = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


class FakeTimer:
    """The Windows timer as leave uses it: its target kept while started, its starts and stops counted; started twice
    without a stop, it refuses, as NativeTimer does."""

    def __init__(self) -> None:
        self.target, self.starts, self.stops = None, 0, 0

    def start(self, target) -> None:
        if self.target is not None:
            raise RuntimeError("Menu timer still registered")
        self.target, self.starts = target, self.starts + 1

    def stop(self) -> None:
        self.target, self.stops = None, self.stops + 1


class DeadTimer(FakeTimer):
    def start(self, target) -> None:
        raise RuntimeError("Menu timer unavailable")


class FakeMode:
    """The live game mode: its calls to ReturnToMainMenuHost counted with the log as it stood then, or refused."""

    def __init__(self, refuse: bool = False) -> None:
        self.refuse, self.calls, self.logs_at_call = refuse, 0, []

    def ReturnToMainMenuHost(self) -> None:
        self.calls += 1
        self.logs_at_call = list(state["logs"])
        if self.refuse:
            raise RuntimeError("refused")


def new_timer(kind=FakeTimer) -> FakeTimer:
    timers.append(kind())
    return timers[-1]


def stamp_of_file() -> tuple[int, int]:
    status = path.stat()
    return status.st_mtime_ns, status.st_size


def fake_change(game: str, current: str, wanted: str, places=None, sleep=None) -> switch.Outcome:
    """switch.change as leave sees it: the save written as Amon's, and the stamp of the file it wrote noted."""
    changes.append((game, current, wanted))
    fx.put(client, 4, AMON)
    written.append(stamp_of_file())
    return switch.Outcome(switch.DONE)


switch.change = fake_change


def raising(*_args, **_kwargs) -> None:
    raise RuntimeError("broken")


def in_game(game: str = G) -> None:
    state["pc"] = SimpleNamespace(OakCharacter=object(),
                                  PlayerState=SimpleNamespace(ActiveCharGuid=fake_game.id_words(game)))


def title(game: str = G) -> None:
    state["pc"] = SimpleNamespace(OakCharacter=None,
                                  PlayerState=SimpleNamespace(ActiveCharGuid=fake_game.id_words(game)))


def fresh(live: list | None = None) -> FakeMode | None:
    """The module as loaded, the game in play with one live mode (or these), its save back in its folder; the mode."""
    importlib.reload(leave)
    leave.now, leave.new_timer, leave.live_modes = (lambda: clock[0]), new_timer, (lambda: list(modes))
    modes[:] = [FakeMode()] if live is None else live
    clock[0] = 0.0
    places[:] = [documents]
    timers.clear()
    changes.clear()
    written.clear()
    report.reset()
    fx.put(client, 4, HARLOWE)
    in_game()
    return modes[0] if modes else None


def ask(wanted: str = WANTED) -> bool:
    return leave.ask(G, CURRENT, wanted)


def tick(at: float) -> None:
    """A tick of the clock at `at`; none once it is stopped, as with the real timer."""
    clock[0] = at
    if timers and timers[-1].target is not None:
        timers[-1].target()


def signal(at: float, game: str = G) -> None:
    """The title screen ready at `at` with this game selected, no character."""
    clock[0] = at
    title(game)
    leave.ready(None, None, None, None)


def to_settling() -> None:
    """Asked, returned at 0 s, the title screen ready on the game at 1 s and its save found at the tick."""
    ask()
    tick(0.0)
    signal(1.0)
    tick(1.0)


def stopped() -> bool:
    """The hook off, the clock stopped, no request left."""
    return (not leave.ready.enabled and timers[-1].target is None and timers[-1].stops >= 1 and not leave.busy())


def ended(reason: str, changed: int = 0) -> bool:
    last = leave.STATE.last
    return stopped() and last is not None and last.outcome.reason == reason and len(changes) == changed


def end_stamp() -> object:
    """The stamp the last end carries; "missing" when it carries none at all."""
    return getattr(leave.STATE.last, "stamp", "missing")


def refused_quietly(asked: bool) -> bool:
    return (asked is False and not timers and not leave.ready.enabled and not leave.busy()
            and all(mode.calls == 0 for mode in modes))


def numbered(lines: list[str]) -> bool:
    """Every line starts with the request's operation number, the same from start to end."""
    found = [LINE.match(line) for line in lines]
    return bool(lines) and all(found) and len({match.group(1) for match in found}) == 1


# 1. Refusals: nothing started.
fresh()
quiet = [refused_quietly(leave.ask(G, "Nobody", WANTED)), refused_quietly(ask("Nobody")), refused_quietly(ask(CURRENT))]
quiet += [refused_quietly(leave.ask(game, CURRENT, WANTED)) for game in ("../x", G.lower(), None)]
fresh([])
quiet.append(refused_quietly(ask()))
fresh([FakeMode(), FakeMode()])
quiet.append(refused_quietly(ask()))
fresh()
leave.new_timer = lambda: new_timer(DeadTimer)
errors = len(state["errors"])
dead = ask()
quiet.append(dead is False and not leave.ready.enabled and not leave.busy() and len(state["errors"]) == errors + 1)
check("asking refused, nothing started: an unknown or the same hunter, a game id not a game's, zero or two live game "
      "modes, a clock that does not start (said)", quiet == [True] * 9)
mode = fresh()
leave.ready.enable = raising
errors = len(state["errors"])
try:
    hooked = ask()
except Exception:
    hooked = None
tick(0.0)
check("a hook that does not start: asking refused and said, the clock stopped again, no return at the next tick",
      hooked is False and timers[-1].target is None and mode.calls == 0 and not leave.busy()
      and len(state["errors"]) == errors + 1)
mode = fresh()
ask()
leave.ready.disable = raising
modes.clear()
errors = len(state["errors"])
tick(0.0)
released = timers[-1].target is None and not leave.busy() and len(state["errors"]) == errors + 1
del leave.ready.disable
modes.append(mode)
check("a hook that does not stop: the clock still stopped, said, and a next request starts",
      released and ask() is True and timers[-1].starts == 2)
fresh()
first = ask()
errors = len(state["errors"])
again = ask("DarkSiren")
quiet_again = again is False and len(state["errors"]) == errors
to_settling()
tick(3.0)
check("asking again while a request is in progress refused without an error line, the first one kept and done",
      first is True and quiet_again and len(timers) == 1 and timers[0].starts == 1
      and changes == [(G, CURRENT, WANTED)])

# 2. Accepted: the return called at the first tick only.
mode = fresh()
since = len(state["logs"])
accepted = ask()
check("asking accepted: busy, the hook on, the clock started, no return called before the first tick",
      accepted is True and leave.busy() and leave.ready.enabled and timers[-1].starts == 1
      and timers[-1].target is not None and mode.calls == 0)
tick(0.0)
tick(0.5)
check("at the first tick, ReturnToMainMenuHost called once, said before the call",
      mode.calls == 1 and any("calling ReturnToMainMenuHost" in line for line in mode.logs_at_call[since:])
      and leave.busy())

# 3. No return.
ends = []
fresh()
ask()
modes.clear()
tick(0.0)
ends.append(ended(leave.NO_RETURN) and end_stamp() is None)
mode = fresh()
ask()
modes.append(FakeMode())
tick(0.0)
ends.append(ended(leave.NO_RETURN) and mode.calls == 0 and end_stamp() is None)
mode = fresh([FakeMode(refuse=True)])
ask()
tick(0.0)
ends.append(ended(leave.NO_RETURN) and mode.calls == 1 and end_stamp() is None)
check("at the tick, zero or two live game modes, or the call raising: finished no_return, hook and clock stopped, "
      "no stamp since no save was found", ends == [True] * 3)

# 4. Signals ignored.
mode = fresh()
ask()
signal(0.0)
in_game()
tick(0.0)
check("the title screen's signal before the call ignored: the return still called at the first tick", mode.calls == 1)
in_game()
leave.ready(None, None, None, None)
since = len(state["logs"])
signal(1.0, fx.VEX_GAME)
said_once = len(state["logs"]) - since
signal(1.5, fx.VEX_GAME)
said_again = len(state["logs"]) - since
tick(2.0)
tick(5.0)
check("the signal ignored while a character is played and on another game, said once",
      not changes and leave.busy() and said_once == 1 and said_again == 1
      and "another game" in state["logs"][since])
signal(6.0)
tick(6.0)
tick(8.0)
check("the right signal after them still taken", ended(switch.DONE, changed=1))

# 5. The save changed once it stays still, the wait started again at each write; 12. its lines numbered.
fresh()
since = len(state["logs"])
to_settling()
fx.put(client, 4, fx.full_size(HARLOWE))
tick(2.5)
tick(3.5)
tick(4.25)
check("the save found and watched: nothing changed while it moves, the wait started again at each write",
      not changes and leave.busy() and any("wrote the save again" in line for line in state["logs"][since:]))
settled = leave.STATE.stamp
tick(4.5)
last = leave.STATE.last
check("2 s of clock without a write: the change made once with the request's game and hunters, then finished",
      ended(switch.DONE, changed=1) and changes == [(G, CURRENT, WANTED)]
      and (last.game, last.current, last.wanted, last.outcome) == (G, CURRENT, WANTED, switch.Outcome(switch.DONE)))
check("the done end carries the stamp of the file the change wrote, not the one the wait saw before it",
      len(written) == 1 and end_stamp() == written[0] == stamp_of_file() and settled is not None
      and written[0] != settled)
check("every line of a request starts with its operation number, the same from start to end",
      numbered(state["logs"][since:]) and len(state["logs"]) - since >= 5)

# 6. Not before 2 s.
fresh()
to_settling()
tick(2.9)
early = not changes and leave.busy()
tick(3.0)
check("1.9 s without a write: not changed yet; at 2 s changed", early and ended(switch.DONE, changed=1))

# 7. Given up past the bounds.
fresh()
ask()
tick(0.0)
tick(59.5)
waiting = leave.busy()
tick(60.5)
check("no title screen signal 60 s after the call: given up, nothing changed, no stamp since no save was found",
      waiting and ended(leave.GAVE_UP) and end_stamp() is None)


def keep_writing(times: list[float]) -> None:
    """The save written again before each tick at these times, each time with another size."""
    data = path.read_bytes()
    for count, at in enumerate(times):
        path.write_bytes(data + b"x" * (count % 2 + 1))
        tick(at)


fresh()
to_settling()
keep_writing([float(second) for second in range(2, 22)])
moving = not changes and leave.busy()
tick(21.5)
check("a save still moving 20 s after the signal: given up, nothing changed, no stamp though the save was found",
      moving and ended(leave.GAVE_UP) and end_stamp() is None)
fresh()
ask()
tick(0.0)
signal(50.0)
tick(50.0)
keep_writing([float(second) for second in range(51, 61)])
moving = not changes and leave.busy()
keep_writing([60.5])
check("the signal at 50 s, the save still moving 60 s after the call: given up, nothing changed, no stamp",
      moving and ended(leave.GAVE_UP) and end_stamp() is None)

# 8. No save.
fresh()
places[:] = [empty_documents]
to_settling()
check("no save of the game at the title screen: finished no_save, nothing changed", ended("no_save"))
fresh()
fx.put(client, 7, HARLOWE)
to_settling()
check("the game in two saves at the title screen: finished two_saves, nothing changed",
      ended(save_places.TWO_SAVES))
(client / "7.sav").unlink()

# 9. A game loading or loaded meanwhile; another game selected is not one.
fresh()
to_settling()
in_game()
tick(1.5)
check("a game loaded during the wait: ended as loaded, nothing changed, no stamp though the save was found",
      ended("loaded") and end_stamp() is None)
fresh()
to_settling()
state["pc"] = None
tick(1.5)
check("no controller during the wait, a game loading: ended as loaded, nothing changed", ended("loaded"))
fresh()
to_settling()
state["pc"] = None
tick(2.0)
title()
tick(3.1)
check("no controller, then one without a character: ended as loaded, nothing changed", ended("loaded"))
fresh()
to_settling()
title(fx.VEX_GAME)
tick(3.0)
check("another game selected during the wait: the change still made, by the request's game",
      ended(switch.DONE, changed=1) and changes == [(G, CURRENT, WANTED)])

# The save unreadable a while: said once, the wait started again until it reads.
fresh()
to_settling()
data = path.read_bytes()
path.unlink()
since = len(state["logs"])
for at in (1.5, 2.0, 2.5, 3.5):
    tick(at)
unreadable_lines = state["logs"][since:]
path.write_bytes(data)
tick(4.0)
waited = not changes and leave.busy()
tick(6.0)
check("a save that cannot be read a while: said once, not changed meanwhile, changed once still again",
      len(unreadable_lines) == 1 and "cannot be read" in unreadable_lines[0] and waited
      and ended(switch.DONE, changed=1))

# 10. Cancelled.
fresh()
to_settling()
tick(3.0)
done = leave.STATE.last
ask()
tick(4.0)
signal(5.0)
tick(5.0)
leave.cancel()
check("cancelled during the wait: hook and clock stopped, nothing changed, the last end kept, one clock kept",
      done is not None and done.outcome.done and stopped() and changes == [(G, CURRENT, WANTED)]
      and leave.STATE.last is done and len(timers) == 1 and timers[0].starts == 2)

# 11. A tick that raises.
fresh()
since, errors = len(state["logs"]), len(state["errors"])
ask()
tick(0.0)
signal(1.0)
real_stamp = save_places.stamp


def unreadable(save: save_places.Save) -> None:
    raise PermissionError(13, "Access is denied", str(save.path))


save_places.stamp = unreadable
try:
    tick(1.0)
finally:
    save_places.stamp = real_stamp
said = state["errors"][errors:]
check("a tick that raises: given up, one error line numbered as the request's, nothing changed",
      ended(leave.GAVE_UP) and len(said) == 1 and numbered(state["logs"][since:] + said))
fresh()
switch.change = raising
try:
    to_settling()
    tick(3.0)
finally:
    switch.change = fake_change
last = leave.STATE.last
check("an error inside the change itself: finished error, not gave_up, hook and clock stopped, with the stamp of the "
      "save as the change left it", stopped() and last is not None and last.outcome.reason == "error"
      and end_stamp() == stamp_of_file())


def unverified_change(game: str, current: str, wanted: str, places=None, sleep=None) -> switch.Outcome:
    fake_change(game, current, wanted)
    return switch.Outcome("unverified")


fresh()
switch.change = unverified_change
try:
    to_settling()
    tick(3.0)
finally:
    switch.change = fake_change
check("any other end of the change itself, unverified: the stamp of the file the change wrote",
      ended("unverified", changed=1) and end_stamp() == written[0] == stamp_of_file())

# 12. The last end taken by the page.
fresh()
to_settling()
tick(3.0)
done = leave.STATE.last
take_last = getattr(leave, "take_last", lambda _game: "missing")
check("the last end asked for another game: nothing, and kept for its own",
      done is not None and take_last(fx.VEX_GAME) is None and leave.STATE.last is done)
check("the last end asked for its game: given once, then forgotten",
      take_last(G) is done and take_last(G) is None and leave.STATE.last is None)

# 13. No path nor account number anywhere.
check("no path nor account number in the whole log",
      not any(re.search(r"\d{17}", line) or str(documents) in line or str(empty_documents) in line or ".sav" in line
              for line in state["logs"] + state["errors"]))

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
