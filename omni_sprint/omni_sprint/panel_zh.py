"""Simplified Chinese Omni Sprint texts: camera words from the common camera vocabulary, plus the sprint page."""

from .panel_camera_pages import page_texts
from .panel_camera_text import ZH as CAMERA, ZH_OPTIONS
from .panel_common_zh import TEXT as COMMON

# The sprint switch is the same setting as Apex Movement's omni_direction_sprint: its words come from there, once.
SPRINT = ZH_OPTIONS["omni_direction_sprint"]
# The sprint page's tab is translated like OMNI DIRECTION's (Kevin, 2026-10-12); the window's logo keeps the mod's
# name.
TEXT = {**COMMON, **CAMERA, "omni_sprint": SPRINT[0]}
GROUPS = {"omni_sprint": "游戏自带的疾跑，任何方向都能用。", **page_texts(CAMERA)}
OPTIONS = {"omni_sprint": SPRINT, **ZH_OPTIONS}
