"""Simplified Chinese texts of Co-op Duel's window and of its message on the screen, translated from the English ones.

Every game word is the Chinese game's own, read in its .locres (Steam build 1.10.2, 2026-10-17), counted over the
game's texts outside the engine's: a duel is 决斗 (29; 单挑 28 is "come fight me", 对决 13 a showdown), a round 第一轮
(12; Round 1 is 第一轮, Round 1 - Waves 第1轮), the host 主办者 (16: Host Player 主办者玩家; 主机 is a machine, 房主 0),
the player who joined 客户端玩家 (Client Player, the game's only name for him), a vehicle 载具 (143; 车辆 4) left by
退出载具 (Exit Vehicle; 下车 0), a downed player 倒地 (Revive downed allies: 复活倒地友方), Invite Friend 邀请好友, a game
loaded 加载 with its 存档 (Failed to load saved data: 无法加载此用户的存档数据; 载入 is never that), Options 选项, and
Press any key 按任意键 (the key binding popup). The mod's name stays in Latin letters, as the other mods keep theirs.
"""

from .panel_common_zh import TEXT as COMMON

TEXT = {
    **COMMON,
    "duel": "决斗",
    "duel_how": "互相射击。倒下的一方会在地上停留 3 秒，然后原地站起，下一轮随即开始。附近的敌人会同时攻击你们两人。"
                "只有主办者需要安装此模组。",
    "start": "开始决斗", "stop": "停止决斗",
    "host": "主办者", "guest": "客户端玩家",
    "banner_start": "决斗", "banner_round": "第{round}轮", "banner_over": "决斗结束",
    "banner_refused": "CO-OP DUEL",
    "options": "选项", "ready_options": "每次更改都会立即保存。",
    "open_key_label": "打开此菜单", "open_key_hint": "在游戏中打开 Co-op Duel 的按键。",
    "duel_key_label": "开始或停止决斗",
    "duel_key_hint": "开始或停止决斗的按键，无需打开此菜单。",
    "press_key": "按任意键", "key_taken": "此按键已用于另一个快捷键：请选择其他按键。",
    "ready_duel": "站到另一名玩家身旁，两人都不在载具中，然后选择「开始决斗」。",
    "ready_on": "决斗正在进行。「停止决斗」会结束决斗，并让所有人恢复正常。",
    "start_off": "Co-op Duel 已停用。你的游戏未做任何更改。在左下角启用它，然后重新开始决斗。",
    "start_already_on": "决斗已在进行中。你的游戏未做任何更改。请先停止当前决斗，再开始新的决斗。",
    "start_not_host": "只有游戏的主办者才能开始决斗。你的游戏未做任何更改。请让主办者开始决斗。",
    "start_no_character": "此处无法决斗。你的游戏未做任何更改。请加载一个存档，然后重新开始决斗。",
    "start_in_vehicle": "无法在载具中决斗。你的游戏未做任何更改。两名玩家都退出载具后，再重新开始决斗。",
    "start_no_guest": "你的游戏中没有其他玩家。你的游戏未做任何更改。邀请好友加入后，再重新开始决斗。",
    "start_too_many": "目前决斗仅限两名玩家。你的游戏未做任何更改。请只和一名客户端玩家进行决斗。",
    "start_player_down": "有玩家倒地了。你的游戏未做任何更改。等两人都重新站起来后，再重新开始决斗。",
    "start_team_refused": "游戏拒绝了决斗。你的游戏未做任何更改。请重试；原因记录在 unrealsdk.log 中。",
    "start_refused": "决斗未能开始。你的游戏未做任何更改。请重试；原因记录在 unrealsdk.log 中。",
}

GROUPS = {"duel": "", "options": ""}

OPTIONS: dict = {}
