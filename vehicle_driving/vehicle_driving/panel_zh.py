"""Simplified Chinese Vehicle Driving pages and options.

载具 is the game's word for a vehicle, 镜头 the camera and 视角 a view, as in the camera mods' windows. 加速 is the
boost and 加速度 the acceleration: no official Chinese source named the boost (2026-10-13).
"""

from .panel_common_zh import TEXT as COMMON
from .panel_controls_text import ZH as CONTROLS

TEXT = {
    # The update notes' pop-up (panel_updates.py), Apex Movement's words.
    "updates_title": "更新 {version}", "updates_count": "第 {page} / {pages} 页", "updates_next": "下一页",
    **COMMON, **CONTROLS, "driving": "驾驶", "handling": "操控", "boost": "加速", "combat": "战斗",
    "camera": "镜头", "no_key": "无",
    "command_view": "切换视角",
    "command_view_desc": "驾驶时切换到下一个视角的按键。",
    "keyboard": "键盘 / 鼠标", "controller": "手柄",
    "change_keyboard": "选择按键", "change_controller": "选择按钮",
    "press_keyboard": "请按下按键", "press_controller": "请按下按钮",
    "escape_hint": "Esc 取消按键录入。控制台键已被保留。",
    "controls_reset": "已恢复默认按键。",
    "invalid_keyboard": "未保存：请选择键盘按键或鼠标按钮。之前的按键保持不变。",
    "invalid_controller": "未保存：请选择手柄按钮。之前的按钮保持不变。",
}

GROUPS = {
    "driving": "载具的速度、倒车、转向和跳跃。",
    "handling": "载具在弯道中的操控。",
    "boost": "加速的持续时间和空中推力。",
    "combat": "载具的耐久度和武器伤害。",
    "camera": "驾驶时的镜头视角，以及自定义视角的位置。",
}

OPTIONS = {
    "max_speed": ("最高速度", "100% 为游戏原本的速度，含加速。"),
    "acceleration": ("加速度", "100% 为游戏原本的加速度。"),
    "turn_speed": ("转向速度", "100% 为游戏原本的数值。"),
    "jump_height": ("跳跃高度", "100% 为游戏原本的数值。"),
    "reverse_speed": ("倒车", "100% 为游戏原本的倒车速度。"),
    "grip": ("抓地力", "载具保持行驶路线，不会打滑。"),
    "turn_loss": ("转弯减速", "直角转弯时损失的速度比例。"),
    "boost_duration": ("加速持续时间", "100% 为游戏原本的加速持续时间。"),
    "unlimited_boost": ("无限加速", "加速槽永远不会耗尽。"),
    "air_push": ("空中加速", "100% 为地面加速的推力，跳跃和下落时生效。"),
    "toughness": ("载具耐久度", "200% 即受到的伤害减半。"),
    "weapon_damage": ("武器伤害", "100% 为游戏原本的伤害，含机枪和火箭。"),
    "vehicle_view": ("载具视角", "驾驶时的镜头视角。"),
    "custom_forward": ("前 / 后", "自定义视角：镜头向前（+）或向后（-）。"),
    "custom_side": ("左 / 右", "自定义视角：镜头向右（+）或向左（-）。"),
    "custom_height": ("上 / 下", "自定义视角：镜头向上（+）或向下（-）。"),
}

# The views' names, translated from the French ones (panel_fr.CHOICES).
CHOICES = {"Far": "远", "Default": "默认", "Close": "近", "Closer": "更近", "Closest": "极近", "Custom": "自定义"}
