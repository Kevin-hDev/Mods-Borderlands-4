"""It Follows' window in Japanese, its fourth language, translated from the English one.

Every game word is the Japanese game's own, read in its .locres (Steam build 1.10.2, 2026-10-23), counted over the
game's rows: Vault Hunter ヴォルト・ハンター (1664 rows), enemy 敵 (1397; Enemies 敵), kill キル as a count (Kill
キル, 4) and 倒す in a sentence (Kill enemies 敵を倒す, 倒し 378 rows; 撃破 4), death 死亡 (34; You will respawn from
here when killed 死亡すると), shield シールド (16) and its recharge リチャージ (15; Shield Recharge Delay
シールド・リチャージ・ディレイ), health ライフ (377; ヘルス 2, 体力 9) and health bars ライフ・バー, dodge 回避 (36),
companion コンパニオン (Companion Damage コンパニオンのダメージ, 9), ally 味方 (75; An ally! 味方だ), level レベル (7)
and difficulty 難易度 (17), zone エリア (76; ゾーン only in names), pause 一時停止 (77; PAUSED 一時停止中, ポーズ 4),
weapon 武器, ammo 弾薬, speed 速度 (4; スピード 2), tough タフ, on foot 徒歩 (Only On Foot 徒歩のみ), vehicle
ビークル (64) and Exit Vehicle 降りる, graphics グラフィック, Main Menu メイン・メニュー, load ロード (823) and save
data セーブデータ (9; セーブ 35), solo ソロ (Solo campaign ソロ・ストーリー), co-op 協力プレイ (local co-op
ローカル協力プレイ), Normal ノーマル (4; 普通 4, 法線 8 the editor's), Buff バフ, Unlimited 無制限, Progress 進行
(Progress 進行状況), Hardcore Mode ハードコア・モード (5 of 5 rows), the game's name 『ボーダーランズ®4』 (18),
Bandit バンディット (18), Predator 捕食者 (16; プレデター 0), Veteran ベテラン (Senior's nearest; Senior is 老 in
monsters' names), God 神 (God's Punishment 神の裁き; ゴッド only in names), Lost Loot 未回収戦利品 (8 of 8 rows) and its
machine 未回収戦利品マシン, items アイテム, Resolution 解像度, Fullscreen 全画面表示, Display Mode ディスプレイモード,
Open World オープンワールド, the starting point 開始地点 (Group at the starting point 開始地点に集合する), Start 開始
(10), Stop 停止 (31), Back 戻る, Next 次へ, Preview プレビュー, Select 選択 (18), Ready 準備完了, Increased 上昇 and
Reduced 低下, ammo, cash and experience 弾薬, 現金, 経験値, beta ベータ (Beta preview ベータ プレビュー), Options
オプション (35), History 履歴 (7) (read 2026-10-23). The window words shared with the other mods (有効, 無効, オン,
オフ, 外観, デフォルト, プロファイル) are Apex Grapple's and Apex Movement's.
The game has no word for a horde (ホード 0 rows; 大群 4, a swarm in dialogue): the mod's horde is ホード, short
enough for the bar in the game. Nor for a run: ラン, which keeps a run apart from ゲーム, the save the player plays.
Nor for a stagger: ひるみ. Those three are the translators' choice (2026-10-23), not read in the game. The mod's name
stays in Latin letters, as the other mods keep theirs. Buttons and rows named in a sentence are quoted 「…」, as they
show; a controller player selects, never clicks (選択).
"""

from .panel_common_ja import TEXT as COMMON
from .panel_companion_texts import JA as COMPANIONS, OPTIONS_JA

