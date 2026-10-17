"""It Follows' window in Simplified Chinese, its third language, translated from the English one.

Every game word is the Chinese game's own, read in its .locres (Steam build 1.10.2, 2026-10-17), counted over the
game's texts outside the engine's: Vault Hunter 秘藏猎人 (2743 of 2906 rows), enemy 敌人 (1110; 敌方 9), kill 击杀
(1030; 杀死 16, 消灭 14), death 死亡 (200; 阵亡 0), Boss in Latin letters (85; 首领 0), shield 护盾 (333) and its
recharge 充能 (Shield Recharge Delay 护盾充能延迟; 充电 2), a shield depleted 耗尽, health 生命值 (203; 血量 0), dodge
闪避 (3; 躲避 0), companion 伙伴 (Companion Damage 伙伴伤害, 18; 同伴 12), level 等级 (Mayhem Level 混乱等级, Lvl 等级)
and difficulty 难度 (16), fast travel 快速移动 (54; 快速旅行 0), damage 伤害 (1678), map 地图 (66), zone 区域 (12;
地区 0), pause 暂停 (11), weapon 武器 (431), bullet 子弹 (183; 弹药 13), accuracy 精准度 (Gun Accuracy 武器精准度),
speed 速度 (223), chase 追击 (Cyber Chase), on foot 步行 (Only On Foot 仅步行时), vehicle 载具 and Exit Vehicle 退出载具,
graphics 图形 (Graphics Preset 图形预设, 12; 画质 0), Quit to Main Menu 退出至主菜单, Quit Game 退出游戏, a save 存档
loaded 加载, solo 单人 (Solo campaign 单人主剧情), Normal 普通 (5; 正常 1), Buff 增益, Infinite 无限, Progress 进度,
Hardcore Mode 硬核模式 (硬核 7 of 7 rows), the game's name 《无主之地®4》, Bandit 匪徒 (21; 强盗 8), Predator 掠食者
(19), Veteran 资深 (Senior's nearest; 老手 1). The game has no word for a horde (a horde of bandits is 一群强盗): the
mod's horde is 敌群, a run 一局. The mod's name stays in Latin letters, as the other mods keep theirs. Buttons named in
a sentence are quoted 「…」, as the buttons show them; a controller player selects, never clicks (选择, never 点击).
"""

from .panel_common_zh import TEXT as COMMON

