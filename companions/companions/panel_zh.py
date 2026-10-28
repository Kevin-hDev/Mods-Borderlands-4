"""Companions' window in Chinese. The game's words as the game's zh-Hans texts name them, as It Follows' window does
(its test_chinese_texts.py counts them): 伙伴 for a companion, 秘藏猎人 for the Vault Hunters, 生命值, 护盾, 充能 for
a recharge, 速度, 死亡, 暂停, 存档 for a game loaded; a sentence names a button as it shows, in 「」. The cards' and
the keys' words are It Follows' own."""

from .panel_common_zh import TEXT as COMMON

TEXT = {
    **COMMON,
    "hunters": "秘藏猎人", "allies": "盟友", "team_settings": "队伍设置", "options": "选项",
    "team_count": "队伍 {count} / {most}",
    "team_none": "还没有伙伴：选择一名伙伴即可加入队伍。",
    "outfit": "外观", "outfit:own": "默认", "outfit:player": "你的配色",
    "team_launch": "启动队伍", "team_stop": "停止队伍",
    "cards_locked": "先停止队伍才能更改。",
    "settings_locked": "先停止队伍才能更改设置：队伍保持启动时的设置。",
    "team_elsewhere": "It Follows 正在控制伙伴。请使用它的菜单。",
    "team_outdated": "此 It Follows 版本过旧，即使已停用也无法共享伙伴：请更新它，然后重启游戏。",
    "team_mismatch": "It Follows 和 Companions 的版本不兼容，伙伴队伍无法启动：请更新这两个模组，然后重启游戏。",
    "ready_cards": "选择伙伴加入队伍，然后选择「启动队伍」。",
    "team_on_notice": "你的队伍正在跟随你。在这里停止队伍才能更改。",
    "ready_settings": "队伍设置适用于你所有的伙伴。",
    "team_full": "队伍已满：最多{most}名伙伴。",
    "team_empty": "请先加入至少一名伙伴。",
    "team_busy": "正在保存你的选择：请再次启动队伍。",
    "team_off": "Companions 已停用：请先在左下角启用，再启动队伍。",
    "team_not_started": "队伍未能启动。原因记录在 unrealsdk.log 中。",
    "team_already_on": "队伍已经启动。",
    "team_main_menu": "请先加载一个存档，再启动队伍。",
    "team_stopped": "队伍已停止：伙伴不再跟随你。",
    "key_label": "菜单按键", "press_key": "按任意键", "no_key": "无",
    "key_hint": "在游戏中打开此菜单；菜单打开时游戏会暂停，合作模式除外。选择该栏即可设定按键。",
    "team_key_label": "队伍按键",
    "team_key_hint": "游戏中启动或停止你的队伍。选择该按键即可更改。",
    "key_taken": "这个按键已是 Companions 的另一个按键：请选择其他按键。",
    "value_times": "×{value}", "value_percent": "{value}%", "value_bonus": "+{value}%", "value_seconds": "{value}秒",
    "value_never": "从不",
}

GROUPS = {"hunters": "秘藏猎人只用武器战斗，不使用技能。", "allies": "", "settings": "适用于你所有的伙伴。"}

OPTIONS = {
    "health_times": ("生命值", "你的秘藏猎人生命值的倍数。"),
    "shield_percent": ("护盾", "占伙伴生命值的比例。0%：没有护盾。"),
    "shield_refill_s": ("护盾充能", "护盾被打破后，到重新充能前的时间。"),
    "speed_percent": ("速度", "在伙伴自身速度之上增加。"),
    "back_after_s": ("死亡后返回", "经过这段时间后，伙伴会回到你身边。"),
    "companion_bars": ("屏幕生命值条", "在屏幕左下角显示每名伙伴的生命值，就像合作模式中的队友。"),
}
