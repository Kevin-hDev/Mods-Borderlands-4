"""The team: up to MOST companions following the hunter together, the hook that drives them, and those on their way.

A team starts with the companions the player chose: each is called (respawn.Respawns.call), then born in front of the
hunter one beat after another once he may have one born (on foot, alive), found by its spawner and followed. A
companion dead comes back the same way, after the wait its mod gives. One hook for the whole team, on the animation
update, as It Follows' heartbeat and the trials since 166: each follow keeps its own pace, rank by rank shifted so
that the samples do not all fall on one frame. The mod's session owns the team: it starts it, stops it, and stops it
with the mod. Those asked of a spawner and not found yet when it stops are looked for a while after, and taken out
of the world (strays.py). A hunter is Lemmy dressed at each birth (dress.py): a Lemmy coming back is born himself.
As he is found, he is handed to the team's wardrobe (wardrobe.py), which dresses him from the camera's update, never
from this beat's (decision 65: dressed from here, the game crashed since its update of 22 October 2026).
Each companion follows with what its mod gives it (tuning.py), asked at each of its births and at its death: the mod
that runs the team owns its levels, its cards or its settings (decision 69), the team none. The bars' service
(bars.py: the bars on the left of the screen, the hunter aimed at) publishes on the same beat and is stopped with the
team. The hooks are named after the mod this copy of the companions ships in, so that two mods carrying it never
take each other's. When several mods carrying it are installed, one leads the team (owners.py): a team starts
only when no other mod leads, stopping first any other mod's team still running (owners.claim), and stops when
another comes to lead.
"""

import time
from typing import Any, Callable

import unrealsdk
from mods_base import get_pc, hook
from unrealsdk.hooks import Type

from .. import camps, game_thread, report
from . import (birth, choose, dress, fight, follow, kinds, main_menu, owners, player_paint, respawn, strays,
               tuning, wardrobe, world)
from .zone import zone_of

