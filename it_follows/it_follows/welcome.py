"""Whether the welcome opens (decision 61: at the first opening of the window, « à détecter »): the edition of it the
player last saw, kept in the settings file, as BL4 Arena keeps its own."""

from mods_base import SliderOption

# Raised by a later version that has news to tell: the welcome then opens once more. 2: the normal mode's page
# (decision 80), which a player who saw the first edition has not read. 3: that page saying the mode is made first for
# a game from the start, like NG+ (decision 101).
EDITION = 3
seen = SliderOption("welcome_seen", 0, 0, 100, step=1, is_integer=True, is_hidden=True)


def due() -> bool:
    """Whether the welcome opens: an edition the player has not seen yet, or a value that is not one."""
    value = seen.value
    return type(value) not in (int, float) or value < EDITION
