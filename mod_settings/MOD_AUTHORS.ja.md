# Mod Settings：MOD作者向けガイド

Mod Settingsは、『ボーダーランズ4』のポーズメニューとメインメニューにMODS項目を追加します。この項目では、ゲームの「オプション」画面の部品を使って、Python SDKのすべてのMODのオプションを表示・設定できます。

このガイドでは、MODがMODSにどう表示されるか、そしてオプションがきちんと表示されるようにどう書けばよいかを説明します。

## 概要

- **インストール、インポート、呼び出しが必要なものは何もありません**。MODSは、SDKのコンソールのMODメニューとまったく同じように、MODが `mods_base` に宣言したものを読み取ります。
- **MODはMod Settingsに依存しません**。Mod Settingsがなくても同じように動きます。インストールされているかどうかを調べようとしないでください。
- **コンソールに表示されるものは、MODSにも表示されます**（後述の制限の範囲内で）。

## MODSに表示される内容

- **MODの一覧**：SDKのすべてのMODが、コンソールのメニューと同じ順番で並びます。
- **MODのページ**：MODの名前、オプション、説明パネル。「General」タブで、プレイヤーがどのオプションにもカーソルを合わせていないとき、このパネルにはMODの説明、続いてバージョンと作者が表示されます。
- **「Enabled」スイッチ**：MODを有効・無効にできる場合、「General」タブの先頭に表示されます。
- **「No settings」**：MODに表示できるオプションが一つもなく、有効・無効も切り替えられない場合に表示されます。空のタブにも表示されます。

<img src="site/images/mods-list.jpg" width="1600" height="840" alt="MODSのMOD一覧。各MODに「OPEN」ボタンがあり、右に選んだMODの説明が表示されている">

名前、説明、バージョン、作者は `Mod` オブジェクトのもので、`build_mod()` が `pyproject.toml` またはモジュールから設定します。

## オプションの種類

| SDKのオプション | MODSでの表示 | MODSが読み取るもの |
|---|---|---|
| `BoolOption` | スイッチ | `true_text` と `false_text` を2つの位置のテキストとして使用 |
| `SliderOption` | スライダー | `min_value`、`max_value`、`step`、`is_integer`。小数点以下の桁数は刻み幅に合わせ、最大3桁（刻み幅が0.0005より小さいと小数なし）。`is_integer` では小数なしで、`is_integer` のデフォルトは `True`。小数のあるスライダーには `is_integer=False` を渡す |
| `SpinnerOption` | 矢印で切り替える項目 | `choices`。`wrap_enabled` は読み取らない |
| `DropdownOption` | ドロップダウンリスト | `choices` |
| `KeybindOption` | キー | プレイヤーがクリックしてから新しいキーを押す。Escでキャンセル。受け付けるのは、英字、数字、F1〜F12、矢印キー、制御キー、テンキー、マウスの右・中央・サイドボタンだけで、10秒間キーが押されないとキャプチャーは止まる。`is_rebindable=False` では、キーは表示されるが変更できない |
| `ButtonOption` | ボタン | `on_press` |
| `GroupedOption` | オプションの上のセクション見出し | `display_name` |
| `NestedOption` | タブ、サブタブ、またはページ | 「オプションを整理する」を参照 |

<img src="site/images/option-types.jpg" width="1116" height="452" alt="MODSのスライダー、スイッチ、キー">

これらの型のサブクラスは、元の型と同じように表示されます。ほかのクラスのオプションは表示されず、非表示のオプション（`is_hidden=True`、`HiddenOption` を含む）も表示されません。

## オプションを整理する

MODSは、すべてのMODに同じ規則で、MODのページをタブに整理します：

1. どの `NestedOption` にも入っていないオプションは、**「General」タブ**に入ります。
2. 最上位の各 `NestedOption` は、`display_name` を名前とする**タブ**になります。
3. タブの中では、各 `NestedOption` が**サブタブ**になります。そのタブのほかのオプションは「General」サブタブに入ります。
4. それより深い `NestedOption` は**「OPEN」の行**になり、同じ方法で整理された画面を開きます。4階層を超えると表示されません。
5. `GroupedOption` は、そのオプションの上に**セクション見出し**を付けます。すぐ後に別の見出しが続く見出しは表示されません。入れ子のグループは平らに並べられるため、内側のグループの後に置いたオプションは、その内側のグループの見出しの下に表示されます。ページだけを含むグループには見出しが表示されません。ただし、グループ外のオプションが後に続く場合は、その見出しがそのオプションの上に表示されます。

<img src="site/images/tabs.jpg" width="1200" height="112" alt="MODSのMODのタブバー">

SDKは自動的に、オプションを「Options」グループに、キー（`@keybind`）を「Keybinds」グループにまとめます（`Mod.iter_display_options`）。そのため、デフォルトでは「General」タブに「Options」の見出しが表示され、MODにキーがあれば「Keybinds」も表示されます。最初のオプションがグループの場合、「Options」は表示されません（規則5）。MODが `iter_display_options` を再定義している場合、MODSはコンソールと同じく、その結果に従います。

例：

```python
options=[
    BoolOption(...),                                        # General tab
    NestedOption("combat", [...], display_name="Combat"),   # "Combat" tab
    NestedOption("movement", [                              # "Movement" tab
        SliderOption(...),                                  #   its General sub-tab
        NestedOption("dash", [...], display_name="Dash"),   #   "Dash" sub-tab
    ], display_name="Movement"),
]
```

**オプションは `build_mod(options=[...])` に渡してください**。この引数がないと、`build_mod()` はモジュールのオプションを変わりうる順番で集め、`GroupedOption` と `NestedOption` を無視します。各 `NestedOption` には `display_name` も付けてください。付けないと、タブには識別子がそのまま表示されます（「combat」）。

