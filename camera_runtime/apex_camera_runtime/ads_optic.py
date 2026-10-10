"""Each weapon type's optics while it aims at the shoulder (second list n° 6, Kevin 2026-10-09; every weapon type,
docs/third_person_fov/camera/2026-10-09-plan-optiques-toutes-armes.md).

The player ticks zooms on the AIMING page, one row per weapon type (weapon_optic_options.py); none ticked is "BDL4",
the game's own aim in first person. x1 is a light zoom, the same on every weapon as x2 and up. It was first the
weapon's own zoom (Kevin: « x1 = visée actuelle »), but trial 2 (2026-10-10) measured that zoom from 1.3 to 3.5
times with the weapon's scope: a pistol's x1 showed its x2, an assault rifle's fell between its x3 and x4. A .dll
built before the optics keeps the weapon's own zoom for x1, the aim it can show. The zoom key goes to the next ticked
zoom, smallest to largest and back to the smallest. The next aim with that weapon type starts on its last zoom used, as an Apex optic keeps its zoom (Kevin:
« elle revient sur le dernier zoom donc on mémorise ça »), for the game session only: written to the settings file at
each press, it would bring the player nothing more.
"""

from .generated_ads import (CATEGORY_ASSAULT, CATEGORY_HEAVY, CATEGORY_PISTOL, CATEGORY_SHOTGUN, CATEGORY_SMG,
                            CATEGORY_SNIPER)

# The magnifying zooms, each with its sensitivity row (look_sensitivity_options.py); the sniper rifle's row.
ZOOMS = (2, 3, 4, 6, 8)
X1 = 1
# x1's view factor: the settled aim of an assault rifle without a scope, measured in trial 2 (2026-10-10, 0.750),
# 1.33 times narrower than without aiming (Kevin: « oui on va testé ça »).
X1_SCALE = 0.75
CHOICES = {CATEGORY_PISTOL: (X1, 2, 3), CATEGORY_SMG: (X1, 2, 3, 4), CATEGORY_SHOTGUN: (X1, 2),
           CATEGORY_ASSAULT: (X1, 2, 3, 4), CATEGORY_SNIPER: ZOOMS, CATEGORY_HEAVY: (X1, 2)}
# A mod built before the rows of every weapon type: the aim those types had then.
BEFORE_ROWS = {CATEGORY_PISTOL: (X1,), CATEGORY_SMG: (X1,), CATEGORY_SHOTGUN: (X1,), CATEGORY_ASSAULT: (X1,),
               CATEGORY_HEAVY: ()}


def scale(zoom: int) -> float:
    """The .dll's factor: 1/N makes the view N times narrower than without aiming (trials 3 and 4, 2026-10-09)."""
    return X1_SCALE if zoom == X1 else 1.0 / zoom


class Optics:
    def __init__(self) -> None:
        self.last = None

    def current(self, ticked: tuple) -> int | None:
        """The zoom to aim with, or None for "BDL4"; a zoom no longer ticked gives the smallest."""
        if not ticked:
            return None
        if self.last not in ticked:
            self.last = ticked[0]
        return self.last

    def next(self, ticked: tuple) -> int | None:
        current = self.current(ticked)
        if current is None:
            return None
        self.last = ticked[(ticked.index(current) + 1) % len(ticked)]
        return self.last


def held_zoom(controller) -> int | None:
    """The magnifying zoom of the optic held at the shoulder now, or None: x1 keeps the weapon's own sensitivity
    row."""
    optic = getattr(getattr(controller, "ads", None), "optic", None)
    zoom = optic.zoom if optic is not None else None
    return None if zoom == X1 else zoom


def read_ticked(settings, category) -> tuple:
    """The elected mod's ticked zooms for that weapon type; a value out of the row is "BDL4"."""
    choices = CHOICES.get(category)
    if choices is None:
        return ()
    if category == CATEGORY_SNIPER:
        read = getattr(settings, "sniper_optics", None)
        value = read() if callable(read) else ()
    else:
        read = getattr(settings, "weapon_optics", None)
        value = read(category) if callable(read) else BEFORE_ROWS[category]
    if (type(value) is not tuple or any(type(zoom) is not int or zoom not in choices for zoom in value)
            or list(value) != sorted(set(value))):
        return ()
    return value


class OpticLink:
    """The optic of the published aim, set on the .dll (ads_bridge.set_optic). The .dll forgets it on its own at the
    next publication; generation 0 means no aim of ours is published."""

    def __init__(self) -> None:
        # One memory per weapon type: bounded by CHOICES.
        self.memories: dict = {}
        self.category = None
        self.ticked = ()
        self.generation = 0
        self.released = False
        self.native_optics = False

    def allows(self, settings, native, category) -> bool:
        """Reads the weapon type's ticked zooms: True when it may aim at the shoulder with one. A .dll built before the
        optics keeps x1 only, the aim it can show; one built before heavy weapons at the shoulder keeps them on
        "BDL4"."""
        ticked = read_ticked(settings, category)
        if category == CATEGORY_HEAVY and getattr(native, "heavy", False) is not True:
            ticked = ()
        self.native_optics = getattr(native, "optics", False) is True
        if not self.native_optics:
            ticked = (X1,) if X1 in ticked else ()
        self.category, self.ticked = category, ticked
        return bool(ticked)

    @property
    def active(self) -> bool:
        return bool(self.generation) and not self.released

    @property
    def zoom(self) -> int | None:
        return self._optics().current(self.ticked) if self.active else None

    def _optics(self) -> Optics:
        return self.memories.setdefault(self.category, Optics())

    def publish(self, native, generation: int) -> None:
        self.generation, self.released = generation, False
        zoom = self._optics().current(self.ticked)
        if zoom is not None and self.native_optics:
            native.set_optic(generation, scale(zoom))

    def next(self, native) -> int | None:
        """The zoom key: the next ticked zoom at once, only while the published aim is held with two or more."""
        if not self.active or len(self.ticked) < 2:
            return None
        zoom = self._optics().next(self.ticked)
        native.set_optic(self.generation, scale(zoom))
        return zoom

    def release(self, native) -> None:
        """Let go: the zoom goes at once, then the aim ends as for the other weapons, on a fresh write at 1; without
        the .dll's optics, on the weapon's own curve."""
        if self.active:
            self.released = True
            if self.native_optics:
                native.set_optic(self.generation, 1.0)

    def clear(self) -> None:
        self.generation, self.released = 0, False
