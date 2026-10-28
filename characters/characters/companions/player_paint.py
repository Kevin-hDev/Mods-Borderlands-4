"""The player's own colours on the hunter companion dressed as the hunter the player plays (spec-compagnons.md: « la
tenue aux couleurs du joueur », shown only on that hunter's card; trial 160 of docs/renforts, vérifié en jeu: Lemmy
dressed as Vex took Kevin's colours, 13 slots of his four meshes).

Why this way (enquetes/2026-10-20-essai-160-la-tenue-du-joueur.md): the game makes for the player's meshes materials
of their own, each from one of the hunter's (MID_MI_CH_Lowerbody from MI_CH_Lowerbody). Each slot of a mesh drawing
that hunter whose own material one of them was made from is given it; the others keep the hunter's own. They are
shared, not copied: copying asks for game functions whose parameters were never read.

The hunter played is the one whose code name (DarkSiren for Vex, from his parts' names) the most of those materials
bear, in their folder (PlayerCharacters/DarkSiren/) or their name (MI_DarkSiren_U: trial 160's log, which wrote
names only); read by fields only. A material shared by every hunter, as the mouth's, bears none.

His head too (Kevin, 2026-10-22, trial 193: « Meme tenue mais pas meme tete »): the head he chose is another model,
not other colours (SK_DS_Head_16_Premium, in Customizations/DarkSiren/HeadSwaps/; the base one in DarkSiren/Heads/,
read in the game files). The companion wears it in place of the hunter's base head, only when it lies in that
hunter's folder: a head kept from another hunter played before never goes on him. It is read in the list of parts the
game merges into his body (GestaltMeshParts: hunter change, essai 16; Apex Grapple reads it there): his body is one
mesh, not one per part, and trial 194 found no head among his meshes.
"""

from itertools import islice
from typing import Any, NamedTuple

import unrealsdk

from . import hunters, wear, world

MAX_MESHES = 32
MAX_SLOTS = 24
DYNAMIC = "MaterialInstanceDynamic"
FOLDER = "/PlayerCharacters/"
LISTER = "/Script/Engine.Actor:K2_GetComponentsByClass"
HEAD_FOLDERS = ("/Heads/", "/HeadSwaps/")


class Own(NamedTuple):
    """What the player wears that a companion can take: his colours (paints) and the model of his head; parts, the
    paths of the parts his body merges, for the log when no head is found."""
    paints: dict
    head: str | None
    parts: tuple = ()


def path_of(thing: Any) -> str | None:
    if thing is None:
        return None
    try:
        return str(thing._path_name())
    except Exception:
        return None


def code(look: Any) -> str:
    """A hunter's code name in the game, from his upper body's: SKPart_DarkSiren_Upperbody, DarkSiren."""
    return look.upper.rsplit(".", 1)[-1].split("_")[1]


def bears(path: str, name: str) -> bool:
    """Whether a material's path bears that code name: its folder, or a part of its own name."""
    own = path.rsplit(".", 1)[-1]
    return f"{FOLDER}{name}/" in path or name in own.split("_")


def meshes(character: Any) -> list:
    """The player's meshes, MAX_MESHES at most; none when the call's parameters are not the ones trial 160 used."""
    try:
        have = wear.params(unrealsdk.find_object("Function", LISTER))
    except Exception:
        return []
    if have != ("ComponentClass",):
        return []
    return list(islice(character.K2_GetComponentsByClass(unrealsdk.find_class(wear.COMPONENT)), MAX_MESHES))


def paints(found: list) -> dict:
    """The materials the game made for those meshes, by the path of the material each was made from, the first one
    found for each (trial 158)."""
    made: dict = {}
    for mesh in found:
        try:
            over = list(islice(mesh.OverrideMaterials, MAX_SLOTS))
        except Exception:
            continue
        for material in over:
            parent = getattr(material, "Parent", None)
            if material is None or parent is None or str(material.Class.Name) != DYNAMIC:
                continue
            source = path_of(parent)
            if source is not None:
                made.setdefault(source, material)
    return made


def played(made: dict) -> str | None:
    """The name of the hunter the player plays, the one whose code name the most of his colours' sources bear; None
    when none bears one."""
    counted = {look.name: sum(bears(source, code(look)) for source in made) for look in hunters.LOOKS}
    best = max(counted.values(), default=0)
    return next((name for name, count in counted.items() if count == best), None) if best else None


def fitting(model: Any, made: dict) -> list[tuple[int, Any]]:
    """Each slot of the model whose own material one of the player's was made from: its index, the player's one."""
    found = []
    for index, slot in enumerate(islice(model.Materials, MAX_SLOTS)):
        source = path_of(slot.MaterialInterface)
        if source in made:
            found.append((index, made[source]))
    return found


def merged(character: Any) -> list[str]:
    """The paths of the parts the game merged into the player's body, MAX_MESHES at most; none when unread."""
    try:
        found = [path_of(part) for part in islice(character.Mesh.GestaltMeshParts, MAX_MESHES)]
    except Exception:
        return []
    return [path for path in found if path is not None]


def head(parts: list[str]) -> str | None:
    """The first of those parts lying in a heads' folder."""
    return next((path for path in parts if any(folder in path for folder in HEAD_FOLDERS)), None)


def headed(look: Any, path: str | None) -> Any:
    """The look with that head in place of its base one when it lies in that hunter's folder; else the look itself."""
    if path is None or f"/{code(look)}/" not in path:
        return look
    return look._replace(followers=tuple(path if "/Heads/Base/" in part else part for part in look.followers))


def of(pc: Any) -> Own:
    """The player's colours and head, read on his character even while he drives (world.hunter would give his
    vehicle, whose meshes are not his)."""
    character = getattr(pc, "OakCharacter", None) if pc is not None else None
    parts = merged(character)
    return Own(paints(meshes(character)), head(parts), tuple(parts))


def played_by(pc: Any) -> str | None:
    """The hunter the player plays, None when it cannot be read: the window then offers no outfit button, never one
    that would do nothing."""
    try:
        return played(of(pc).paints)
    except Exception:
        return None


def paint(drawn: list[tuple[Any, Any]], made: dict) -> int:
    """Each mesh drawing its model given the player's materials on the slots they fit; how many slots."""
    slots = 0
    for mesh, model in drawn:
        for index, material in fitting(model, made):
            mesh.SetMaterial(index, material)
            slots += 1
    return slots
