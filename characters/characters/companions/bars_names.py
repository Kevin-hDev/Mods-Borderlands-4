"""The companions' names on the bars, in the language of the game's texts, as the aimed bar shows them (trial 182 of
docs/renforts, vérifié en jeu in French: Châssis vétuste, Crankus, Saumure type M, Abomination).

The language is asked of the game once, when the bars start: GetCurrentCulture (KismetInternationalizationLibrary, no
parameter, "fr" at trial 181), called only once its parameters read from the game are the expected ones, as a game
function is never called with guessed parameters. The names come from assets/companion_names.json, made of the game's
own files of texts by docs/renforts/sondes/companion_bars/build_bar_names.py, its one copy: the language's own, else
the language without its country (fr for fr-FR); the English one for a name it lacks, as the game does, and for all
when the language or the table cannot be read. The six hunters keep their own names, the table having none of them;
the game's other names for them are not read (non vérifié: whether it has any). So do the guests (hunters.GUESTS),
but for a name of ours in that language (hunters.NAMES: « Lilith Phénix » in French), so that the aimed bar, whose
package writes the same, shows the name the cards and the bars show.
"""

import json
import re
from itertools import islice
from pathlib import Path
from typing import Any, Callable

import unrealsdk

from . import hunters, kinds

TABLE = "companion_names.json"
VERSION = 1
LIBRARY, FUNCTION = "KismetInternationalizationLibrary", "GetCurrentCulture"
# Unreal's property flags: a parameter, the return value.
PARAM, RETURN = 0x80, 0x400
EXPECTED = [("ReturnValue", "StrProperty", True)]
MOST_PARAMETERS = 4
# A language as the game's files of texts name their folders (fr, es-419, zh-Hans).
CULTURE = re.compile(r"^[A-Za-z0-9-]{2,16}$")
MOST_BYTES = 65536


def parameters(function: Any) -> list:
    """(name, kind, whether it is the return value) of each parameter, in the engine's order."""
    found = []
    for prop in islice(function._properties(), MOST_PARAMETERS + 1):
        flags = int(prop.PropertyFlags)
        if flags & PARAM:
            found.append((str(prop.Name), str(prop.Class.Name), bool(flags & RETURN)))
    return found


def culture() -> tuple[str | None, str]:
    """The game's text language ("fr", "es-ES") and how it was read, or None and why not."""
    try:
        library = unrealsdk.find_class(LIBRARY)
        if parameters(library._find(FUNCTION)) != EXPECTED:
            return None, "parameters_differ"
        value = library.ClassDefaultObject.GetCurrentCulture()
    except Exception as error:
        return None, f"failed:{type(error).__name__}"
    if not isinstance(value, str) or not CULTURE.match(value):
        return None, "no_culture"
    return value, "read"


def read_asset(name: str) -> str:
    """A file of the mod's assets folder, as text, from the .sdkmod as from a folder."""
    from mods_base import open_in_mod_dir
    with open_in_mod_dir(Path(__file__).parent.parent / "assets" / name, binary=True) as source:
        data = source.read(MOST_BYTES + 1)
    if len(data) > MOST_BYTES:
        raise ValueError("the companions' names table is too large")
    return data.decode("utf-8")


def shown(language: str | None, read: Callable[[str], str] = read_asset) -> tuple[dict, str]:
    """({companion: the name shown}, where the names come from), for every companion of kinds.py."""
    english = {kind.name: kind.name for kind in kinds.ALL}
    if language is None:
        return english, "english:no_culture"
    try:
        table = json.loads(read(TABLE))
        if table["version"] != VERSION:
            return english, "english:table_version"
        names = table["names"]
        base = language.split("-")[0]
        own = names.get(language, names.get(base, {}))
        ours = {name: texts.get(language, texts.get(base)) for name, texts in hunters.NAMES.items()}
        found = {name: own.get(name) or ours.get(name) or name for name in english}
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        return english, "english:table_unread"
    if not all(isinstance(name, str) for name in found.values()):
        return english, "english:table_unread"
    return found, "table"


# Our windows' languages as the game's files of texts name them; English shows the names the team knows them by.
WINDOW_CULTURES = {"EN": None, "FR": "fr", "ZH": "zh-Hans", "JA": "ja"}
_in_window: dict = {}  # window language -> names; one per language of WINDOW_CULTURES at most


def in_window(language: str, read: Callable[[str], str] = read_asset) -> dict:
    """{companion: the name a card shows} in that window language, read once: the allies as the game's texts name
    them, the hunters their own; English for a language the game's texts do not have."""
    if language not in WINDOW_CULTURES:
        return shown(None, read)[0]
    if language not in _in_window:
        _in_window[language] = shown(WINDOW_CULTURES[language], read)[0]
    return _in_window[language]
