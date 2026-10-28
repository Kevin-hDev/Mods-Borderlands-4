# Mod Settings：模组作者指南

[English](MOD_AUTHORS.md) · [Français](MOD_AUTHORS.fr.md) · [日本語](MOD_AUTHORS.ja.md)

Mod Settings 在《无主之地 4》的暂停菜单和主菜单中加入「模组」（MODS）入口。它使用游戏「选项」界面的组件，显示并修改 Python SDK 所有模组的选项。

本指南说明你的模组如何出现在「模组」中，以及如何编写选项，让它们正确显示。

## 简介

- **你无需安装、导入或调用任何东西**。「模组」读取你的模组向 `mods_base` 声明的内容，与 SDK 控制台的模组菜单完全相同。
- **你的模组不依赖 Mod Settings**。没有它，你的模组照常运行。不要检查它是否已安装。
- **在控制台中显示的内容，在「模组」中也会显示**，但受下文所列限制约束。

## 「模组」显示你的模组的哪些内容

- **模组列表**：SDK 的所有模组，顺序与控制台菜单相同。
- **你的模组页面**：模组名称、选项，以及一个说明面板。在「通用」标签页中，玩家未选中任何选项时，该面板显示模组的说明，然后是版本和作者。
- **「已启用」开关**，位于「通用」标签页顶部，前提是你的模组可以开启和关闭。
- 「**无设置**」：当你的模组没有任何可见选项、也无法开启和关闭时显示；任何空的标签页中也会显示。

<img src="site/images/mods-list.jpg" width="1600" height="840" alt="「模组」中的模组列表，每个模组都有「打开」按钮，右侧是所选模组的说明">

名称、说明、版本和作者来自你的 `Mod` 对象，由 `build_mod()` 根据你的 `pyproject.toml` 或模块填写。

## 选项类型

| SDK 选项 | 在「模组」中 | 「模组」读取的内容 |
|---|---|---|
| `BoolOption` | 开关 | `true_text` 和 `false_text`，作为两种状态的文字 |
| `SliderOption` | 滑块 | `min_value`、`max_value`、`step`、`is_integer`；小数位数与步长的小数位数相同，最多 3 位（步长小于 0.0005 时没有小数）；`is_integer` 时没有小数，而它默认为 `True`：要使用带小数的滑块，请传入 `is_integer=False` |
| `SpinnerOption` | 左右箭头选择 | `choices`；不读取 `wrap_enabled` |
| `DropdownOption` | 下拉列表 | `choices` |
| `KeybindOption` | 按键 | 玩家点击后按下新按键；按 Esc 取消。只接受字母、数字、F1 到 F12、方向键、控制键、数字小键盘，以及鼠标右键、中键和侧键；10 秒内没有按键时，捕获会停止。`is_rebindable=False` 时，按键会显示但无法更改 |
| `ButtonOption` | 按钮 | `on_press` |
| `GroupedOption` | 显示在其选项上方的分区标题 | `display_name` |
| `NestedOption` | 标签页、子标签页或页面 | 见「整理你的选项」 |

<img src="site/images/option-types.jpg" width="1116" height="452" alt="「模组」中的滑块、开关和一个按键">

这些类型的子类按其父类型显示。其他类的选项不会显示，隐藏选项（`is_hidden=True`，包括 `HiddenOption`）也不会显示。

## 整理你的选项

「模组」将你的模组页面分为多个标签页，所有模组遵循同一规则：

1. 不在任何 `NestedOption` 中的选项放入「**通用**」标签页。
2. 每个第一层的 `NestedOption` 成为一个**标签页**，以其 `display_name` 命名。
3. 在标签页内，每个 `NestedOption` 成为一个**子标签页**。该标签页的其他选项放入一个「通用」子标签页。
4. 更深层的 `NestedOption` 成为一行「**打开**」，打开一个按同样规则排列的界面。超过 4 层则不显示。
5. `GroupedOption` 在其选项上方显示一个**分区标题**。紧接着另一个标题的标题不显示。嵌套的分组会被展平：放在内层分组之后的选项，会显示在该内层分组的标题下。只包含页面的分组不显示标题，除非其后跟着一个不属于该分组的选项：这时它的标题会显示在该选项上方。

<img src="site/images/tabs.jpg" width="1200" height="112" alt="「模组」中某个模组的标签栏">

SDK 本身会把你的选项放入名为「Options」的分组，把你的按键（`@keybind`）放入名为「Keybinds」的分组（`Mod.iter_display_options`）。因此，默认情况下「通用」标签页会显示「Options」标题；如果你的模组有按键，还会显示「Keybinds」。如果你的第一个选项是一个分组，「Options」不会显示（见规则 5）。如果你的模组重写了 `iter_display_options`，「模组」会按照它给出的内容显示，与控制台相同。