TEXT = {
    **COMMON,
    **COMPANIONS,
    "run": "ホード・モード【ベータ版】", "normal": "ノーマル・モード", "history": "履歴", "options": "オプション",
    "running_tag": "進行中",
    "run_settings": "ランの設定", "run_live": "ラン進行中 · {level}",
    "kills": "キル", "deaths": "死亡", "time": "時間", "start": "開始", "stop": "停止",
    "caution": ("数十体、選んだレベルによっては百体を超える敵が、同時に追ってきます：このモードはPCに大きな負荷を"
                "かけます。ゲームが重くなったら、「最大敵数」を下げる、低いレベルを選ぶ、ゲームのグラフィック設定を"
                "下げる、バックグラウンドのアプリを閉じる、などを試してください。"),
    "locked": "これらの設定を変更するには、ランを停止してください。",
    "help_run_title": "ランの流れ",
    "help_run": ("ランは静かに始まります：近くの敵が追いかけてきます。\n\n"
                 "ランの開始時に近くに敵がいない場合は、敵を探しに行ってください：そうしないと何も起きません。\n\n"
                 "敵を倒すほど、敵の数は増えていきます。\n\n"
                 "敵を100体倒すごとに、敵は1%強くなります：これがバーの「ハードコア」の割合で、ランごとに0に"
                 "戻ります。\n\n"
                 "追ってくる敵の種類は、プレイしているエリアと、通り抜けるエリアによって決まります。\n\n"
                 "敵の種類を変えたい時は、マップのあちこちへ移動してください。"),
    "ready_run": "準備完了：「開始」を選択すると、メニューが閉じてランが始まります。",
    "paused_run": "このメニューを開いている間、ゲームは一時停止します。",
    "ready_history": "直近20回のラン。ゲームを再起動しても残ります。",
    "ready_options": "変更は自動で保存されます。",
    "start_busy": "設定を保存しています：もう一度「開始」を選択してください。",
    "start_off": "It Follows は無効です：有効にしてから、「開始」を選択してください。",
    "start_in_vehicle": "ビークルに乗ったままではランを開始できません：降りてから、「開始」を選択してください。",
    "start_no_character": "ここではランを開始できません：先にセーブデータをロードしてください。",
    "start_coop": "ホード・モードは現在、ソロプレイでのみ使えます。ゲームには何も変更を加えていません。",
    "start_already_running": "すでにランが進行中です。",
    "start_normal_on": "先にノーマル・モードを停止してから、「開始」を選択してください。",
    "run_blocked": "ノーマル・モードが進行中です：ランを開始するには、「ノーマル・モード」のページで停止してください。",
    "normal_settings": "ノーマル・モード", "normal_lead": "ゲームの敵を作り直す最初の一歩で、今も改良を続けています。",
    "normal_live": "ノーマル・モード進行中 · {level}",
    "normal_playing": "プレイ中は敵が強化されます。「停止」を選択すると、敵はゲーム本来の状態に戻ります。",
    "normal_waiting": "ゲームをロードし、徒歩の状態になるとすぐに始まります。",
    "normal_locked": "これらの設定を変更するには、ノーマル・モードを停止してください。",
    "normal_blocked": "ホード・モードのランが進行中です：ノーマル・モードを開始するには、先にランを停止してください。",
    "normal_level:Bandit": ("敵が増え、少し速く、少しタフになります。回避が速くなり、より遠くまで追ってきます。"
                            "シールドのない敵にシールドを付けるかどうかは、お好みで選べます。"),
    "normal_level:Senior": ("敵がさらに増え、より速く、よりタフになります。回避はより素早く、追跡はより長くなります。"
                            "シールドのない敵すべてにシールドが付きます。"),
    "normal_level:Predator": ("敵がさらに増え、とても速く、とてもタフになります。回避は電光石火で、はるかに遠くまで"
                              "追ってきます。シールドのない敵すべてにシールドが付き、破壊されても10秒後に"
                              "リチャージされます。"),
    "normal_level:God": ("敵は捕食者と同じ数で、はるかにタフですが、少し遅くなります。シールドのない敵すべてに"
                         "シールドが付き、破壊されても10秒後にリチャージされます。弾薬、現金、経験値が増えます。"
                         "コンパニオンと一緒に遊ぶためのレベルです。"),
    "hardcore_settings": "ハードコア", "hardcore_lead": "ゲーム全体を通して、ゆっくりと上がっていく難易度。",
    "hardcore_badge": "ハードコア {percent}%", "hardcore_badge_paused": "ハードコア {percent}%\n一時停止中",
    "help_hardcore_title": "ハードコア・モード",
    "help_hardcore": ("『ボーダーランズ4』では、敵のレベルがヴォルト・ハンターのレベルに合わせて上がります：ゲームが"
                      "本当に難しくなることはなく、むしろずっと簡単なままです。\n\n"
                      "ハードコア・モードはそれを変えます。有効にした時点では何も変わりません。その後は敵を100体倒す"
                      "ごとに、ゲーム全体を通して敵が1%ずつ、ゆっくりと着実に強くなります。これは選んだレベルに"
                      "上乗せされます。\n\n"
                      "このハードコアは、ノーマル・モードの進行中にのみ働きます：ホード・モードには専用のハードコアが"
                      "あり、ランごとに最初からやり直しになります。到達した割合はメニューの左側に表示されます。\n\n"
                      "自分に合った難易度を保つために進行を一時停止したり、いつでもこのモードを無効にしたりできます："
                      "進行状況は保持され、再び有効にすると元どおりになります。"),
    "ready_normal": "準備完了：「開始」を選択すると、メニューが閉じてノーマル・モードが始まります。",
    "normal_waiting_notice": "ノーマル・モードが進行中です：ゲームをロードし、徒歩の状態になるとすぐに始まります。",
    "start_horde_running": "先にホード・モードのランを停止してから、「開始」を選択してください。",
    "start_already_on": "ノーマル・モードはすでに進行中です。",
    "normal_start_failed": ("ノーマル・モードを開始できませんでした。ゲームには何も変更を加えていません。"
                            "原因は unrealsdk.log に記録されています。"),
    "normal_stop_unsaved": ("ノーマル・モードは停止しましたが、この変更を保存できませんでした：次回の起動時に再び"
                            "有効になる場合があります。"),
    "start_failed": ("ランを開始できませんでした。原因は unrealsdk.log に記録されています。敵の様子がおかしい場合は、"
                     "メイン・メニューに戻ってから、セーブデータをもう一度ロードしてください。"),
    "start_refused": ("ここではランを開始できませんでした。ゲームには何も変更を加えていません。原因は unrealsdk.log に"
                      "記録されています。"),
    "start_place_caption": "場所", "start_map_caption": "マップ上の位置",
    "start_choose": "選択", "start_chosen": "選択済み", "start_back": "戻る",
    "colour_preview": "プレビュー", "colour_back": "戻る",
    "help_start_title": "開始地点",
    "help_start": ("ホード・モードのランをどこから始めるかを選びます。\n\n"
                   "「開始地点」をオンにしてから、「ランの設定」の横にある場所のタブを開きます：その場所の画像と、"
                   "マップ上の位置が表示されます。「選択」を押してください。\n\n"
                   "「開始」を選択すると、移動して場所がロードされる間は画面が暗くなり、画面が戻るとすぐにランが"
                   "始まります。\n\n"
                   "オフの時は、これまでどおり今いる場所からランが始まります。最後に選んだ場所は保持されます。"),
    "locked_trip": "開始地点へ移動中です：到着するとランが始まります。",
    "start_not_open_world": "ここからは開始地点を使えません：オープンワールドに戻ってから、「開始」を選択してください。",
    "start_trip_going": "すでに開始地点へ移動中です。",
    "start_move_failed": ("ゲームが移動を受け付けませんでした：位置は変わっておらず、ランは始まっていません。もう一度"
                          "「開始」を選択してください。"),
    "start_no_floor": ("開始地点のロードが間に合いませんでした：元の場所に戻され、ランは始まっていません。もう一度"
                       "「開始」を選択してください。"),
    "start_character_gone": "移動が途中で止まりました（マップの切り替え）：ランは始まっていません。",
    "start_hold_failed": ("エラーにより移動が止まりました：元の場所に戻され、ランは始まっていません。原因は"
                          " unrealsdk.log に記録されています。"),
    "start_arrival_coop": ("移動中に誰かがゲームに参加しました：ホード・モードは現在ソロプレイでのみ使えるため、ランは"
                           "始まっていません。開始地点にとどまります。"),
    "start_arrival_refused": ("開始地点に着きましたが、そこではランを開始できませんでした。もう一度「開始」を選択"
                              "してください。原因は unrealsdk.log に記録されています。"),
    "history_title": "直近20回のラン", "history_empty": "まだランの記録はありません：ランを行うと、ここに表示されます。",
    "col_when": "開始日時", "col_level": "レベル", "col_limit": "制限時間", "col_held": "耐えた時間", "col_kills": "キル",
    "col_deaths": "死亡", "col_end": "終了理由",
    "clock_time": "{hour:02d}:{minute:02d}", "today": "今日 {time}", "yesterday": "昨日 {time}",
    "day": "{month}{day}日 {time}", "months": "1月 2月 3月 4月 5月 6月 7月 8月 9月 10月 11月 12月",
    "end:time_up": "時間切れ", "end:stopped": "停止", "end:left_game": "ゲームから退出", "end:mod_disabled": "MOD無効",
    "end:interrupted": "自動停止",
    "level_number": "レベル{number}",
    "result:time_up": "時間切れ", "result:stopped": "ラン停止", "result:interrupted": "ラン自動停止",
    "result_sentence:time_up": "{level}で{held}耐えました。敵はもう来ません。",
    "result_sentence:stopped": "{level}で{held}耐えました。敵はもう来ません。",
    "result_sentence:interrupted": ("{level}で{held}経過後、ランが自動で停止しました：敵はもう来ません。ゲームには"
                                    "何も変更を加えていません。原因は unrealsdk.log に記録されています。"),
    "key_label": "メニューのキー", "press_key": "キーを押してください",
    "key_hint": "ゲーム中にこのメニューを開きます。開いている間、ゲームは一時停止します。キーを選択すると変更できます。",
    "welcome_title": "IT FOLLOWS へようこそ",
    "welcome_lead": ("It Follows には、互いに独立した2つのモードがあります。ホード・モード：「開始」を選択すると、周りの"
                     "すべての敵が向かってきて、どこまでも追いかけてきます。途中で出会った敵はホードに加わり、倒した"
                     "敵は戻ってきます。できるだけ長く耐え抜いてください。"),
    "welcome_film_title": "映画『イット・フォローズ』",
    "welcome_film": "何かがこちらへ歩いてきます。どこへ行こうと、決して止まりません。",
    "welcome_zombies_title": "『コール オブ デューティ ブラックオプス』ゾンビモード",
    "welcome_zombies": "終わりなく戻ってきて、レベルとともに膨れ上がるホード。倒して、走って、生き延びます。",
    "welcome_next": "次へ",
    "updates_title": "アップデート {version}",
    "updates_count": "{page} / {pages} ページ",
    "updates_next": "次へ",
    "welcome_normal_lead": ("ノーマル・モード：いつもどおりにゲームをプレイします。出会う敵はより多く、より速く、より"
                            "タフになり、回避も速く、より遠くまで追ってきます。主にゲームを最初から始める、または"
                            "やり直すためのモードで、4段階の周回プレイ（NG+）のようなものですが、ゲームの途中からでも"
                            "使えます。"),
    "welcome_levels_title": "4つのレベル",
    "welcome_levels": "バンディット、ベテラン、捕食者、神。より難しいゲームから、はるかに難しいゲームまで。",
    "welcome_evolving_title": "改良を継続中",
    "welcome_evolving": "ゲームの敵を作り直す最初の一歩で、バージョンを重ねるごとに改良を続けていきます。",
    "welcome_go": "始めよう",
}

