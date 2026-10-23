"""The COMPANIONS page's words (decision 50 of docs/renforts/README.md, sketch A of docs/renforts/esquisses_menu), in
the window's four languages, English, French, Chinese and Japanese, taken into panel_en, panel_fr, panel_zh and
panel_ja. The Chinese names the game's words as the game's zh-Hans texts do (test_chinese_texts.py): 伙伴 for a
companion, 秘藏猎人 for the Vault Hunters, 护盾, 生命值 and 速度; the Japanese as its ja texts do (panel_ja.py):
コンパニオン, 味方, ヴォルト・ハンター, シールド, ライフ and 速度. A sentence names a button as it shows, in 「」. The
six hunters keep their own names in every language; the allies are named as the game names them
(companions/bars_names.py)."""

EN = {
    "companions": "COMPANIONS", "companions_hunters": "VAULT HUNTERS", "companions_allies": "ALLIES",
    "companions_team": "TEAM {count} / {most}",
    "companions_none": "No companion yet: choose one to add it to the team.",
    "companions_lead": "The Vault Hunters fight with their weapons only, not their skills.",
    "companions_shield": "SHIELD", "companions_speed": "SPEED", "companions_outfit": "OUTFIT",
    "companions_outfit:own": "BASE", "companions_outfit:player": "YOUR COLOURS",
    "companions_speed:Off": "OFF", "companions_speed:+20%": "+20%", "companions_speed:+30%": "+30%",
    "companions_launch": "LAUNCH THE TEAM", "companions_stop": "STOP THE TEAM",
    "companions_locked": "Stop the team to change it.",
    "ready_companions": "Choose a companion to add it to the team, then launch the team.",
    "companions_on": "Your team follows you. Stop it here to change it.",
    "team_full": "The team is full: 8 companions at most.",
    "team_empty": "Add at least one companion first.",
    "team_busy": "Your choices are being saved: launch the team again.",
    "team_off": "It Follows is off: switch it on, then launch the team.",
    "team_already_on": "The team is already on.",
    "team_main_menu": "Load a game first, then launch the team.",
    "team_mismatch": "It Follows and Companions are at versions that do not work together, so no team starts: "
                     "update both, then restart the game.",
    "team_stopped": "The team stopped: they no longer follow you.",
    "team_key_label": "Team key",
    "team_key_hint": "Launches your team, or stops it, while you play. Click the key to change it.",
    "key_taken": "That key is already It Follows' other key: choose another one.",
}

FR = {
    "companions": "COMPAGNONS", "companions_hunters": "CHASSEURS DE L'ARCHE", "companions_allies": "ALLIÉS",
    "companions_team": "ÉQUIPE {count} / {most}",
    "companions_none": "Aucun compagnon pour l'instant : choisis-en un pour l'ajouter à l'équipe.",
    "companions_lead": "Les chasseurs de l'Arche se battent avec leurs armes seulement, sans leurs compétences.",
    "companions_shield": "BOUCLIER", "companions_speed": "VITESSE", "companions_outfit": "TENUE",
    "companions_outfit:own": "DE BASE", "companions_outfit:player": "TES COULEURS",
    "companions_speed:Off": "COUPÉE", "companions_speed:+20%": "+20 %", "companions_speed:+30%": "+30 %",
    "companions_launch": "LANCER L'ÉQUIPE", "companions_stop": "ARRÊTER L'ÉQUIPE",
    "companions_locked": "Arrête l'équipe pour la changer.",
    "ready_companions": "Choisis un compagnon pour l'ajouter à l'équipe, puis lance l'équipe.",
    "companions_on": "Ton équipe te suit. Arrête-la ici pour la changer.",
    "team_full": "L'équipe est complète : 8 compagnons au plus.",
    "team_empty": "Ajoute d'abord au moins un compagnon.",
    "team_busy": "Tes choix sont en cours d'enregistrement : relance l'équipe.",
    "team_off": "It Follows est coupé : active-le, puis lance l'équipe.",
    "team_already_on": "L'équipe est déjà lancée.",
    "team_main_menu": "Charge d'abord une partie, puis lance l'équipe.",
    "team_mismatch": "It Follows et Companions ne sont pas à des versions compatibles, aucune équipe ne part : "
                     "mets les deux à jour, puis relance le jeu.",
    "team_stopped": "L'équipe est arrêtée : ils ne te suivent plus.",
    "team_key_label": "Touche de l'équipe",
    "team_key_hint": "Lance ton équipe, ou l'arrête, pendant que tu joues. Clique sur la touche pour la changer.",
    "key_taken": "Cette touche est déjà l'autre touche d'It Follows : choisis-en une autre.",
}

