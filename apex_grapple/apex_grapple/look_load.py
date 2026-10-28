"""Our pieces, found in the game's memory or loaded from our container, and the list of those the game does not have.

unrealsdk.load_package loads nothing in this game; the engine's own AssetRegistryHelpers.GetAsset does (verified in
game by Apex Heirloom on 2026-09-23, and by Benefix Ohm Attack, whose game_assets.py this follows, on 2026-10-01).
What GetAsset returns is not relied on: the object is found again by its path.
"""

from typing import Any

import unrealsdk

MESH, MATERIAL, TEXTURE, ANIMATION = "StaticMesh", "MaterialInstanceConstant", "Texture2D", "AnimSequence"


class Missing(Exception):
    """Pieces the game does not have, by path: our container is not installed, or no longer fits the game."""

    def __init__(self, paths: list[str]) -> None:
        super().__init__(f"{len(paths)} of our pieces missing, the first: {paths[0]}")
        self.paths = paths


def _load(kind: str, path: str) -> Any:
    try:
        return unrealsdk.find_object(kind, path)
    except ValueError:
        pass
    package, name = path.rsplit(".", 1)
    kind_package, kind_name = unrealsdk.find_class(kind)._path_name().rsplit(".", 1)
    unrealsdk.find_class("AssetRegistryHelpers").ClassDefaultObject.GetAsset(unrealsdk.make_struct(
        "AssetData", PackageName=package, PackagePath=package.rsplit("/", 1)[0], AssetName=name,
        AssetClassPath=unrealsdk.make_struct("TopLevelAssetPath", PackageName=kind_package, AssetName=kind_name)))
    return unrealsdk.find_object(kind, path)


def animation(path: str) -> Any:
    """One animation, ours or the game's, looked up right before it plays and never kept: on 2026-10-14 the game
    crashed playing one kept 27 s, nothing of the game holding it meanwhile (docs/apex_grapple/pistolet-grappin/
    enquetes/2026-10-14-gestes-ensemble.md)."""
    try:
        return _load(ANIMATION, path)
    except ValueError:
        raise Missing([path]) from None


def fetch(wanted: list[tuple[str, str]]) -> dict[str, Any]:
    """Each (kind, path) of `wanted` as the game's object, by path; Missing names every one the game does not have.
    Any other error of the game propagates: it is a failure, not a missing piece."""
    found, missing = {}, []
    for kind, path in dict.fromkeys(wanted):
        try:
            found[path] = _load(kind, path)
        except ValueError:
            missing.append(path)
    if missing:
        raise Missing(missing)
    return found
