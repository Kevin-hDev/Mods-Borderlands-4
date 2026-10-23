"""The zone lent to the horde: posed on the hunter and following him, lent to each enemy drawn, its combat radius
widened; put back where it stood, each enemy given its own back and its radius written back when the run stops.

Trial 3a: a lent zone on the hunter keeps a walked enemy on him (docs/RUN/enquetes/2026-10-10-zone-sur-le-chasseur.md);
trial 3c: it follows him while he runs; trial 6a: one zone lent to several enemies at once; trial 6p: its combat radius
widened (zone_radius.py, decision 33). A zone the game moves away is put back onto the hunter (replace) and the tries
that fail in a row are counted: the trials stopped at the first one, a mode of play tries again. Taken from the trials'
docs/RUN/sondes/run_hunter_zone.py.
"""

from typing import Any, Callable

from .characters import reads
from .seen import Seen
from .zone_loan import Loan
from .characters.zone_radius import TerritoryRadiusPatch
from .zone_shift import Shift

# docs/RUN/spec-run.md, section 3: the zone set off after the hunter every 2 seconds.
FOLLOW_S = 2.0
# Closer than this to the hunter the zone stays put: a call a second while he stands still would change nothing.
FOLLOW_M = 5.0
# Trial 6g: a zone read on the hunter right after each move was back 420 m away a second later, every time; read
# farther than this from where it was put, the game has moved it.
HELD_M = 5.0
# The zone cannot be kept on the hunter once this many tries in a row leave it elsewhere, or once the game has moved
# it away this many samples in a row though each try puts it back (lost).
TRIES = 3
AWAY_SAMPLES = 10


