"""Companions' window in Japanese, translated from the English one. The game's words as the Japanese game's .locres
names them (Steam build 1.10.2, read 2026-10-23; most counted in It Follows' panel_ja.py): ヴォルト・ハンター for the
Vault Hunters, コンパニオン for a companion, 味方 for the allies, ライフ for health, シールド and its recharge リチャージ,
速度, スキル (Skills), 死亡, 一時停止 for a pause, ロード of セーブデータ for a game loaded, 協力プレイ for co-op,
オプション, and なし for Never (7 of 7 rows) and None (132). The cards', the team's and the keys' words are It Follows'
own Japanese for the same things (its panel_companion_texts.py): チーム, チームを出動, 外観, the bars' row. A sentence
names a button as it shows, in 「」; a controller player selects, never clicks (選択)."""

from .panel_common_ja import TEXT as COMMON

TEXT = {
    **COMMON,
    "hunters": "ヴォルト・ハンター", "allies": "味方", "team_settings": "チームの設定", "options": "オプション",
    "team_count": "チーム {count} / {most}",
    "team_none": "まだコンパニオンがいません：選択するとチームに加わります。",
    "outfit": "外観", "outfit:own": "標準", "outfit:player": "自分の色",
    "team_launch": "チームを出動", "team_stop": "チームを停止",
    "cards_locked": "変更するには、チームを停止してください。",
    "settings_locked": "設定を変更するには、チームを停止してください：チームは出動した時の設定を保ちます。",
    "team_elsewhere": "It Follows がコンパニオンを管理しています。It Follows のメニューから操作してください。",
    "team_outdated": ("お使いの It Follows は古すぎるため、無効にしていてもコンパニオンを共有できません：It Follows を"
                      "更新してから、ゲームを再起動してください。"),
    "team_mismatch": ("It Follows と Companions のバージョンが合わないため、チームは出動しません：両方を更新してから、"
                      "ゲームを再起動してください。"),
    "ready_cards": "コンパニオンを選択してチームに加え、「チームを出動」を選択してください。",
    "team_on_notice": "チームがついてきています。変更するには、ここでチームを停止してください。",
    "ready_settings": "チームの設定は、すべてのコンパニオンに適用されます。",
    "team_full": "チームは満員です：コンパニオンは最大{most}人までです。",
    "team_empty": "先にコンパニオンを1人以上加えてください。",
    "team_busy": "選択内容を保存しています：もう一度「チームを出動」を選択してください。",
    "team_off": "Companions は無効です：左下で有効にしてから、「チームを出動」を選択してください。",
    "team_not_started": "チームは出動しませんでした。原因は unrealsdk.log に記録されています。",
    "team_already_on": "チームはすでに出動しています。",
    "team_main_menu": "先にセーブデータをロードしてから、「チームを出動」を選択してください。",
    "team_stopped": "チームを停止しました：コンパニオンはもうついてきません。",
    "key_label": "メニューのキー", "press_key": "キーを押してください", "no_key": "なし",
    "key_hint": ("ゲーム中にこのメニューを開きます。開いている間、ゲームは一時停止します（協力プレイ中は除く）。"
                 "この欄を選択するとキーを設定できます。"),
    "team_key_label": "チームのキー",
    "team_key_hint": "プレイ中にチームを出動、または停止します。キーを選択すると変更できます。",
    "key_taken": "このキーは Companions のもう一方のキーにすでに使われています：別のキーを選んでください。",
    "value_times": "×{value}", "value_percent": "{value}%", "value_bonus": "+{value}%", "value_seconds": "{value}秒",
    "value_never": "なし",
}

GROUPS = {"hunters": "ヴォルト・ハンターは武器だけで戦い、スキルは使いません。", "allies": "",
          "settings": "すべてのコンパニオンに共通の設定です。"}

OPTIONS = {
    "health_times": ("ライフ", "プレイヤーのヴォルト・ハンターのライフに対する倍率。"),
    "shield_percent": ("シールド", "コンパニオンのライフに対する割合。0%：シールドなし。"),
    "shield_refill_s": ("シールド・リチャージ", "破壊されたシールドがリチャージされるまでの時間。"),
    "speed_percent": ("速度", "コンパニオン本来の速度に上乗せされます。"),
    "back_after_s": ("死亡後の復帰", "死亡したコンパニオンは、この時間が経つとプレイヤーのそばに戻ってきます。"),
    "companion_bars": ("ライフ・バー", "各コンパニオンのライフを、協力プレイのチームメイトのように"
                                             "画面の左下に表示します。"),
}
