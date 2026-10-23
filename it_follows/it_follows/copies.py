"""It Follows' camps put to work in a run: the camp whose zone is lent to the horde, the copies of the enemies near at
the start (decision 38), and the killed coming back (wave.py), each born of a camp It Follows makes (camps.py).

Why the zone lent is that of a camp It Follows makes (docs/RUN/enquetes/2026-10-12-arret-au-loin.md, trials 6x and
6y): the game's camps live in pieces of the map it loads and unloads, and every horde lent the zone of such a camp was
lost at once, 400 m to 1.2 km from the start, whatever the camp's settings or how far the map was loaded. The two
hordes lent the zone of a camp made during the game, in the level always loaded, followed to the end (trials 6s and
6t). So the zone lent is that of a camp made the same way, holding no enemy; and each enemy within NEAR_M of the hunter
gets a copy, born of such a camp, which the census then draws like any other enemy. The killed come back the same way,
free camps first.

The copies are born on a ring of RING_M around a point BEHIND_M behind the hunter, opposite to where he looks: none
appears under his eyes (decision 23; trial 8b, 245 born so, none seen appearing by Kevin). Each one's ring is moved
along his back by the next offset of the level's spread (decision 66, spread.py), so that they are not all born in one
group: from 25 to 65 m behind him with Kevin's example. Each is laid on the ground found under its point of the ring, a
point over water left out (decision 28), and one whose trace met a character or a projectile (decision 72): with no
ground on the ring, nobody is asked, and the killed wait for the next second. The game's limit of enemies is lifted at
the first ask and given back at the stop (budget.py).
"""

from itertools import islice
import math
import time
from typing import Any, Callable

import unrealsdk

from .characters import reads
from .seen import Seen

# Kevin, decision 38: « dupliquer les premiers ennemis des premiers camps à proximité ». Trial 6y: 20 enemies stood
# within 133 m of the hunter, the next ones 400 m away.
NEAR_M = 150.0
# The ring's centre: with RING_M, 30 to 50 m behind the hunter, more than 90 degrees from his look (catch_up.py's
# HIDDEN_DEG), no nearer than the 30 m the trials brought enemies back to (decision 26).
BEHIND_M = 40.0
# BL4 Arena's ring in trials 6z to 8b; 50 enemies born on it within 4 s in the domed arena's lots trial 3.
RING_M = 10.0
# Each ask's ring turned from the last by the golden angle, so that the asks at one place do not reuse its spots.
TURN_RAD = math.pi * (3.0 - math.sqrt(5.0))
# Ground from 3 m above the hunter's height down to 20 m below, a ledge's foot, as BL4 Arena's ring found it in trials
# 6z to 8b. The ocean's own collision is met first and refused as water (trial 6m: 337 times).
UP_CM = 300.0
DOWN_CM = 2000.0
# The camp's zone is found among all the game's zones, a few hundred around the hunter; the game waits while they are
# read.
MAX_ZONES = 5000
READ_S = 0.25
ZONE_CLASS = "GbxTerritoryComponent"


def behind(here: tuple, yaw: float) -> tuple:
    """BEHIND_M behind here, opposite to a look of yaw degrees, at the same height."""
    angle, reach = math.radians(yaw + 180.0), BEHIND_M * 100.0
    return here[0] + reach * math.cos(angle), here[1] + reach * math.sin(angle), here[2]


def facing(point: tuple, here: tuple) -> float:
    """The yaw, in degrees, from point towards here."""
    return math.degrees(math.atan2(here[1] - point[1], here[0] - point[0]))