class HunterZone:
    """The zone of one group, on the hunter, and the enemies it is lent to, by name; announce(call, log=True, **fields)
    notes a call before it happens."""

    def __init__(self, host: Seen, announce: Callable[..., None]) -> None:
        """host holds the zone."""
        self.host_path, self.announce = host.zone_path, announce
        self.shift = Shift(host.zone)
        self.loans: dict[str, Loan] = {}
        self.followed_at: float | None = None
        self.put_at: tuple | None = None
        self.radius: TerritoryRadiusPatch | None = None
        # Tries in a row that did not put a zone the game moved away back onto the hunter, and samples in a row that
        # found it moved away (lost).
        self.failures = 0
        self.away = 0

    def centre(self) -> tuple | None:
        return self.shift.where()

    def stays(self) -> bool | None:
        """Whether the zone still stands where it was last put; None before it is put or when it cannot be read."""
        centre = self.centre()
        if self.put_at is None or centre is None:
            return None
        return reads.metres(centre, self.put_at) <= HELD_M

    def place(self, here: tuple | None, now: float) -> str:
        """Moves the zone onto the hunter; says whether it stands there: moved, not_moved or unavailable. A failing call
        raises, the zone counted as moved so that it is put back."""
        return self._put(here, now, "onto_hunter")

    def replace(self, here: tuple | None, now: float) -> str:
        """Puts the zone back onto the hunter as place does once the game has moved it away (stays() is False); kept
        otherwise, nothing called. A try that does not leave it moved counts in failures, a failing call too (it
        raises); a move counts them from 0 again."""
        if self.stays() is not False:
            return "kept"
        try:
            placed = self._put(here, now, "back_on_hunter")
        except Exception:
            self.failures += 1
            raise
        self.failures = 0 if placed == "moved" else self.failures + 1
        return placed

    def lost(self, here: tuple | None, now: float, note: Callable[..., None]) -> str | None:
        """Once a sample: the zone put back on the hunter once the game moved it away; why the run must stop, or None.
        It stops when the zone is gone, when TRIES tries in a row leave it elsewhere, and when the game moves it away
        AWAY_SAMPLES samples in a row though each try puts it back: trial 6g read a zone on the hunter right after each
        move and 420 m away a second later, every time. Only the first try of a series is written down (note)."""
        if self.shift.zone() is None:
            return "zone_gone"
        if self.stays() is not False:
            self.away = 0
            return None
        self.away += 1
        try:
            outcome = self.replace(here, now)
        except Exception as error:
            outcome = f"call_failed:{type(error).__name__}"
        if self.away == 1:
            note("zone_replaced", outcome=outcome, failures=self.failures)
        if self.failures >= TRIES or self.away >= AWAY_SAMPLES:
            return "zone_lost"
        return None

    def _put(self, here: tuple | None, now: float, why: str) -> str:
        placed = self.shift.place(here, lambda: self.announce("K2_SetWorldLocation", zone=why))
        self.followed_at, self.put_at = now, here
        return placed

    def lend(self, mover: Seen) -> str:
        """Lends the zone to an enemy, the call announced first; says which zone it holds then. A failing call raises,
        the loan kept so that it is given back."""
        loan = Loan(mover, self.shift.zone, self.host_path)
        self.loans[mover.name] = loan
        return loan.lend(mover.actor, lambda: self.announce("SetTerritory", zone="target", on=mover.name))

    def held(self, name: str, zone: Any) -> str:
        """Which zone the enemy lent under that name holds: none, target, own or other; not_lent if it is not."""
        loan = self.loans.get(name)
        return loan.held(zone) if loan is not None else "not_lent"

    def follow(self, here: tuple | None, now: float, again: bool = False) -> str:
        """Moves the zone back onto the hunter once he has walked away from it, at most every FOLLOW_S; with again, at
        once: a camp's spawner just moved may have carried its zone along (camp_follow.py)."""
        if not again and (self.followed_at is None or now - self.followed_at < FOLLOW_S):
            return "waiting"
        away = reads.metres(self.centre(), here)
        if not again and (away is None or away <= FOLLOW_M):
            return "kept"
        self.followed_at, self.put_at = now, here
        return self.shift.place(here, lambda: self.announce("K2_SetWorldLocation", log=False, zone="follow"))

    def give_back(self, name: str, actor: Any, body_reused: bool) -> str:
        """Gives one enemy its own zone back, once, unless the game reuses its body; not_lent if it never was lent."""
        loan = self.loans.pop(name, None)
        if loan is None:
            return "not_lent"
        return loan.give_back(actor, body_reused, lambda: self.announce("SetTerritory", zone="own", on=name))

    def put_back(self) -> str:
        """Stops following the hunter and puts the zone back where it stood, whatever happened to the enemies."""
        self.followed_at = self.put_at = None
        return self.shift.put_back(lambda: self.announce("K2_SetWorldLocation", zone="back"))

    def widen(self, radius_cm: float) -> dict:
        """Gives the zone a combat radius of radius_cm, the write announced first; says the radius it had. A write the
        game does not keep raises, the zone's own radius written back first."""
        zone = self.shift.zone()
        if zone is None:
            return {"widened": "unavailable"}
        self.radius = TerritoryRadiusPatch(radius_cm)
        self.announce("CombatTerritory.Radius", zone="widen", radius_m=round(radius_cm / 100.0, 2))
        before = self.radius.apply(zone)
        return {"widened": "done", "radius_m_before": round(before / 100.0, 2), "radius_m": self.radius_m()}

    def radius_m(self) -> float | None:
        """The zone's combat radius read now, in metres; None when it cannot be read."""
        try:
            return round(reads.zone_radius_cm(self.shift.zone()) / 100.0, 2)
        except ValueError:
            return None

    def narrow(self) -> str:
        """Writes the zone's own combat radius back, once, if the one the run wrote is still there: a radius the game
        changed meanwhile is left as the game set it."""
        patch, self.radius = self.radius, None
        if patch is None:
            return "not_widened"
        self.announce("CombatTerritory.Radius", zone="narrow")
        return patch.restore(self.shift.zone())