ZH = {
    "companions": "伙伴", "companions_hunters": "秘藏猎人", "companions_allies": "盟友",
    "companions_team": "队伍 {count} / {most}",
    "companions_none": "还没有伙伴：选择一名伙伴即可加入队伍。",
    "companions_lead": "秘藏猎人只用武器战斗，不使用技能。",
    "companions_shield": "护盾", "companions_speed": "速度", "companions_outfit": "外观",
    "companions_outfit:own": "默认", "companions_outfit:player": "你的配色",
    "companions_speed:Off": "关闭", "companions_speed:+20%": "+20%", "companions_speed:+30%": "+30%",
    "companions_launch": "启动队伍", "companions_stop": "停止队伍",
    "companions_locked": "先停止队伍才能更改。",
    "ready_companions": "选择伙伴加入队伍，然后启动队伍。",
    "companions_on": "你的队伍正在跟随你。在这里停止队伍才能更改。",
    "team_full": "队伍已满：最多8名伙伴。",
    "team_empty": "请先加入至少一名伙伴。",
    "team_busy": "正在保存你的选择：请再次启动队伍。",
    "team_off": "It Follows 已关闭：先开启，再启动队伍。",
    "team_already_on": "队伍已经启动。",
    "team_main_menu": "请先加载一个存档，再启动队伍。",
    "team_mismatch": "It Follows 和 Companions 的版本不兼容，伙伴队伍无法启动：请更新这两个模组，然后重启游戏。",
    "team_stopped": "队伍已停止：伙伴不再跟随你。",
    "team_key_label": "队伍按键",
    "team_key_hint": "游戏中启动或停止你的队伍。选择该按键即可更改。",
    "key_taken": "这个按键已是 It Follows 的另一个按键：请选择其他按键。",
}

JA = {
    "companions": "コンパニオン", "companions_hunters": "ヴォルト・ハンター", "companions_allies": "味方",
    "companions_team": "チーム {count} / {most}",
    "companions_none": "まだコンパニオンがいません：選択するとチームに加わります。",
    "companions_lead": "ヴォルト・ハンターは武器だけで戦い、スキルは使いません。",
    "companions_shield": "シールド", "companions_speed": "速度", "companions_outfit": "外観",
    "companions_outfit:own": "標準", "companions_outfit:player": "自分の色",
    "companions_speed:Off": "オフ", "companions_speed:+20%": "+20%", "companions_speed:+30%": "+30%",
    "companions_launch": "チームを出動", "companions_stop": "チームを停止",
    "companions_locked": "変更するには、チームを停止してください。",
    "ready_companions": "コンパニオンを選択してチームに加え、「チームを出動」を選択してください。",
    "companions_on": "チームがついてきています。変更するには、ここでチームを停止してください。",
    "team_full": "チームは満員です：コンパニオンは最大8人までです。",
    "team_empty": "先にコンパニオンを1人以上加えてください。",
    "team_busy": "選択内容を保存しています：もう一度「チームを出動」を選択してください。",
    "team_off": "It Follows は無効です：有効にしてから、「チームを出動」を選択してください。",
    "team_already_on": "チームはすでに出動しています。",
    "team_main_menu": "先にセーブデータをロードしてから、「チームを出動」を選択してください。",
    "team_mismatch": ("It Follows と Companions のバージョンが合わないため、チームは出動しません：両方を更新してから、"
                      "ゲームを再起動してください。"),
    "team_stopped": "チームを停止しました：コンパニオンはもうついてきません。",
    "team_key_label": "チームのキー",
    "team_key_hint": "プレイ中にチームを出動、または停止します。キーを選択すると変更できます。",
    "key_taken": "このキーは It Follows のもう一方のキーにすでに使われています：別のキーを選んでください。",
}

# The bars' row (companions/bars.py), in French, Chinese and Japanese; its English is the option's own.
OPTIONS_FR = {"companion_bars": ("Barres de vie à l'écran", "La vie de chaque compagnon en bas à gauche de "
                                                           "l'écran, comme celle d'un coéquipier en coop.")}
OPTIONS_ZH = {"companion_bars": ("屏幕生命值条", "在屏幕左下角显示每名伙伴的生命值，就像合作模式中的队友。")}
OPTIONS_JA = {"companion_bars": ("ライフ・バー", "各コンパニオンのライフを、協力プレイのチームメイトのように"
                                                     "画面の左下に表示します。")}
