"""The camera window presents existing SDK options without changing their saved identifiers."""

from mods_base import NestedOption

from . import panel_camera_text, settings

# Presentation groups are not registered with the SDK: old flat saves remain authoritative.
camera = NestedOption(
    "camera_menu", [settings.third_person, settings.shoulder_left, settings.orbit,
                    settings.fov, *settings.loot.options],
    display_name="Camera", description=panel_camera_text.EN["camera_desc"],
)
ALL = MENU = [camera]
