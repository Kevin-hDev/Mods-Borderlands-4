"""Omni Sprint's settings as its window's pages; the SDK menu keeps its flat list (settings.OPTIONS)."""

from mods_base import NestedOption

from . import panel_camera_pages, settings

# Left out of the mod's options: saved values stay at the top level of the settings file, where they were before the
# window existed.
sprint = NestedOption(
    "omni_sprint_menu", [settings.omni_sprint],
    display_name="Omni Sprint", description="The game's sprint, in every direction.",
)
CAMERA = panel_camera_pages.groups(settings, fov=[settings.custom_fov, settings.fov])

# OMNI DIRECTION, the last camera page, right after OMNI SPRINT: its dash or slide follows that page's switch (Kevin,
# 2026-10-09, sketch omni_direction/omni_sprint.png).
ALL = MENU = [sprint, CAMERA[-1], *CAMERA[:-1]]