HOOK = "/Script/Engine.AnimInstance:BlueprintUpdateAnimation"
# The mod's package, first part of this one's name: it_follows in It Follows.
OWNER = __package__.split(".")[0]
IDENTIFIER = f"{OWNER}:companions"
STRAYS_IDENTIFIER = f"{OWNER}:companions_strays"
MOST = kinds.MOST
# A companion called back after an end that is no death: 3 in a row at most, the count forgotten after a follow of
# 60 s (Claude's choice: a map change ends every follow once; a companion taken away at each birth would loop). The
# count goes with the companion, not its name: a team may hold the same one eight times (review of 23 October 2026).
RECALLS_MOST = 3
RECALL_KEPT_S = 60.0
# How often the team looks whether the main menu shows (main_menu.py), and whether another mod leads it.
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
        # What the mod gives a companion of that name (start), the starting values until the team starts.
        self.tuned: Callable[[str], Any] = lambda _name: tuning.STARTING
        # What stops this team when another mod's starts (owners.claim), kept from its start to its stop.
        self.claimed: Callable[[], None] | None = None
        # The bars on the left of the screen while they are on (bars.Bars), set and taken back by session.py.
        self.bars: Any = None
        self.births = births if births is not None else new_births()
        self.respawns = respawn.Respawns(lambda: respawn.looked(get_pc(), world, world.mode),
                                         self._ask_birth,
                                         self.join, report.note, MOST, clock,
                                         lambda name: self.tuning_of(name).back_after_s)

    def _ask_birth(self, name: str) -> dict:
        """That companion asked of the companions' camps; the spawner it is given watched no more as a stray's:
        what it bears is this team's (strays.py)."""
        answer = self.births.ask(kinds.BY_NAME[name].definition, get_pc())
        if isinstance(answer, dict) and isinstance(answer.get("spawner"), str):
            strays.forget(answer["spawner"])
        return answer

    def active(self) -> list:
        return [one for one in self.follows if not one.done]

    def has(self, name: str) -> bool:
        return any(one.name == name for one in self.active())

    def free_rank(self) -> int:
        """The lowest rank no running follow holds; MOST when the team is full."""
        taken = {one.rank for one in self.active()}
        return next((rank for rank in range(MOST) if rank not in taken), MOST)

    def start(self, names: list[str], tuned: Callable[[str], Any] | None = None) -> str:
        """Each companion named (kinds.py) called, MOST at most, a name it does not know left out, each given what
        tuned(name) gives (tuning.Tuning; the starting values without it), and the hook set: started, or why not."""
        unknown = [name for name in names if name not in kinds.BY_NAME]
        chosen = [name for name in names if name in kinds.BY_NAME][:MOST]
        if not chosen:
            return "empty"
        if owners.elsewhere(OWNER):
            report.note("team_elsewhere", leads=owners.leads(), at="start")
            return "elsewhere"
        self.claimed = self._given_way
        stopped = owners.claim(OWNER, self.claimed)
        if tuned is not None:
            self.tuned = tuned
        for name in chosen:
            self.respawns.call(name, None)
        self.guard = game_thread.Guard("team")
        self.wardrobe.start()
        self.hook = hook(HOOK, Type.POST, hook_identifier=IDENTIFIER)(self.beat)
        self.hook.enable()
        report.note("team_start", companions=chosen, unknown=len(unknown),
                    tuning={name: tuning.written(self.tuning_of(name)) for name in chosen},
                    **({"stopped": stopped} if stopped else {}))
        return "started"

    def _given_way(self) -> None:
        """Another mod's team starting (owners.claim): this one stops at once, through its owner as at a beat."""
        if self.ended is not None:
            return
        report.note("team_elsewhere", leads=owners.leads(), at="claim")
        if self.end is not None:
            self.end("elsewhere")
        if self.ended is None:
            self.stop("elsewhere")

    def tuning_of(self, name: str) -> tuning.Tuning:
        """What the mod gives that companion now, checked; the starting values, said, when its reading failed."""
        try:
            return tuning.checked(self.tuned(name))
        except Exception as error:
            report.note("companion_tuning_failed", companion=name, error=f"{type(error).__name__}")
            return tuning.STARTING

    def join(self, name: str, spawner: str, times: float | None, recalls: int = 0) -> dict:
        """The companion of that name that spawner bore, dressed if a hunter, followed, called back recalls times in
        a row before (_ended): started, or why not (not_found while it is not there yet)."""
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
        tuned = self.tuning_of(name)
        dressed = {} if kind.look is None else {"dressed": self._dress(actor, kind.look, name, tuned.outfit)}
        one = follow.Follow(actor, zone, self.clock, rank, kind.definition, times, offset(rank, follow.EVERY_S),
                            tuned)
        one.on_death = lambda _definition, health: self.respawns.died(name, health)
        one.on_end = lambda why, ended=one: self._ended(name, ended, why)
        one.companion = name
        one.recalls = recalls
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
        count = 0 if self.clock() - ended.started >= RECALL_KEPT_S else getattr(ended, "recalls", 0)
        if count >= RECALLS_MOST:
            report.note("companion_not_recalled", companion=name, why=why, recalls=count)
            return
        report.note("companion_recalled", companion=name, why=why, recalls=count + 1)
        self.respawns.call(name, ended.times, count + 1)

    def _dress(self, actor: Any, look: str, name: str, outfit: str) -> str:
        """A hunter handed to the wardrobe, with the player's colours when his mod asks for them."""
        dressing = dress.Dressing(unrealsdk.unreal.WeakPointer(actor), look, self.clock,
                                  _player_own if outfit == "player" else None)
        return self.wardrobe.add(str(actor.Name), name, dressing)

    def _ending(self) -> str | None:
        """Why the team must stop now, read each MENU_EVERY_S, or None: another mod leading it (owners.py), or
        the main menu showing; each change of the menu's read said."""
        now = self.clock()
        if now < self.menu_next:
            return None
        self.menu_next = now + MENU_EVERY_S
        if owners.elsewhere(OWNER):
            report.note("team_elsewhere", leads=owners.leads(), at="beat")
            return "elsewhere"
        shown = self.menu()
        if shown != self.menu_shown:
            self.menu_shown = shown
            report.note("main_menu_read", shown=shown, **({"why": main_menu.why()} if shown is None else {}))
        return "main_menu" if shown is True else None

    def beat(self, *_args: Any) -> None:
        if self.guard is not None and not self.guard.here():
            return
        why = None if self.end is None or self.ended is not None else self._ending()
        if why is not None:
            # Back at the main menu, the team stops (decision 61): a new game must not find it on. Another mod
            # leading, it stops too: two teams would follow the hunter.
            self.end(why)
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
        asked: list = []
        try:
            for one in running:
                failed += isinstance(follow.tried(lambda one=one: one.finish(why)), str)
            asked = self.respawns.asked()
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
            if self.claimed is not None:
                owners.release(OWNER, self.claimed)
        report.note("team_stop", why=why, following=len(running), on_their_way=waiting, failed=failed,
                    off_thread=0 if self.guard is None else self.guard.away)
        if asked and why != "main_menu":
            failed_watch = follow.tried(lambda: strays.watch(asked, self.clock, HOOK, STRAYS_IDENTIFIER))
            if isinstance(failed_watch, str):
                report.note("strays_failed", why=failed_watch, companions=[one[0] for one in asked])
        return len(running)