TEXT = {
    **COMMON,
    "run": "敌群模式【测试版】", "normal": "普通模式", "history": "历史记录", "options": "选项",
    "running_tag": "进行中",
    "run_settings": "单局设置", "run_live": "本局进行中 · {level}",
    "kills": "击杀", "deaths": "死亡", "time": "时间", "start": "开始", "stop": "停止",
    "caution": "数十个敌人会同时追杀你，根据所选等级，最多可超过一百个：此模式对你的电脑要求很高。如果游戏变慢，"
               "请降低「最大敌人数」、选择更低的等级、降低游戏的图形设置，或关闭在后台运行的程序。",
    "locked": "停止本局后才能更改这些设置。",
    "help_run_title": "一局如何进行",
    "help_run": "每局开始时很平静：附近的敌人开始追击你。\n\n"
                "如果开始时你附近没有敌人，就去找它们：否则什么也不会发生。\n\n"
                "你击杀的敌人越多，敌人就会越多。\n\n"
                "每击杀 100 个敌人，它们还会变强 1%：这就是状态栏中的硬核百分比，每局从 0 重新开始。\n\n"
                "跟随你的敌人类型取决于你所在的区域，以及你经过的区域。\n\n"
                "想让敌人有所变化，就在地图上四处移动。",
    "ready_run": "准备就绪：选择「开始」，菜单会关闭，本局随即开始。",
    "paused_run": "此菜单打开时，游戏处于暂停状态。",
    "ready_history": "最近 20 局的记录，重新启动游戏后依然保留。",
    "ready_options": "更改会随时保存。",
    "start_busy": "正在保存你的设置：请再次选择「开始」。",
    "start_off": "It Follows 已停用：请启用它，然后选择「开始」。",
    "start_in_vehicle": "无法在载具中开始一局：请退出载具，然后选择「开始」。",
    "start_no_character": "无法在此处开始一局：请先加载一个存档。",
    "start_coop": "It Follows 目前只能在单人游戏中使用。你的游戏未做任何更改。",
    "start_already_running": "已有一局正在进行。",
    "start_normal_on": "请先停止普通模式，然后选择「开始」。",
    "run_blocked": "普通模式已开启：请在它的页面上将其停止，才能开始一局。",
    "normal_settings": "普通模式", "normal_lead": "对游戏敌人的首次改造，仍在持续完善。",
    "normal_live": "普通模式进行中 · {level}",
    "normal_playing": "你游玩时，敌人会变强。「停止」会让它们恢复成游戏原本的样子。",
    "normal_waiting": "只要你在已加载的游戏中步行，它就会开始。",
    "normal_locked": "停止普通模式后才能更改这些设置。",
    "normal_blocked": "敌群模式的一局正在进行：请先停止它，再开启普通模式。",
    "normal_level:Bandit": "敌人更多，速度稍快，也更坚韧。它们闪避更快，追击你的距离更远。"
                           "没有护盾的敌人可获得一个护盾，由你决定。",
    "normal_level:Senior": "敌人还要更多，速度更快，也更坚韧。闪避更迅速，追击距离更长。"
                           "每个没有护盾的敌人都会获得一个护盾。",
    "normal_level:Predator": "敌人还要更多，速度非常快，也非常坚韧。闪避快如闪电，追击你的距离远得多。"
                             "每个没有护盾的敌人都会获得一个护盾，护盾耗尽 10 秒后重新充能。",
    "hardcore_settings": "硬核", "hardcore_lead": "在整个游戏过程中缓慢上升的难度。",
    "hardcore_badge": "硬核 {percent}%", "hardcore_badge_paused": "硬核 {percent}% · 已暂停",
    "help_hardcore_title": "硬核模式",
    "help_hardcore": "在《无主之地4》中，敌人的等级会跟随你的秘藏猎人的等级：游戏从不会真正变难，甚至一直很简单。\n\n"
                     "硬核模式改变了这一点。开启时，它不会改变任何东西。之后，每击杀 100 个敌人，敌人就会变强 1%，"
                     "在整个游戏过程中缓慢而稳定地上升。这会叠加在所选等级之上。\n\n"
                     "这个硬核只在普通模式开启时生效：敌群模式有它自己的硬核，每局重新开始。"
                     "已达到的百分比显示在菜单顶部。\n\n"
                     "你可以暂停它的进度，以保持适合你的难度，也可以随时关闭此模式：你的进度会被保留，"
                     "重新开启时即可恢复。",
    "ready_normal": "准备就绪：选择「开始」，菜单会关闭，普通模式随即开始。",
    "normal_waiting_notice": "普通模式已开启：只要你在已加载的游戏中步行，它就会开始。",
    "start_horde_running": "请先停止敌群模式的这一局，然后选择「开始」。",
    "start_already_on": "普通模式已经开启。",
    "normal_start_failed": "普通模式未能开始。你的游戏未做任何更改。原因记录在 unrealsdk.log 中。",
    "normal_stop_unsaved": "普通模式已停止，但这一更改未能保存：下次启动游戏时，它可能会重新开启。",
    "start_failed": "本局未能开始。原因记录在 unrealsdk.log 中。如果敌人行为异常，请退出至主菜单，然后重新加载你的存档。",
    "start_refused": "本局无法在此处开始。你的游戏未做任何更改。原因记录在 unrealsdk.log 中。",
    "history_title": "最近 20 局", "history_empty": "还没有任何一局记录：你的每一局都会列在这里。",
    "col_when": "开始时间", "col_level": "等级", "col_limit": "时间限制", "col_held": "坚持时长", "col_kills": "击杀",
    "col_deaths": "死亡", "col_end": "结束方式",
    "clock_time": "{hour:02d}:{minute:02d}", "today": "今天 {time}", "yesterday": "昨天 {time}",
    "day": "{month}{day}日 {time}", "months": "1月 2月 3月 4月 5月 6月 7月 8月 9月 10月 11月 12月",
    "end:time_up": "时间到", "end:stopped": "停止", "end:left_game": "已退出游戏", "end:mod_disabled": "模组已停用",
    "end:interrupted": "自行停止",
    "level_number": "等级 {number}",
    "result:time_up": "时间到", "result:stopped": "本局已停止", "result:interrupted": "本局自行停止",
    "result_sentence:time_up": "你在{level} 下坚持了 {held}。敌人不再前来。",
    "result_sentence:stopped": "你在{level} 下坚持了 {held}。敌人不再前来。",
    "result_sentence:interrupted": "本局在{level} 下进行 {held} 后自行停止：敌人不再前来。你的游戏未做任何更改。"
                                   "原因记录在 unrealsdk.log 中。",
    "key_label": "菜单按键", "press_key": "按任意键",
    "key_hint": "在游戏中打开此菜单；菜单打开时，游戏会暂停。选择该按键即可更改。",
    "welcome_title": "欢迎来到 IT FOLLOWS",
    "welcome_lead": "It Follows 包含两种相互独立的模式。敌群模式：选择「开始」，你周围的所有敌人都会冲向你，"
                    "并跟着你到处走。你在路上遇到的敌人会加入敌群，你击杀的敌人会卷土重来。尽可能坚持下去。",
    "welcome_film_title": "电影《它在身后》（IT FOLLOWS）",
    "welcome_film": "某个东西一直朝你走来，从不停下，无论你走到哪里。",
    "welcome_zombies_title": "《使命召唤：黑色行动》僵尸模式",
    "welcome_zombies": "无穷无尽、不断卷土重来的敌群，随等级不断壮大。你击杀，你奔跑，你生存。",
    "welcome_next": "下一页",
    "updates_title": "更新 {version}",
    "updates_count": "{page} / {pages}",
    "updates_next": "下一页",
    "welcome_normal_lead": "普通模式：像平常一样玩你的游戏。你遇到的敌人更多、更快、更坚韧，闪避更快，追击你的距离更远。"
                           "它首先是为从头开始或重新开始游戏而设计的，有点像三个等级的多周目，在游戏中途也能使用。",
    "welcome_levels_title": "三个等级",
    "welcome_levels": "匪徒、资深和掠食者，从更难的游戏到难得多的游戏。",
    "welcome_evolving_title": "持续完善中",
    "welcome_evolving": "对游戏敌人的首次改造，会随着一个又一个版本持续完善。",
    "welcome_go": "出发",
}

