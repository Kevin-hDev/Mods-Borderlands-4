"""Simplified Chinese for Apex Grapple's window. Its first keys are the window words every mod shares
(sync_menu_sources.COMMON_TEXT): sync_menu_messages.py reads TEXT with ast, so it stays one plain literal dictionary.

抓钩 is the grapple, as Chinese guides name BL4's own (18183.com, 2025-09-24); 钩爪 is the hook it fires and 牵引 the
pull. Page names in a sentence are written 「…」.
"""

TEXT = {
    "close": "关闭", "restore": "恢复默认设置", "undo": "撤销重置",
    "enabled": "已启用", "disabled": "已停用", "on": "开", "off": "关",
    "by": "作者", "version": "版本", "settings": "设置",
    "ready": "更改会自动保存。选择「关闭」返回模组列表。",
    "saved": "已保存。", "failed": "无法保存设置，请重试。",
    "rollback_abandoned": "更改已取消，但未能确认恢复成功。请重启游戏后再更改设置。",
    "toggle_failed": "无法启用或停用模组，未做任何更改。原因记录在 unrealsdk.log 中。",
    "refused": "无法绑定：此按键已被保留或已被占用。",
    "restored": "已恢复默认设置。可选择「撤销重置」撤销。",
    "undone": "已恢复之前的设置。",
    "theme": "主题：", "theme:EMBER": "余烬", "theme:DARK": "暗色", "theme:LIGHT": "亮色", "theme:BL4": "BL4",
    "theme_later": "主题已保存，下次打开菜单时生效。",
    "window_size": "窗口：", "window_size:LARGE": "大", "window_size:FULL": "全屏", "window_size:NORMAL": "标准",
    "window_size_later": "窗口大小已保存，下次打开菜单时生效。",
    "shot": "发射", "pull": "牵引", "release": "脱离", "controls": "按键",
    "controls_intro": "选择一个键位，然后按下键盘、鼠标或手柄上的按键。选择完整后自动保存。",
    "two": "同时按住两个按键", "first": "1. 选择按键", "second": "2. 选择第二个按键",
    "listening": "请按下按键", "reset_controls": "默认按键",
    "one_hint": "选择一个按键。按键会立即保存。",
    "two_hint": "从同一设备选择两个按键。同时按住它们即可发射抓钩。",
    "escape_hint": "Esc 取消按键录入。控制台键已被保留。单独按下时，每个按键保持原本的功能。",
    "keyboard": "键盘 / 鼠标", "gamepad": "手柄", "game_controls": "游戏按键",
    "invalid_keys": "未保存。请从同一设备选择不同的按键。Esc 和控制台键已被保留。",
    "controls_saved": "按键已保存。", "controls_reset": "已恢复抓钩的默认按键。",
    "current_controls": "当前按键",
    # Brand names, never translated.
    "controller_icons": "手柄图标", "PS5": "PLAYSTATION", "XSX": "XBOX",
    "game_controls_pending": "游戏按键（进入游戏后可用）",
    "reserved_key": "未保存：此按键已保留给控制台或取消操作。之前的按键保持不变。",
}
OPTIONS = {
    "grapple_range": ("射程", "钩爪的最远距离。3000 = 30 米。"),
    "hook_speed": ("钩爪速度", "钩爪飞向目标的速度。"),
    "melee_wins": ("近战优先", "对着敌人时，按键会出拳，而不是发射抓钩。"),
    "stamina_cost": ("耐力消耗", "每次发射消耗的耐力条比例。33 = 三次发射，0 = 不消耗。"),
    "punch_range": ("近战距离", "比此距离更近的敌人会挨一拳。"),
    "keyboard_hold": ("键盘：按住发射抓钩", "按住按键发射抓钩；短按近战键则出拳。"),
    "controller_hold": ("手柄：按住发射抓钩", "按住按钮发射抓钩；短按近战按钮则出拳。"),
    "hold_time": ("按住时长", "需要按住的时间，单位为秒。"),
    "keep_game_grapple": ("保留游戏抓钩", "游戏的钩点仍使用游戏自带的抓钩。"),
    "show_rope": ("显示绳索", "显示绳索和手臂动画。"),
    "pull_strength": ("牵引力度", "绳索拉动你的力度。"),
    "pull_speed_cap": ("最大牵引速度", "绳索提供的最高速度。你的惯性会叠加在上面。"),
    "rope_carry": ("绳索托举", "绳索承担的体重比例：100% 时，绳索托住你；0% 时，整个牵引过程都受重力影响。"),
    "steer_strength": ("转向力度", "摇杆让你的轨迹弯曲的程度。"),
    "steer_speed_cap": ("最大转向速度", "牵引时摇杆增加的最大横向速度。"),
    "release_on_key_up": ("按住持续牵引", "松开按键即脱离抓钩。短按则一直牵引到底。"),
    "arrival_distance": ("到达距离", "离钩点只剩此距离时，牵引停止。"),
    "longest_pull": ("最长牵引时间", "单位为秒。0 = 无限制。"),
    "takeoff_lift": ("起跳高度", "从地面出发时轻轻一跳。为 0 时，你贴地出发。"),
    "ground_grace": ("离地时间", "出发时在这段时间内忽略地面，以便离地。"),
    "release_on_landing": ("落地时脱离", "接触地面会结束牵引。"),
    "block_jump": ("脱离时保留跳跃", "跳跃脱离抓钩不会消耗跳跃次数。"),
}
GROUPS = {
    "shot": "射程、钩爪速度、近战和视觉效果。",
    "pull": "绳索力度、速度和轨迹控制。",
    "release": "结束牵引的条件。已达到的速度会保留。",
}
