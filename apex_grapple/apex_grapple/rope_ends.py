"""The rope's two ends: under what name, and through which function, the effect takes a position.

Split out of `beam.py` on 2026-09-21, which by then held two jobs: putting the rope in the game, and
finding out how to tell it where to go. This file is the second.

Two lessons are written in here rather than left to be learnt again:

- the names are read from the effect, never guessed. Eight guessed names all failed, while the real
  ones carry a `User.` prefix and real spaces;
- a refusal is kept and written down. The first version tried each name and swallowed the error to
  try the next, so a silent failure said nothing at all about why — and one kept refusal hid three
  others, which cost a session on its own.

*Verified in game on 2026-09-21*: the effect takes `User.Target` and `User.Source` through its own
`SetVariablePosition`. `NiagaraFunctionLibrary` has no `SetNiagaraVariablePosition` at all on this
build, so asking the library was asking the wrong thing.
"""

import re
from typing import Any

import unrealsdk

from . import report

# What each end of the rope reads like, likeliest first.
SOURCE_WORDS = ("source", "start", "muzzle", "hand")
TARGET_WORDS = ("target", "beam end", "end point", "endpoint", "destination", "hook", "end")
# Who is asked to write a position, in order. The effect itself comes first. A world position has
# its own type in Unreal 5, hence a position writer before a vector one.
WRITERS = ("component.SetVariablePosition", "component.SetVariableVec3",
           "library.SetNiagaraVariablePosition", "library.SetNiagaraVariableVec3")
# Function names worth writing down when nothing works: it is the list that ends the guessing.
WRITER_WORDS = ("variable", "parameter")
MAX_WRITERS_LISTED = 40
# Niagara puts a `User.` in front of a user parameter by itself, so a name read from the effect is
# tried both as it is printed and without that prefix.
USER_PREFIX = "User."
# The names inside what the effect prints of itself, as `Name: 'User.Color Scale'`.
NAME_IN_PRINT = re.compile(r"Name: '([^']+)'")
MAX_NAMES = 60
# Bounded: the store prints long, and the log has to stay readable. It holds the values too, which
# is how the eleven parameters were read side by side with the game's own on 2026-09-21.
MAX_STORE = 4000

# The effect's own parameter names, read from it at the first spawn.
_names: list[str] = []
_listed = False
# The function that answered, found once and kept.
_setter: str | None = None
# Why each way of writing was refused, so a silent refusal is never investigated by guesswork again.
_refusals: dict[str, str] = {}


def reset() -> None:
    global _setter, _listed
    _setter = None
    _listed = False
    _names.clear()
    _refusals.clear()


def read_names(system: Any) -> None:
    """Reads the effect's own parameter names once: they are what names the two ends for good."""
    global _listed
    if _listed:
        return
    _listed = True
    try:
        printed = str(system.ExposedParameters)
    except Exception:
        report.note("the grapple beam does not hand over its parameter list")
        return
    # The whole printed store, not only the names pulled out of it: it carries the values, and it is
    # how the effect's eleven parameters were read beside the game's own and found identical.
    report.note(f"grapple beam defaults: {printed[:MAX_STORE]}")
    names = parameter_names(printed)
    if names:
        _names[:] = names
        report.note(f"grapple beam parameters: {', '.join(names)}")
    else:
        report.note("the grapple beam hands over a parameter list with no names in it")


def parameter_names(printed: str) -> list[str]:
    """The parameter names out of what the effect prints of itself, in the order it gives them."""
    return list(dict.fromkeys(NAME_IN_PRINT.findall(printed)))[:MAX_NAMES]


def find(component: Any, library: Any, words: tuple[str, ...],
         spot: tuple[float, float, float], what: str) -> str | None:
    """Tries every way of writing against every likely name, and keeps the pair that worked."""
    global _setter
    writers = (_setter,) if _setter is not None else WRITERS
    for writer in writers:
        for name in candidates(_names, words):
            try:
                put(component, library, writer, name, spot)
            except Exception as exc:
                # One refusal per way of writing, not one per name: it is the way that fails, and a
                # single kept refusal hid three others on 2026-09-21.
                _refusals.setdefault(writer, repr(exc))
                if isinstance(exc, AttributeError):
                    # The way of writing does not exist at all: no name will make it work.
                    break
            else:
                _setter = writer
                report.note(f"the grapple beam takes its {what} as {name!r}, written with {writer}")
                return name
    return None


def write(component: Any, library: Any, name: str, spot: tuple[float, float, float]) -> None:
    """Writes one end, through the way of writing already known to answer. Raises on refusal."""
    put(component, library, _setter, name, spot)


def put(component: Any, library: Any, writer: str, name: str,
        spot: tuple[float, float, float]) -> None:
    where, function = writer.split(".", 1)
    holder = component if where == "component" else library
    arguments = (name, vector(spot)) if where == "component" else (component, name, vector(spot))
    getattr(holder, function)(*arguments)


def candidates(names: list[str], words: tuple[str, ...]) -> tuple[str, ...]:
    """What to try for one end of the rope, the likeliest name first, in both spellings."""
    ranked: list[str] = []
    for word in words:
        for name in names:
            if word in name.lower() and name not in ranked:
                ranked.append(name)
    tried: list[str] = []
    for name in ranked:
        bare = name[len(USER_PREFIX):] if name.startswith(USER_PREFIX) else USER_PREFIX + name
        for spelling in (name, bare):
            if spelling not in tried:
                tried.append(spelling)
    return tuple(tried)


def refusals() -> str:
    return "; ".join(f"{writer}: {why}" for writer, why in _refusals.items())


def tell_writers(component: Any, library: Any) -> None:
    """Writes down what the effect and the library really offer, so the next try is not a guess."""
    for what, holder in (("the effect", component), ("the library", library)):
        try:
            names = [name for name in dir(holder)
                     if any(word in name.lower() for word in WRITER_WORDS)][:MAX_WRITERS_LISTED]
        except Exception:
            continue
        report.note(f"what {what} offers: {', '.join(names) if names else 'nothing with that in its name'}")


def vector(spot: tuple[float, float, float]) -> Any:
    return unrealsdk.make_struct("Vector", X=spot[0], Y=spot[1], Z=spot[2])
