"""Omni Sprint's settings as its window's pages; the SDK menu keeps its flat list (settings.OPTIONS)."""

from mods_base import NestedOption

from . import panel_camera_text, settings

# Left out of the mod's options: saved values stay at the top level of the settings file, where they were before the
# window existed.
sprint = NestedOption(
    "omni_sprint_menu", [settings.omni_sprint],
    display_name="Omni Sprint", description="The game's sprint, in every direction.",
)
camera = NestedOption(
    "camera_menu", [settings.third_person, settings.third_person_key, settings.custom_fov, settings.fov],
    display_name="Camera", description=panel_camera_text.EN["camera_desc"],
)

ALL = MENU = [sprint, camera]
