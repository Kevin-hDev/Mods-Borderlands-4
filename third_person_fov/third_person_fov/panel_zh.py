"""Simplified Chinese camera window labels from the common camera vocabulary."""

from .panel_camera_pages import page_texts
from .panel_camera_text import ZH as CAMERA, ZH_OPTIONS
from .panel_common_zh import TEXT as COMMON

# The key that opens this window in game (open_key.py, panel_open_key.py).
TEXT = {**COMMON, **CAMERA,
        "command_open_window": "菜单快捷键",
        "command_open_window_desc": "在游戏中打开或关闭此窗口。",
        "open_key_command": "此按键已用于某项镜头按键功能：请换一个。",
        "key_opens_window": "此按键用于打开此窗口（菜单快捷键）：请换一个。"}
GROUPS = page_texts(CAMERA)
OPTIONS = ZH_OPTIONS
