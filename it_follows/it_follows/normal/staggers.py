"""The enemies' staggers and launches made rarer (decision 135, spec-mode-normal.md, section 9): Kevin, 18 October
2026, « Bandit : 15% de sursaut en moins Senior : 25% de sursaut en moins », and Predator 50 % (« on partira plutot sur
une reduction de 50% des sursauts »), or none at all with its « No staggers » row (« juste au cas ou le joueur
voudrait rendre le jeu encore plus compliquer »).

Through the game's one OakHitReactionSettings, HitReactionSettings, common to every enemy: its StaggerChance (0.4)
and LaunchChance (0.2) times the level's staggers. Both at zero, Kevin saw no stagger for 30 s, then three or four
once they were given back (trials 91 and 92, verified in game). That a chance times 0.5 halves the staggers is the
likeliest, not measured: too few come in a few minutes (non vérifié). Blocking them enemy by enemy
(LockHitReactions) was left: its unblock gives nothing back (trial 90, verified in game).

The assets found are held by weak pointers only, read again at each pass: an object the game drops while Python
holds it crashes it. They are searched again only when one of them is gone: a search of every object the game holds
costs 9 to 13 ms (trial 38), and the game loads them once a game (211 logs: 260 writes, each the first of its game;
audit of 24 October 2026, N1). The chances first read in this launch of the game are the game's, kept here for every
play after: a play that never ended cannot make the next take ours for the game's. Each pass of the census writes ours
again where the game reads its own (an asset loaded again); at the end the game's are given back where ours still
lie, an asset changed since left.
"""

from itertools import islice
from typing import Any, Callable

import unrealsdk

ASSET_CLASS = "OakHitReactionSettings"
FIELDS = ("StaggerChance", "LaunchChance")
MOST = 8
SAME = 1e-4
_GAME: dict[str, dict[str, float]] = {}


def _assets() -> list:
    """The loaded settings, the class's default object left out."""
    found = islice(unrealsdk.find_all(ASSET_CLASS, exact=False), MOST)
    return [asset for asset in found if not str(asset.Name).startswith("Default__")]


def _read(asset: Any) -> dict[str, float]:
    return {field: float(getattr(asset, field)) for field in FIELDS}


def _same(one: dict[str, float], other: dict[str, float]) -> bool:
    return all(abs(one[field] - other[field]) <= SAME for field in FIELDS)


class Staggers:
    """factor: the level's staggers, 1 for the game's; announce(call, **fields): written before each write."""

    def __init__(self, factor: float, announce: Callable[..., None]) -> None:
        self.factor = factor
        self.announce = announce
        self.ours: dict[str, dict[str, float]] = {}
        self.found: list[Any] = []

    def keep(self) -> dict:
        """Ours written on each loaded asset that reads the game's: their names, or why none could be."""
        if self.factor == 1.0:
            return {}
        try:
            assets = self._loaded()
        except Exception as error:
            return {"refused": f"unfound:{type(error).__name__}"}
        written = []
        for asset in assets:
            name = str(asset.Name)
            now = _read(asset)
            game = _GAME.setdefault(name, now)
            ours = {field: game[field] * self.factor for field in FIELDS}
            if _same(now, ours):
                self.ours[name] = ours
            if not _same(now, game):
                continue
            self.announce("set_hit_reaction_chances", asset=name, **{f: round(v, 4) for f, v in ours.items()})
            for field in FIELDS:
                setattr(asset, field, ours[field])
            self.ours[name] = ours
            written.append(name)
        return {"staggers": round(self.factor, 3), "written": written} if written else {}

    def _loaded(self) -> list:
        """The assets held, when none is gone; else searched again and held."""
        held = [pointer() for pointer in self.found]
        if held and all(asset is not None for asset in held):
            return held
        assets = _assets()
        self.found = [unrealsdk.unreal.WeakPointer(asset) for asset in assets]
        return assets

    def put_back(self) -> dict | str:
        """The game's chances where ours still lie: by name "given_back", "changed" or "gone"."""
        if not self.ours:
            return "none"
        ours, self.ours = self.ours, {}
        try:
            found = {str(asset.Name): asset for asset in _assets()}
        except Exception as error:
            return f"unfound:{type(error).__name__}"
        given = {}
        for name, wrote in ours.items():
            asset = found.get(name)
            if asset is None:
                given[name] = "gone"
            elif not _same(_read(asset), wrote):
                given[name] = "changed"
            else:
                self.announce("set_hit_reaction_chances", asset=name, **_GAME[name])
                for field in FIELDS:
                    setattr(asset, field, _GAME[name][field])
                given[name] = "given_back"
        return given