## 説明パネル

- プレイヤーがオプションにカーソルを合わせると、パネルにはその `description_title`（デフォルトは `display_name`）と `description` が表示されます。
- SDKは説明のHTMLをテキストに変換します。`<br>` は改行になります。MODSはそれをテキストとして表示し、連続する空行を1つにまとめます。
- 何にもカーソルを合わせていないときは、「General」タブではMODの説明が表示されます。ほかのタブやサブタブでは、その `NestedOption` の説明が表示され、説明がなければ何も表示されません。

## 変更がMODに届くとき

- MODSは、コンソールと同じく、ゲームのスレッドで `option.value = new_value` を書き込みます。するとSDKが `on_change_anytime` を呼び、MODが有効なら続いて `on_change_while_enabled` を呼びます。
- **これらの関数は、値が変わる前に呼ばれます**。新しい値は引数 `value` から読んでください。`option.value` にはまだ古い値が入っています。
- **ドラッグ中のスライダーは、100ミリ秒に1回まで値を送ります**。常に最新の値です。そのため関数は1秒間に10回呼ばれることがあります。ファイルの書き込みや重い検索はせず、軽く保ってください。
- ボタンは、これもゲームのスレッドで `on_press(option)` を呼びます。
- 「Enabled」スイッチは、コンソールと同じく `mod.enable()` または `mod.disable()` を呼びます。
- 保存はSDKの `mod.save_settings()` で行われます。変更の直後、スライダーの場合はMODSを閉じたとき、または次にほかの設定を変えたときです。ボタンは何も保存しません。

## 制限

| 対象 | 上限 | 超えた場合 |
|---|---|---|
| MOD | 64 | それ以降は表示されない |
| 行（すべてのMODの合計） | 3,000 | それ以降は表示されない |
| 1ページの行 | 100 | それ以降は表示されない |
| ページの階層 | 4 | それより深いページは表示されない |
| オプションまたは選択肢の名前 | 80文字 | 切り詰められる |
| 説明 | 600文字 | 切り詰められる |
| リストまたは矢印で切り替える項目の選択肢 | 64 | オプション全体が表示されない |

行とは、オプションのほか、セクション見出し、タブ、「Enabled」スイッチのことです。最上位では、100行に「General」タブとタブがまとめて含まれます。切り詰められた見出しやタブは、その中身ごと表示されません。

以下も表示されません：
- 選択肢がない、または選択肢のどれかがテキストでないリスト。
- 最小値が最大値より小さくない、または最小値・最大値・刻み幅・値のどれかがNaNか無限大のスライダー。
- 名前が1〜32文字の英字または数字でできていないキー。たとえばコントローラーのキーです。`MODEL_BUILT` の行はこれを数えません。

オプションを列挙する関数が失敗した場合、またはスライダーの値がそもそも数値でない場合（`None`、テキスト）、MODSはそれより前の内容を表示し、MODを `failed_mods` に数えます。

## 言語

MODSのテキストはゲームの言語に合わせて、英語、フランス語、簡体字中国語で表示され、それ以外の言語（日本語を含む）では英語で表示されます。オプションの名前と説明は、MODが付けたとおりに表示されます。MODSはそれを翻訳しません。

## アドバイス

- オプションは、表示したい順番で `build_mod(options=[...])` に渡してください。
- 名前は短くし、各オプションに説明を付けてください。プレイヤーがパネルで読むのはその説明です。
- 関連するオプションは `GroupedOption` でまとめ、話題ごとに `NestedOption` で分けてください。2階層あれば、すべてをタブとサブタブに収められます。
- `on_change` 関数は軽く保ち、新しい値は引数から読んでください。
- MODの内部的な値は、`is_hidden=True` または `HiddenOption` で隠してください。

## MODを確認する

1. Mod Settingsをインストールします。2つのファイル、`mod_settings.sdkmod` と `mod-settings_999_P.pak` が必要です（[README](README.ja.md)を参照）。
2. ゲームを起動し、ポーズメニューを開き、MODSを選び、自分のMODを選びます。
3. SDKのコンソールのMODメニューと比べます。同じオプションがあるはずです。
4. 何か足りない場合は、`unrealsdk.log` で `[ModSettings] MODEL_BUILT` の行を探します。この行はすべてのMODの合計を示し、どのMODかは示しません：`unsupported`（不明な型、無効な値、または64個を超える選択肢）、`truncated`（制限で切り詰められた行、タブ、MOD。1回の切り詰めを1と数える）、`failed_mods`（オプションの列挙に失敗したMODの数）。非表示のオプションは数えません。

## 完全な例

```python
from mods_base import (BoolOption, ButtonOption, GroupedOption, NestedOption, SliderOption, SpinnerOption,
                       build_mod)


def on_speed(option: SliderOption, value: float) -> None:
    # value is the new value: option.value still holds the old one here.
    ...


speed = SliderOption("speed", 100, 50, 300, step=10, display_name="Speed",
                     description="Movement speed, in percent.", on_change_anytime=on_speed)
enabled_in_air = BoolOption("in_air", True, display_name="In the air",
                            description="Also works while jumping or falling.")
quality = SpinnerOption("quality", "Medium", ["Low", "Medium", "High"], display_name="Quality",
                        description="Visual quality of the effect.")
reset = ButtonOption("reset", display_name="Reset", description="Puts every setting back to its default.",
                     on_press=lambda _option: ...)

build_mod(options=[
    GroupedOption("main", [speed, enabled_in_air], display_name="Movement"),  # General tab, "Movement" section
    NestedOption("effects", [quality, reset], display_name="Effects",          # "Effects" tab
                 description="How the effect looks."),
])
```
