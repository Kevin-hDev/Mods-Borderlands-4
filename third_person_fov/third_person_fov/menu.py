"""The camera window presents existing SDK options without changing their saved identifiers."""

from . import panel_camera_pages, settings

# Presentation groups are not registered with the SDK: old flat saves remain authoritative.
# This mod's FOV has no Custom FOV switch: it always applies while the mod owns the camera.
CAMERA = panel_camera_pages.groups(settings, fov=[settings.fov])
# OMNI DIRECTION, the last camera page, right after CAMERA, the mod's main page (Kevin, 2026-10-09, sketch
# omni_direction/third_person.png).
ALL = MENU = [CAMERA[0], CAMERA[-1], *CAMERA[1:-1]]