class Copies:
    """The camps one run puts to work: the lent zone's, the copies' and those of the killed born again. announce(call,
    log, **fields) notes a call before it is made; camps is a camps.Camps; ground answers ground(name, mover, point,
    up_cm, down_cm) with (what was found, where the camp goes, what was met), as ground.py does; budget is a
    budget.Budget; spread a spread.Spread."""

    def __init__(self, announce: Callable[..., None], camps: Any, ground: Any, budget: Any, spread: Any) -> None:
        self.announce, self.camps, self.ground, self.budget, self.spread = announce, camps, ground, budget, spread
        # How many rings were laid.
        self.rings = 0
        # The camps whose birth has not joined the horde yet, with its kind; and the kinds of births found lost, their
        # camp free again before they joined, until unseen gives them. At most a kind a camp.
        self.owed: dict[str, str] = {}
        self.lost: list[str] = []
        # The camps whose enemy the horde holds alive, given by the run once its horde is made (camps.survey).
        self.held: Callable[[], frozenset[str | None]] = frozenset

    def ask(self, crowd: list, character: Any, pc: Any, here: tuple, most: int) -> tuple[Seen | None, dict]:
        """The zone to lend, as a Seen, and what was made; no zone when the camp could not be made or has none, said,
        and then no copy is asked. crowd: the enemies around, as the census's Seen; most: the copies the horde has room
        for (decision 96), beyond which a copy would be born only to stay out of it."""
        began = time.monotonic()
        kit = self.camps.kit()
        if isinstance(kit, str):
            return None, {"made": f"no_kit:{kit}"}
        try:
            yaw = float(pc.GetControlRotation().Yaw)
        except Exception as error:
            return None, {"made": f"no_look:{type(error).__name__}"}
        middle = behind(here, yaw)
        near = [seen for seen in crowd if seen.definition and (reads.metres(seen.at, here) or math.inf) <= NEAR_M]
        self.announce("run_camps", near=len(near), at=reads.spot(middle))
        camp = self.camps.made(kit, middle, facing(middle, here), character)
        if camp is None:
            return None, {"made": "camp_refused"}
        name = reads.clean(camp.Name)
        self.camps.mine.add(name)
        host, why = self._host(camp)
        if host is None:
            return None, {"made": why, "camp": name}
        wanted = [(seen.name, seen.definition) for seen in near if self.camps.knows(seen.definition)][:max(0, most)]
        born = self._born(kit, wanted, character, here, middle)
        return host, {"made": "done", "camp": name, "zone": host.zone_path, "near": len(near),
                      "unknown": len(near) - len(wanted), **born, "at": reads.spot(middle),
                      "took_ms": round((time.monotonic() - began) * 1000.0, 1)}

    def again(self, wanted: list, character: Any, pc: Any, here: tuple) -> dict:
        """The killed of wanted, (name, kind) oldest first, born again as the copies were. handed: how many of wanted's
        first were handed a camp."""
        began = time.monotonic()
        kit = self.camps.kit()
        if isinstance(kit, str):
            return {"again": f"no_kit:{kit}", "handed": 0}
        try:
            yaw = float(pc.GetControlRotation().Yaw)
        except Exception as error:
            return {"again": f"no_look:{type(error).__name__}", "handed": 0}
        middle = behind(here, yaw)
        self.announce("run_camps", again=len(wanted), at=reads.spot(middle))
        return {"again": "done", **self._born(kit, wanted, character, here, middle), "at": reads.spot(middle),
                "took_ms": round((time.monotonic() - began) * 1000.0, 1)}

    def _born(self, kit: Any, wanted: list, character: Any, here: tuple, middle: tuple) -> dict:
        """wanted's first, each handed a camp on the ground behind the hunter, free camps first, as many as the camps'
        room and the ring's ground allow; stops at the first one refused, the refusal said (wave.py writes who). alive:
        the copies alive, their camps holding an enemy or handed one lately, wherever they are."""
        survey = self.camps.survey(held=self.held())
        self._settle(survey)
        alive = survey.busy + survey.pending
        room = self.camps.room(survey)
        spots, left_out = self._spots(min(room, len(wanted)), character, here, middle)
        asked = wanted[:len(spots)]
        said = {"free": len(survey.free), "taken_back": survey.stuck, "alive": alive, "room": room,
                "spots": len(spots), "asked": len(asked), "handed": 0}
        if left_out:
            said["left_out"] = left_out
        if asked:
            self.budget.lift()
        for (_name, kind), spot in zip(asked, spots):
            try:
                placed = self.camps.place(kit, survey.free, spot, facing(spot, here), character)
                refused = "camp_refused" if placed is None else self.camps.hand(kit, *placed, kind)
            except Exception as error:
                refused = f"error:{type(error).__name__}"
            if refused is not None:
                said["refusal"] = refused
                break
            said["handed"] += 1
            name = reads.clean(placed[1].Name)
            self.camps.mine.add(name)
            self.owed[name] = kind
        return said

    def _settle(self, survey: Any) -> None:
        for _camp, spawner in survey.free:
            kind = self.owed.pop(reads.clean(spawner.Name), None)
            if kind is not None:
                self.lost.append(kind)

    def owes(self, camp: str | None) -> bool:
        """Whether that camp's birth has not joined the horde yet."""
        return camp in self.owed

    def owing(self) -> int:
        """How many births have not joined the horde yet."""
        return len(self.owed)

    def joined(self, camp: str | None) -> None:
        """The birth of that camp joined the horde: it is owed no more."""
        self.owed.pop(camp, None)

    def unseen(self) -> list[str]:
        """The kinds of the births whose camp was found free again before they joined the horde, each given once:
        killed before a census drew them, or never born (trial 18: 15 % of a run's births, and its horde ran dry)."""
        if self.owed:
            self._settle(self.camps.survey(log=False, held=self.held()))
        found, self.lost = self.lost, []
        return found

    def _spots(self, count: int, character: Any, here: tuple, middle: tuple) -> tuple[list[tuple], dict[str, int]]:
        """Up to count points of a ring of RING_M around middle, each ring moved away from here by the spread's next
        offset, each point laid on the ground under it; none over water or with no ground (decision 28), nor on a
        character or a projectile (decision 72); with how many were left out, by why."""
        left_out: dict[str, int] = {}
        if count < 1:
            return [], left_out
        first, self.rings = self.rings * TURN_RAD, self.rings + 1
        reach = math.dist(here[:2], middle[:2]) or 1.0
        away = ((middle[0] - here[0]) / reach, (middle[1] - here[1]) / reach)
        laid = []
        for index in range(count):
            angle, offset = first + 2.0 * math.pi * index / count, self.spread.next() * 100.0
            point = (middle[0] + away[0] * offset + math.cos(angle) * RING_M * 100.0,
                     middle[1] + away[1] * offset + math.sin(angle) * RING_M * 100.0, middle[2])
            said, where, _met = self.ground.ground("camp", character, point, UP_CM, DOWN_CM)
            if where is not None:
                laid.append(where)
            else:
                left_out[said] = left_out.get(said, 0) + 1
        return laid, left_out

    def _host(self, camp: Any) -> tuple[Seen | None, str]:
        """The camp's zone as a Seen holding it, or why there is none."""
        zone = self._zone(camp)
        if zone is None:
            return None, "no_camp_zone"
        try:
            radius_m = reads.zone_radius_cm(zone) / 100.0
        except ValueError:
            return None, "camp_zone_radius_unreadable"
        return Seen(actor=None, name="own_camp", definition="", zone=zone, zone_path=reads.path_of(zone),
                    centre=reads.point(zone, "K2_GetComponentLocation"), radius_m=radius_m, at=None,
                    walks=False), "done"

    def _zone(self, camp: Any) -> Any:
        """The game's zone owned by the camp, read among them all within MAX_ZONES and READ_S; None if not found."""
        began = time.monotonic()
        for zone in islice(unrealsdk.find_all(ZONE_CLASS, exact=False), MAX_ZONES):
            if time.monotonic() - began > READ_S:
                return None
            if zone.Outer == camp:
                return zone
        return None

    def knows(self, kind: str) -> bool:
        """Whether It Follows' camps can make that kind: in the game's list, read when the first camp was made."""
        return self.camps.knows(kind)

    def ours(self, camp: str | None) -> bool:
        """Whether the camp is one It Follows made, so its enemy a copy."""
        return camp in self.camps.mine

    def status(self) -> dict:
        """It Follows' camps holding their enemy alive, and what the game's limit came to."""
        return {**self.camps.status(), "budget": self.budget.said}

    def put_back(self) -> str:
        """The game's limit of enemies given back where It Follows lifted it."""
        return self.budget.restore()
