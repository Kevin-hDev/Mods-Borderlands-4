"""The team: up to MOST companions following the hunter together, the hook that drives them, and those on their way.

A team starts with the companions the player chose: each is called (respawn.Respawns.call), then born in front of the
hunter one beat after another once he may have one born (on foot, alive), found by its spawner and followed. A
companion dead comes back AFTER_S later the same way. One hook for the whole team, on the animation update, as It
Follows' heartbeat (frame.py) and the trials since 166: each follow keeps its own pace, rank by rank shifted so that
the samples do not all fall on one frame. session.py owns the team: it starts it, stops it, and stops it with the
mod. A hunter is Lemmy dressed at each birth (dress.py): a Lemmy coming back is born himself. As he is found, he
is handed to the team's wardrobe (wardrobe.py), which dresses him from the camera's update, never from this beat's
(decision 65: dressed from here, the game crashed since its update of 22 October 2026).
Each companion follows with the choice kept for its name on the window's card (choices.py), its shield and its speed,
the same at each of its births. The bars' service (bars.py: the bars on the left of the screen, the hunter aimed
at) publishes on the same beat and is stopped with the team.
"""

import time
from typing import Any, Callable

import unrealsdk
from mods_base import get_pc, hook
from unrealsdk.hooks import Type

from .. import camps, game_thread, report
from . import (birth, choices, choose, dress, fight, follow, kinds, main_menu, player_paint, respawn, wardrobe,
               world)
from .zone import zone_of

HOOK = "/Script/Engine.AnimInstance:BlueprintUpdateAnimation"
IDENTIFIER = "it_follows:companions"
MOST = choices.MOST
# A companion called back after an end that is no death: 3 in a row at most, the count forgotten after a follow of
# 60 s (Claude's choice: a map change ends every follow once; a companion taken away at each birth would loop).
RECALLS_MOST = 3
RECALL_KEPT_S = 60.0
# How often the team looks whether the main menu shows (main_menu.py).
MENU_EVERY_S = 1.0


def new_births() -> birth.Births:
    """The companions' camps for a whole game session, as the Horde's (session.py keeps them): a Births per team left
    up to MOST_CAMPS more spawners in the world at each start, never destroyed (trial 197: 5, then 8 more)."""
    return birth.Births(camps.Camps(report.announce, birth.MOST_CAMPS))


def offset(rank: int, every_s: float) -> float:
    """How far the samples of that rank are shifted from rank 0's."""
    return rank * every_s / MOST


def _player_own() -> player_paint.Own:
    """The player's colours and head (player_paint.py)."""
    return player_paint.of(get_pc())