例如：

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

**把你的选项传给 `build_mod(options=[...])`**。不传这个参数时，`build_mod()` 收集模块中选项的顺序可能会变化，并且会忽略 `GroupedOption` 和 `NestedOption`。也请为每个 `NestedOption` 设置 `display_name`：否则标签页会直接显示其标识符（「combat」）。

## 说明面板

- 玩家选中某个选项时，面板显示它的 `description_title`（默认为其 `display_name`）和 `description`。
- SDK 会把说明中的 HTML 转换为文本：`<br>` 变为换行。「模组」将其作为文本显示，并合并连续的空行。
- 未选中任何内容时，面板在「通用」标签页中显示你的模组的说明；在其他标签页或子标签页中，显示其 `NestedOption` 的说明，如果没有则什么都不显示。

## 更改如何传到你的模组

- 「模组」在游戏线程上执行 `option.value = new_value`，与控制台相同。随后 SDK 调用 `on_change_anytime`；如果你的模组已启用，再调用 `on_change_while_enabled`。
- **这些函数在值改变之前运行**。请从它们的 `value` 参数读取新值：此时 `option.value` 仍是旧值。
- **拖动滑块时，最多每 100 毫秒发送一个值**，且最后一个值一定会发送。因此你的函数每秒可能运行十次：请保持轻量，不要写文件，也不要做耗时的查找。
- 按钮调用 `on_press(option)`，同样在游戏线程上。
- 「已启用」开关调用 `mod.enable()` 或 `mod.disable()`，与控制台相同。
- 保存通过 SDK 自身的 `mod.save_settings()` 完成：更改后立即保存；滑块则在关闭「模组」时或下一次更改其他设置时保存。按钮不会保存任何内容。

## 限制

| 项目 | 上限 | 超出时 |
|---|---|---|
| 模组 | 64 | 之后的不显示 |
| 行（所有模组合计） | 3,000 | 之后的不显示 |
| 同一页面的行 | 100 | 之后的不显示 |
| 页面层级 | 4 | 更深的页面不显示 |
| 选项或可选项的名称 | 80 个字符 | 截断 |
| 说明 | 600 个字符 | 截断 |
| 下拉列表或左右箭头选择的可选项 | 64 | 整个选项不显示 |

一行可以是一个选项，也可以是分区标题、标签页或「已启用」开关。在第一层，100 行同时涵盖「通用」标签页和各个标签页。被截断的标题或标签页，会连同其全部内容一起不显示。

以下内容也不会显示：
- 没有可选项，或某个可选项不是文本的列表；
- 最小值不小于最大值，或某个边界、步长或值为 NaN 或无穷大的滑块；
- 名称不是由 1 到 32 个字母或数字组成的按键，例如手柄按键。`MODEL_BUILT` 这一行不会统计它。

如果列出你的选项的函数出错，或者某个滑块的值根本不是数字（`None`、文本），「模组」会显示在此之前的内容，并把你的模组计入 `failed_mods`。

## 语言

「模组」自身的文字跟随游戏语言：英语、法语或简体中文，其他语言显示英语。你的选项名称和说明按你的模组提供的原样显示：「模组」不会翻译它们。

## 建议

- 把你的选项传给 `build_mod(options=[...])`，并按你希望显示的顺序排列。
- 名称要简短，并为每个选项写说明：玩家在面板中读到的就是它。
- 用 `GroupedOption` 把相关选项归为一组，用 `NestedOption` 区分不同主题。两层就足以让所有内容放进标签页和子标签页。
- 保持 `on_change` 函数轻量，并从参数读取新值。
- 用 `is_hidden=True` 或 `HiddenOption` 隐藏模组的内部值。

## 检查你的模组

1. 安装 Mod Settings 的两个文件：`mod_settings.sdkmod` 和 `mod-settings_999_P.pak`（见 [README](README.zh.md)）。
2. 启动游戏，打开暂停菜单，选择「模组」，再选择你的模组。
3. 与 SDK 控制台的模组菜单对比：两边应显示相同的选项。
4. 如果缺少内容，请在 `unrealsdk.log` 中查找 `[ModSettings] MODEL_BUILT` 这一行。它给出所有模组合计的总数，不说明是哪个模组：`unsupported`（未知类型、无效值，或超过 64 个可选项）、`truncated`（被限制截断的行、标签页或模组，每次截断计为 1）和 `failed_mods`（列出选项时出错的模组数量）。隐藏的选项不计入。

## 完整示例

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