GROUPS = {"run": "", "normal": "", "history": "", "options": ""}

OPTIONS = {
    "level": ("等级", "等级越高，你周围的敌人越多。"),
    "speed": ("敌人速度", "追杀你的敌人的奔跑速度。"),
    "buff": ("增益", "增益：敌人的生命值更高，你受到的伤害更多。增益+：更多。"),
    "duration": ("时间限制", "到时本局会自行停止。无限：直到「停止」。"),
    "max_enemies": ("最大敌人数", "同时追杀你的敌人数量上限。更少：你的电脑负担更轻。"),
    "manage_far": ("管理远处的敌人", "远远落在你身后的敌人会被带回到你身后。目前始终开启：此设置会在之后的版本中调整。"),
    "bar": ("游戏内状态栏", "一局进行时，你的击杀、死亡和时间显示在屏幕左上角。"),
    "bar_size": ("状态栏大小", "它在屏幕上的大小。"),
    "normal_level": ("等级", "游戏中敌人的难度。"),
    "normal_allies": ("敌人结盟", "所有敌人同属一队：它们不再互相攻击。"),
    "normal_fast_dodges": ("加速闪避", "敌人的闪避比游戏原本更快。关：游戏原本的闪避速度。"),
    "normal_speed": ("敌人速度", "降低：敌人的奔跑速度慢 15%，加速闪避也一样。适合觉得它们太快的玩家。"),
    "normal_shields": ("护盾", "没有护盾的敌人会获得一个护盾，相当于其生命值的 40%。护盾一旦耗尽就不会恢复。"),
    "normal_hardcore": ("硬核", "随着你不断击杀，敌人会在整个游戏过程中缓慢变强。"),
    "normal_hardcore_progress": ("进度", "关：已达到的难度保持不变，不再上升。"),
}

# French's keys, then the names French keeps as English and Chinese cannot: the normal mode's levels, as the game names
# a bandit and a predator; the Buff, as the game's 增益; the time limits in minutes.
CHOICES = {"level:25": "等级 1", "level:40": "等级 2", "level:60": "等级 3", "level:80": "等级 4",
           "level:100": "等级 5", "Normal": "普通", "+10%": "+10%", "+20%": "+20%", "+30%": "+30%",
           "+40%": "+40%", "+50%": "+50%", "Unlimited": "无限", "Small": "小", "Medium": "中",
           "Large": "大", "buff:Normal": "普通", "normal_speed:Increased": "提高",
           "normal_speed:Reduced": "降低",
           "Bandit": "匪徒", "Senior": "资深", "Predator": "掠食者", "Buff": "增益", "Buff+": "增益+",
           "10 min": "10 分钟", "20 min": "20 分钟", "30 min": "30 分钟", "45 min": "45 分钟", "60 min": "60 分钟"}
