"""The camera window presents existing SDK options without changing their saved identifiers."""

from . import panel_camera_pages, settings

# Presentation groups are not registered with the SDK: old flat saves remain authoritative.
# This mod's FOV has no Custom FOV switch: it always applies while the mod owns the camera.
CAMERA = panel_camera_pages.groups(settings, fov=[settings.fov])
ALL = MENU = [*CAMERA]
