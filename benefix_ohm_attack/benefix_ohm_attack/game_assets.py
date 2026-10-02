"""An object of the game's archives: found in memory, or loaded when nothing holds it.

unrealsdk.load_package loads nothing in this game (Apex Heirloom, 2026-09-23); the engine's own
AssetRegistryHelpers.GetAsset does (verified in game on 2026-10-01 with the beam's effect, which the game dropped
from memory between two shots 37 s apart).
"""

from typing import Any

import unrealsdk


def load(kind: str, path: str) -> Any:
    """The object of class `kind` at `path`; ValueError when the game does not have it."""
    try:
        return unrealsdk.find_object(kind, path)
    except ValueError:
        pass
    package, name = path.rsplit(".", 1)
    kind_package, kind_name = unrealsdk.find_class(kind)._path_name().rsplit(".", 1)
    unrealsdk.find_class("AssetRegistryHelpers").ClassDefaultObject.GetAsset(unrealsdk.make_struct(
        "AssetData", PackageName=package, PackagePath=package.rsplit("/", 1)[0], AssetName=name,
        AssetClassPath=unrealsdk.make_struct("TopLevelAssetPath", PackageName=kind_package, AssetName=kind_name)))
    # What GetAsset returns is not relied on: the object is found again by its path.
    return unrealsdk.find_object(kind, path)
