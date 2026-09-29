"""What the chosen heirloom wears on the component in the hand: its model, and the slots of its chosen skin, its glow at
the chosen force, as the mod's catalog sets them (heirloom_catalog.py, generated from the heirlooms' definitions).

Why, 2026-09-29 (cosmetics/heirloom/docs/heirloom.md, section 19): Kevin chose that the menu offers the knife and the
axe, each with its skins and its glow. The axe's look was a trial command's (sondes/apex_painted_trial.py, gone
since), tried and validated in game: on the knife's own component, only the model, its materials and its hold
changed. The mod now does the same itself. The engine refuses a model the component already holds (SetStaticMesh
gives false): it is set only when it changes. Each call to the engine is said before it is made.
"""

from typing import Any, Callable

from . import apex_own_look as own_look
from .heirloom_catalog import HEIRLOOMS

Say = Callable[[str], None]
Load = Callable[[str, str], Any]
MODEL_CLASS = "StaticMesh"


def skin_of(heirloom: str, skin: str) -> dict[str, Any]:
    """The heirloom's skin of that name, or its own look when it has none of that name."""
    skins = HEIRLOOMS[heirloom]["skins"]
    return next((known for known in skins if known["name"] == skin), skins[0])


def slots(heirloom: str, skin: str, force: int) -> dict[str, dict]:
    """The skin's slots, its glow's strength at `force` (1 to 5) set on its glow slot when it glows."""
    chosen = skin_of(heirloom, skin)
    made = {slot: dict(recipe) for slot, recipe in chosen["slots"].items()}
    glow = chosen["glow"]
    if glow is not None:
        strength = glow["strengths"][force - 1]
        recipe = made[glow["slot"]]
        recipe["scalars"] = [*recipe.get("scalars", []), *({**value, "value": strength} for value in glow["scalars"])]
    return made


def model(heirloom: str, load: Load, say: Say) -> Any:
    """The heirloom's model, or None, said, when the game has not loaded its container."""
    known = HEIRLOOMS[heirloom]
    found = load(MODEL_CLASS, known["model"])
    if found is None:
        say(f"our {heirloom} model was not found: is {known['container']} installed?")
    return found


def dress(component: Any, heirloom: str, skin: str, force: int, load: Load, say: Say) -> int:
    """The heirloom's skin put on the component, its glow at `force`; how many slots were dressed."""
    chosen = slots(heirloom, skin, force)
    dressed = own_look.dress(component, chosen, load, say)
    say(f"our {heirloom} wears its {skin_of(heirloom, skin)['name']} skin: {dressed} of {len(chosen)} slots dressed")
    return dressed


def wear(component: Any, heirloom: str, skin: str, force: int, load: Load, say: Say) -> bool:
    """The heirloom's model put on the component, then its skin; False, said, when its model is not in the game or
    the component refuses it: the component keeps what it had."""
    found = model(heirloom, load, say)
    if found is None:
        return False
    # Compared by path: the engine may hand the same object back through another wrapper.
    shown = component.StaticMesh
    if shown is None or shown._path_name() != found._path_name():
        say(f"SetStaticMesh {found._path_name()}")
        if not component.SetStaticMesh(found):
            say(f"the component refused our {heirloom} model: it keeps the one it had")
            return False
    dress(component, heirloom, skin, force, load, say)
    return True