GROUPS = {"run": "", "normal": "", "companions": "", "history": "", "options": ""}

OPTIONS = {
    **OPTIONS_JA,
    "start_point": ("開始地点", "今いる場所ではなく、上のタブで選んだマップ上の場所からランを開始します。"),
    "level": ("レベル", "レベルが高いほど、周りの敵が増えます。"),
    "speed": ("敵の速度", "追ってくる敵の走る速さ。"),
    "buff": ("バフ", "バフ：敵のライフが増え、受けるダメージも増えます。バフ+：さらに増えます。"),
    "duration": ("制限時間", "時間になるとランは自動で停止します。無制限：「停止」を選択するまで続きます。"),
    "max_enemies": ("最大敵数", "同時に追ってくる敵の上限。少ないほど、PCの負荷が軽くなります。"),
    "manage_far": ("遠くの敵を管理", "遠く後ろに取り残された敵を、すぐ後ろに連れ戻します。現在は常に有効です：この設定は"
                                     "今後のバージョンで見直されます。"),
    "bar": ("ゲーム内バー", "ランの間、キル数、死亡数、時間を画面の左上に表示します。"),
    "bar_size": ("バーのサイズ", "画面上での大きさ。"),
    "lost_loot": ("未回収戦利品：400個", "未回収戦利品マシンが、ゲームの上限を超えて最大400個のアイテムを保管します。"
                                         "オフ：マシン内のアイテムはそのまま残ります。"),
    "stretch_1610": ("解像度 16：10", "全画面表示で、画面の高さに合わせた16：10の解像度でプレイします（1440pの画面では"
                                       "2304×1440）。16：9の画面では映像が引き伸ばされます。オフ：元の解像度と"
                                       "ディスプレイモードに戻ります。"),
    "saturated_colours": ("カラープロファイル", "ゲーム全体の色がより鮮やかになります。"),
    "normal_level": ("レベル", "ゲームの敵に与える難易度。"),
    "normal_allies": ("敵同士の同盟", "すべての敵が同じチームになり、敵同士で戦わなくなります。"),
    "normal_fast_dodges": ("回避の高速化", "敵がゲーム本来より速く回避します。オフ：ゲーム本来の回避速度。"),
    "normal_speed": ("敵の速度", "低下：ベテラン、捕食者、神では、敵の走る速さ、回避、攻撃が遅くなります。"),
    "normal_shields": ("シールド", "シールドのない敵に、ライフの40%のシールドが付きます。一度破壊されると戻りません。"),
    "normal_no_staggers": ("ひるみなし", "捕食者と神では、撃たれても敵がひるまず、転倒もしなくなります。"),
    "normal_hardcore": ("ハードコア", "敵を倒すにつれて、ゲーム全体を通して敵がゆっくりと強くなります。"),
    "normal_hardcore_progress": ("進行", "オフ：到達した難易度はそのまま保たれ、上がりません。"),
}

# French's keys, then the names French keeps as English: the normal mode's levels, as the game names a bandit, a
# veteran and a predator; the Buff, as the game's バフ; the time limits in minutes.
CHOICES = {"level:25": "レベル1", "level:40": "レベル2", "level:60": "レベル3", "level:80": "レベル4",
           "level:100": "レベル5", "Normal": "ノーマル", "+10%": "+10%", "+20%": "+20%", "+30%": "+30%",
           "+40%": "+40%", "+50%": "+50%", "Unlimited": "無制限", "Small": "小", "Medium": "中",
           "Large": "大", "buff:Normal": "ノーマル", "normal_speed:Increased": "上昇",
           "normal_speed:Reduced": "低下",
           "Bandit": "バンディット", "Senior": "ベテラン", "Predator": "捕食者", "God": "神", "Buff": "バフ",
           "Buff+": "バフ+",
           "10 min": "10分", "20 min": "20分", "30 min": "30分", "45 min": "45分", "60 min": "60分",
           "colour_profile:Profile 1": "プロファイル1", "colour_profile:Profile 2": "プロファイル2",
           "colour_profile:Profile 3": "プロファイル3"}
