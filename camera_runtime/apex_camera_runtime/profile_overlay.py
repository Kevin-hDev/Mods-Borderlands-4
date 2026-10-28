"""The elected mod's camera settings with the shown profile over them (decisions of 2026-10-12): the profile window's
draft while it is open, else the profile switched on, else nothing.

Five readings change and every other passes through. The camera asks them each frame (fov.py, camera_offset.py,
framing_session.py), so a change shows at the next one. A reading the mod does not have stays missing: a mod older
than a setting keeps going without it, as before.
"""

from functools import partial

from .framing_catalog import GROUPS


def _fov_enabled(profiles, read):
    # A profile's FOV always applies: one that changed nothing while the mod's own FOV is off would be broken.
    return profiles.shown() is not None or read()


def _fov_value(profiles, read):
    shown = profiles.shown()
    return read() if shown is None else float(shown.fov)


def _distances(profiles, read):
    """Close, normal and far in centimetres; the normal distance stays the game's."""
    shown = profiles.shown()
    if shown is None:
        return read()
    _close, normal, _far = read()
    return round(shown.close * 100, 2), normal, round(shown.far * 100, 2)


def _distance(profiles, read):
    return profiles.distance(read())


def _framing(profiles, read):
    """The aim zoom stays the player's; spacing and height are the profile's, custom unless a preset's."""
    rows = read()
    shown = profiles.shown()
    if shown is None:
        return rows
    placed = {"horizontal": shown.spacing, "height": shown.height}
    return tuple(row if group.key not in placed
                 else (placed[group.key], all(placed[group.key] != at for _name, at in group.presets))
                 for group, row in zip(GROUPS, rows))


OVER = {"fov_enabled": _fov_enabled, "fov_value": _fov_value, "camera_distances": _distances,
        "camera_distance": _distance, "framing_values": _framing}


class ProfiledSettings:
    def __init__(self, base, profiles) -> None:
        self.base, self.profiles = base, profiles

    def __getattr__(self, name):
        found = getattr(self.base, name)
        over = OVER.get(name)
        reading = found if over is None else partial(over, self.profiles, found)
        # Kept for the next frames: the readings are the mod's own functions, which never change, and a profile is
        # asked at each call, not here. About twenty readings a frame went through this lookup (2026-10-24).
        self.__dict__[name] = reading
        return reading
