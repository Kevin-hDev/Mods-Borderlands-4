"""Simplified Chinese texts of Co-op Duel's window and of its message on the screen, translated from the English ones.

Every game word is the Chinese game's own, read in its .locres (Steam build 1.10.2, 2026-10-17), counted over the
game's texts outside the engine's: a duel is 决斗 (29; 单挑 28 is "come fight me", 对决 13 a showdown), a round 第一轮
(12; Round 1 is 第一轮, Round 1 - Waves 第1轮), the host 主办者 (16: Host Player 主办者玩家; 主机 is a machine, 房主 0),
the player who joined 客户端玩家 (Client Player, the game's only name for him), a vehicle 载具 (143; 车辆 4) left by
退出载具 (Exit Vehicle; 下车 0), a downed player 倒地 (Revive downed allies: 复活倒地友方), Invite Friend 邀请好友, a game
loaded 加载 with its 存档 (Failed to load saved data: 无法加载此用户的存档数据; 载入 is never that), Options 选项, and
Press any key 按任意键 (the key binding popup). The mod's name stays in Latin letters, as the other mods keep theirs.
1.0.1's teams: a downed player stood up by a teammate is 复活 (Revive downed allies), the bandits 强盗 and the Order 教团
as bl4_arena's panel_zh.py reads them in the game; a team 队伍, team 2 第2队, each for themselves 各自为战, a draw 平局.
"""

from .panel_common_zh import TEXT as COMMON

TEXT = {
    **COMMON,
    "duel": "决斗",
    "duel_how": "互相射击。倒下的玩家会安全地留在地上，直到本轮结束，队友可以将其复活。最后仍有人站着的队伍赢得本轮，"
                "随后所有人原地站起。只有两支队伍时，附近的敌人会攻击所有人。只有主办者需要安装此模组。",
    "start": "开始决斗", "stop": "停止决斗",
    "host": "主办者",
    "banner_start": "决斗", "banner_round": "第{round}轮", "banner_over": "决斗结束",
    "banner_refused": "CO-OP DUEL",
    "banner_draw": "平局", "team_name": "第{team}队", "player_fallback": "玩家 {number}",
    "teams": "队伍", "teams_each": "各自为战", "teams_vs": "对", "teams_one": "只有一支队伍",
    "ready_teams": "选择每名玩家的队伍。独自一队的玩家各自为战。",
    "teams_allies": "三支或更多队伍：附近的强盗或教团士兵可能会与某支队伍并肩作战。",
    "teams_alone": "你的游戏中没有其他玩家。邀请好友后，他们会显示在这里。",
    "teams_locked": "决斗正在进行。请先在决斗页面停止决斗，再更改队伍。",
    "teams_not_host": "只有游戏的主办者才能安排队伍。",
    "options": "选项", "ready_options": "每次更改都会立即保存。",
    "open_key_label": "打开此菜单", "open_key_hint": "在游戏中打开 Co-op Duel 的按键。",
    "duel_key_label": "开始或停止决斗",
    "duel_key_hint": "开始或停止决斗的按键，无需打开此菜单。",
    "press_key": "按任意键", "key_taken": "此按键已用于另一个快捷键：请选择其他按键。",
    "ready_duel": "站到其他玩家附近，所有人都不在载具中，然后选择「开始决斗」。",
    "ready_on": "决斗正在进行。「停止决斗」会结束决斗，并让所有人恢复正常。",
    "start_off": "Co-op Duel 已停用。你的游戏未做任何更改。在左下角启用它，然后重新开始决斗。",
    "start_already_on": "决斗已在进行中。你的游戏未做任何更改。请先停止当前决斗，再开始新的决斗。",
    "start_not_host": "只有游戏的主办者才能开始决斗。你的游戏未做任何更改。请让主办者开始决斗。",
    "start_no_character": "此处无法决斗。你的游戏未做任何更改。请加载一个存档，然后重新开始决斗。",
    "start_in_vehicle": "无法在载具中决斗。你的游戏未做任何更改。所有人退出载具后，再重新开始决斗。",
    "start_player_away": "有玩家还没有角色：正在加入或重新出现。你的游戏未做任何更改。等待该玩家，然后重新开始决斗。",
    "start_one_team": "所有玩家都在同一支队伍中。你的游戏未做任何更改。在队伍页面将他们分开，然后重新开始决斗。",
    "start_no_guest": "你的游戏中没有其他玩家。你的游戏未做任何更改。邀请好友加入后，再重新开始决斗。",
    "start_player_down": "有玩家倒地了。你的游戏未做任何更改。等所有人都重新站起来后，再重新开始决斗。",
    "start_team_refused": "游戏拒绝了决斗。你的游戏未做任何更改。请重试；原因记录在 unrealsdk.log 中。",
    "start_refused": "决斗未能开始。你的游戏未做任何更改。请重试；原因记录在 unrealsdk.log 中。",
    "stop_player_joined": "有玩家加入了游戏。在队伍页面将其分入一支队伍，然后重新开始决斗。",
    "stop_teams_left": "只剩下一支队伍。在队伍页面将玩家分开，或邀请好友，然后开始新的决斗。",
}

GROUPS = {"duel": "", "teams": "", "options": ""}

OPTIONS: dict = {}
