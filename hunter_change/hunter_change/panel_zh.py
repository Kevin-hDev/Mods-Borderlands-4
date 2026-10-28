"""Simplified Chinese texts of Hunter Change's window, translated from the French ones.

A game the player loads is a 存档 and the file holding it a 存档文件: the window speaks of both. The class names and
the hunters' names are the Chinese game's own: 魔女, 铁骨战士, 重力法师, 锻造骑士 and Vex, Rafa, Harlowe, Amon as
维克丝, 拉法, 哈洛, 亚蒙 read on a press article quoting 2K's site (163.com, 2025-05-01); 侠盗老钱 and 黑客无爱 are the
titles of the two hunters' packs on the Chinese Steam page (read 2026-10-13). Amon is also written 阿蒙 elsewhere.
"""

from .panel_common_zh import TEXT as COMMON

TEXT = {
    **COMMON,
    "appearance": "外观",
    "applies": "立即生效，仅对此存档。",
    "look_off": "Hunter Change 已停用：在左下角启用它，才能更换外观。",
    "your_hunter": "你的猎人",
    "chosen": "已选",
    "no_game": "载入一个存档，即可选择外观。",
    "own_look": "你正在使用{played}。选择一名秘藏猎人，换上其外观。",
    "worn_look": "你正在使用{played}。当前外观：{worn}。选择{own}，即可换回你自己的外观。",
    "skin_body": "身体",
    "skin_head": "头部",
    "skin_body_hint": "当前外观的身体。只列出你拥有的皮肤。",
    "skin_head_hint": "当前外观的头部，可与任意身体搭配。",
    "skin:default": "基础",
    "skin:prison": "囚服",
    "skin:premium": "高级",
    "class:DarkSiren": "魔女",
    "class:ExoSoldier": "铁骨战士",
    "class:Gravitar": "重力法师",
    "class:Paladin": "锻造骑士",
    "class:RoboDealer": "侠盗",
    "class:CorpoHacker": "黑客",
    "hunter": "猎人",
    "keeps": "等级、背包、剧情都不变。每名秘藏猎人保留各自的技能树。",
    "switch_nowhere": "载入一个存档，或在标题画面选择一个存档，即可更换它的秘藏猎人。",
    "switch_busy": "Hunter Change 正在更换此存档的秘藏猎人。请等待几秒，然后重新打开此窗口。",
    "why:no_save": "无法更换此存档的秘藏猎人：模组在游戏的存档文件夹中找不到它的存档文件。你的存档未受影响，可照常游玩。",
    "why:two_saves": "无法更换此存档的秘藏猎人：此存档存在于多个存档文件中，模组无法判断游戏使用的是哪一个。你的存档未受影响，"
                     "可照常游玩。如果其中一个是你不再需要的旧副本，将它移出游戏的存档文件夹，即可更换猎人。",
    "why:saves_unsure": "暂时无法更换此存档的秘藏猎人：模组未能读取游戏的全部存档文件，可能有其他程序（如 OneDrive）正在使用"
                        "它们。你的存档未受影响。请稍后重新打开此窗口。",
    "why:save_damaged": "无法更换此存档的秘藏猎人：它的存档文件无法完整读取，因此模组不会改动它。",
    "why:unknown_hunter": "无法更换此存档的秘藏猎人：模组还不认识此存档的猎人。你的存档未受影响，可照常游玩。",
    "why:trees_unreadable": "无法更换任何秘藏猎人：模组保存技能树的文件无法读取。你的存档均未受影响，可照常游玩。",
    "why:not_this_hunter": "无法更换此存档的秘藏猎人：它的存档文件显示的不是你正在使用的猎人。请重新载入此存档。",
    "switch_in_game": "你正在使用{current}。选择一名秘藏猎人，在此存档中换成该猎人。",
    "switch_at_title": "此存档的秘藏猎人是{current}。选择一名猎人：立即完成更换。",
    "confirm": "你将在此存档中成为{new}：等级、背包、剧情都不变。每名秘藏猎人在此存档中第一次被选用时，技能树会重置，"
               "所有技能点都可重新分配；之后再选用时，已分配的技能点保持不变。{old}的技能树会保留，等你换回时再用。{tree}"
               "游戏会保存你的存档并返回主菜单。在主菜单等待 5 秒，选择另一个存档，再重新选择这个存档：它会显示{new}。"
               "然后选择「继续」。",
    "tree_first": "{new}在此存档中还没有技能树：所有技能点都可自由分配。",
    "tree_back": "{new}会找回自己的技能树，保留你之前分配的技能点。",
    "leave_button": "返回主菜单",
    "cancel_button": "取消",
    "said:done": "{new}现在是此存档的秘藏猎人。关闭此窗口，选择另一个存档，再重新选择这个存档：它会显示{new}。",
    "said:no_save": "模组没有找到此存档的存档文件。未做任何更改：你的存档可照常游玩。",
    "said:two_saves": "此存档存在于多个存档文件中，模组无法判断游戏使用的是哪一个。未做任何更改：你的存档可照常游玩。"
                      "如果其中一个是你不再需要的旧副本，将它移出游戏的存档文件夹，即可更换秘藏猎人。",
    "said:saves_unsure": "模组未能读取游戏的全部存档文件，可能有其他程序（如 OneDrive）正在使用它们。未做任何更改。"
                         "请稍后再试。",
    "said:save_damaged": "此存档的存档文件无法完整读取。未做任何更改：模组不会改动它。",
    "said:changed": "此存档的存档文件在此期间发生了变化。未做任何更改。请重试。",
    "said:unsafe": "无法安全地更改此存档的技能树。未做任何更改：此存档可照常游玩。",
    "said:trees": "模组保存技能树的文件无法读取。未做任何更改：此存档可照常游玩。",
    "said:not_written": "存档文件无法写入。未做任何更改。请重试。",
    "said:unverified": "存档文件已写入，但无法重新读取。选择另一个存档，再重新选择这个存档，即可查看。",
    "said:restore_failed": "存档文件既无法写入，也无法恢复。请不要载入此存档，并到模组页面寻求帮助：模组已为它保留了一份备份。",
    "said:no_return": "游戏无法返回主菜单。未做任何更改。请重试。",
    "said:gave_up": "游戏返回主菜单的时间过长。未做任何更改。请重试。",
    "said:loaded": "在更换秘藏猎人之前，有一个存档被载入了。未做任何更改。请重试。",
    "said:error": "更改存档文件时出现问题。选择另一个存档，再重新选择这个存档，即可查看它的秘藏猎人。",
}

GROUPS = {
    "appearance": "换上另一名秘藏猎人的外观。你的等级和技能树保持不变。",
    "hunter": "在此存档中成为另一名秘藏猎人。",
}

OPTIONS: dict = {}

# By hunter code (hunters.py), read by panel_hunter_names.py: a Chinese player knows the hunters by these names.
NAMES = {
    "DarkSiren": "维克丝",
    "ExoSoldier": "拉法",
    "Gravitar": "哈洛",
    "Paladin": "亚蒙",
    "RoboDealer": "老钱",
    "CorpoHacker": "无爱",
}