class Team:
    """The follows running together and those on their way; clock() the follows' time; births asks a companion born
    (birth.Births); end(why) asks its owner (session.py) to stop it, at the main menu; menu() whether the main menu
    shows (main_menu.showing)."""

    def __init__(self, clock: Callable[[], float] = time.monotonic, births: Any = None,
                 end: Callable[[str], Any] | None = None, menu: Callable[[], bool | None] | None = None) -> None:
        self.clock = clock
        self.end = end
        self.menu = menu if menu is not None else lambda: main_menu.showing(get_pc())
        self.menu_next = -1.0
        # The last menu read said, so that the log tells the first and each change once.
        self.menu_shown: bool | str | None = "unread"
        self.follows: list = []
        # The hunters being dressed, MOST at most, as the follows.
        self.wardrobe = wardrobe.Wardrobe(clock, MOST)
        self.hook: Any = None
        # Made with the hook, on the game's thread: a beat that comes elsewhere does nothing (game_thread.py).
        self.guard: game_thread.Guard | None = None
        self.ended: str | None = None
        self.picks: dict[str, choices.Choice] = {}
        # Each companion's calls back in a row (_ended), MOST names at most: the team's own.
        self.recalls: dict[str, int] = {}
        # The bars on the left of the screen while they are on (bars.Bars), set and taken back by session.py.
        self.bars: Any = None
        self.births = births if births is not None else new_births()
        self.respawns = respawn.Respawns(lambda: respawn.looked(get_pc(), world, world.mode),
                                         lambda name: self.births.ask(kinds.BY_NAME[name].definition, get_pc()),
                                         self.join, report.note, MOST, clock)

    def active(self) -> list:
        return [one for one in self.follows if not one.done]

    def has(self, name: str) -> bool:
        return any(one.name == name for one in self.active())

    def free_rank(self) -> int:
        """The lowest rank no running follow holds; MOST when the team is full."""
        taken = {one.rank for one in self.active()}
        return next((rank for rank in range(MOST) if rank not in taken), MOST)

    def start(self, names: list[str], picks: dict[str, choices.Choice] | None = None) -> str:
        """Each companion named (kinds.py) called, MOST at most, a name it does not know left out, each with its
        choice in picks (the default for a name it lacks), and the hook set: started, or why not."""
        unknown = [name for name in names if name not in kinds.BY_NAME]
        chosen = [name for name in names if name in kinds.BY_NAME][:MOST]
        if not chosen:
            return "empty"
        self.picks = {name: (picks or {}).get(name, choices.Choice()) for name in chosen}
        for name in chosen:
            self.respawns.call(name, None)
        self.guard = game_thread.Guard("team")
        self.wardrobe.start()
        self.hook = hook(HOOK, Type.POST, hook_identifier=IDENTIFIER)(self.beat)
        self.hook.enable()
        report.note("team_start", companions=chosen, unknown=len(unknown),
                    choices={name: [pick.shielded, pick.speed, pick.outfit] for name, pick in self.picks.items()})
        return "started"

    def join(self, name: str, spawner: str, times: float | None) -> dict:
        """The companion of that name that spawner bore, dressed if a hunter, followed: started, or why not
        (not_found while it is not there yet)."""
        kind = kinds.BY_NAME.get(name)
        if kind is None:
            return {"done": "unknown"}
        if len(self.active()) >= MOST:
            return {"done": "team_full"}
        pc = get_pc()
        here = world.place(world.hunter(pc))
        if here is None:
            return {"done": "no_character"}
        actor, zone, text = choose.choose(fight.characters(pc), world, zone_of, kind.definition, here, spawner)
        if actor is None:
            return {"done": "not_found"}
        if self.has(str(actor.Name)):
            return {"done": "followed_already"}
        if zone is None:
            return {"done": "no_zone", "zone": text}
        rank = self.free_rank()
        dressed = {} if kind.look is None else {"dressed": self._dress(actor, kind.look, name)}
        one = follow.Follow(actor, zone, self.clock, rank, kind.definition, times, offset(rank, follow.EVERY_S),
                            self.picks.get(name, choices.Choice()))
        one.on_death = lambda _definition, health: self.respawns.died(name, health)
        one.on_end = lambda why, ended=one: self._ended(name, ended, why)
        one.companion = name
        self.follows = self.active() + [one]
        report.note("companion_start", character=one.name, companion=name, rank=rank, **dressed, **one.begin(pc))
        return {"done": "started"}

    def _ended(self, name: str, ended: Any, why: str) -> None:
        """A follow ended otherwise than by a death, its companion taken out of the world (leave.py): called back
        near the hunter, as after a map change (decision 59, Kevin, 22 October 2026: « Elle revient seule »), unless
        the team stops. RECALLS_MOST in a row at most, the count forgotten once a follow lasted RECALL_KEPT_S: a
        companion the game takes away at each birth must not be asked forever."""
        if self.ended is not None:
            return
        if self.clock() - ended.started >= RECALL_KEPT_S:
            self.recalls.pop(name, None)
        count = self.recalls.get(name, 0)
        if count >= RECALLS_MOST:
            report.note("companion_not_recalled", companion=name, why=why, recalls=count)
            return
        self.recalls[name] = count + 1
        report.note("companion_recalled", companion=name, why=why, recalls=count + 1)
        self.respawns.call(name, ended.times)

    def _dress(self, actor: Any, look: str, name: str) -> str:
        """A hunter handed to the wardrobe, with the player's colours when his card asks for them."""
        player = self.picks.get(name, choices.Choice()).outfit == "player"
        dressing = dress.Dressing(unrealsdk.unreal.WeakPointer(actor), look, self.clock,
                                  _player_own if player else None)
        return self.wardrobe.add(str(actor.Name), name, dressing)

    def _at_menu(self) -> bool:
        """Whether the main menu shows, read each MENU_EVERY_S; each change of the read said."""
        now = self.clock()
        if now < self.menu_next:
            return False
        self.menu_next = now + MENU_EVERY_S
        shown = self.menu()
        if shown != self.menu_shown:
            self.menu_shown = shown
            report.note("main_menu_read", shown=shown)
        return shown is True

    def beat(self, *_args: Any) -> None:
        if self.guard is not None and not self.guard.here():
            return
        if self.end is not None and self.ended is None and self._at_menu():
            # Back at the main menu, the team stops (decision 61): a new game must not find it on.
            self.end("main_menu")
            return
        for one in self.active():
            one.beat()
        self.wardrobe.overdue()
        self.respawns.beat()
        self.follows = self.active()
        if self.bars is not None:
            self.bars.beat(self)

    def stop(self, why: str) -> int:
        """Ends every follow (each companion taken out of the world, leave.py), forgets those on their way, removes
        the hook; says how many were following. Marked ended first, so that no follow ending calls one back; each
        step on its own, and the hook removed whatever failed before it, so that no team keeps running unowned."""
        self.ended = why
        running = self.active()
        failed = waiting = 0
        try:
            for one in running:
                failed += isinstance(follow.tried(lambda one=one: one.finish(why)), str)
            waiting = self.respawns.clear()
            self.follows = []
            if self.bars is not None:
                follow.tried(lambda: self.bars.stop(why))
                self.bars = None
        finally:
            self.wardrobe.stop()
            if self.hook is not None:
                self.hook.disable()
                self.hook = None
        report.note("team_stop", why=why, following=len(running), on_their_way=waiting, failed=failed,
                    off_thread=0 if self.guard is None else self.guard.away)
        return len(running)
