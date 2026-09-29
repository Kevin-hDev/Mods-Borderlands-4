"""Dresses our knife in its own look, made from the game's files: each slot of our model gets its own copy of the
game's material that the look names, with the values the look sets on it.

Why, 2026-09-26 (cosmetics/heirloom/docs/enquetes/2026-09-26-essai-du-mod.md): our knife borrowed the materials of
whatever Jakobs grenade the game had built, equipped or thrown on the ground, and showed the engine's grid without
one. Kevin chose to keep his grenade's look for good. Read on his grenade (sondes/apex_knife_look.py), each slot is a
copy of a material from the game's files with a few values set, the Jakobs knife's textures among them: the same copy
made here needs no grenade. The look comes from the heirloom's heirloom.json, through the mod's catalog
(heirloom_catalog.py). Each call to the engine is said before it is made: a call that brings the game down leaves
its name as the log's last line.
"""

from typing import Any, Callable

import unrealsdk

Say = Callable[[str], None]
Load = Callable[[str, str], Any]
# The engine's "no slot of that name".
NO_SLOT = -1
# The classes the look's paths name: the material copied, read on the grenade, and its textures.
PARENT_CLASS = "MaterialInstanceConstant"
TEXTURE_CLASS = "Texture2D"


def _info(parameter: dict) -> Any:
    return unrealsdk.make_struct("MaterialParameterInfo", Name=parameter["name"],
                                 Association=parameter["association"], Index=parameter["index"])


def _colour(channels: list[float]) -> Any:
    red, green, blue, alpha = channels
    return unrealsdk.make_struct("LinearColor", R=red, G=green, B=blue, A=alpha)


def _set_values(made: Any, recipe: dict, load: Load, say: Say) -> int:
    count = 0
    for parameter in recipe.get("scalars", []):
        made.SetScalarParameterValueByInfo(_info(parameter), parameter["value"])
        count += 1
    for parameter in recipe.get("vectors", []):
        made.SetVectorParameterValueByInfo(_info(parameter), _colour(parameter["value"]))
        count += 1
    for parameter in recipe.get("textures", []):
        texture = load(TEXTURE_CLASS, parameter["value"])
        if texture is None:
            say(f"texture {parameter['value']} not found: {parameter['name']} keeps the material's own")
            continue
        made.SetTextureParameterValueByInfo(_info(parameter), texture)
        count += 1
    return count


def dress(component: Any, slots: dict[str, dict], load: Load, say: Say) -> int:
    """Each slot of `slots` on `component` given its own copy of the game's material, with the look's values; a slot
    that fails keeps what it wears, and it is said. Returns how many slots were dressed."""
    dressed = 0
    for slot, recipe in slots.items():
        try:
            index = component.GetMaterialIndex(slot)
            if index == NO_SLOT:
                say(f"slot {slot}: our model has none, left undressed")
                continue
            parent = load(PARENT_CLASS, recipe["parent"])
            if parent is None:
                say(f"slot {slot}: {recipe['parent']} not found, left as it is")
                continue
            say(f"slot {slot}: CreateDynamicMaterialInstance from {recipe['parent']}")
            made = component.CreateDynamicMaterialInstance(index, parent, f"MID_ApexHeirloom_{slot}")
            say(f"slot {slot}: setting the look's values on {made._path_name()}")
            count = _set_values(made, recipe, load, say)
            say(f"slot {slot}: dressed, {count} values set")
            dressed += 1
        except Exception as exc:
            say(f"slot {slot}: could not be dressed: {exc!r}")
    return dressed
