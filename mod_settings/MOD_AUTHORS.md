# Mod Settings: a guide for mod authors

[Français](MOD_AUTHORS.fr.md) · [中文](MOD_AUTHORS.zh.md) · [日本語](MOD_AUTHORS.ja.md)

Mod Settings adds a MODS entry to the pause menu and the main menu of Borderlands 4. It shows and changes the options
of every mod of the Python SDK, with the pieces of the game's Options screen.

This guide explains how your mod appears in MODS, and how to write your options so they show up well.

## In short

- **You have nothing to install, import or call.** MODS reads what your mod declares to `mods_base`, exactly like the
  mods menu of the SDK's console.
- **Your mod does not depend on Mod Settings.** Without it, your mod works the same. Don't check whether it is
  installed.
- **What shows up in the console shows up in MODS**, within the limits given below.

## What MODS shows of your mod

- **The mod list**: every mod of the SDK, in the order of the console's menu.
- **Your mod's page**: its name, its options, and a description panel. In the General tab, when the player
  highlights no option, this panel shows your mod's description, then its version and author.
- **The Enabled switch**, at the top of the General tab, if your mod can be turned on and off.
- **"No settings"** when your mod has no visible option and cannot be turned on and off, and in any empty tab.

<img src="site/images/mods-list.jpg" width="1600" height="840" alt="The mod list in MODS, each mod with its OPEN button, and the chosen mod's description on the right">

The name, description, version and author are those of your `Mod` object, which `build_mod()` fills from your
`pyproject.toml` or your module.

## Option types

| SDK option | In MODS | What MODS reads |
|---|---|---|
| `BoolOption` | a switch | `true_text` and `false_text` as the texts of its two positions |
| `SliderOption` | a slider | `min_value`, `max_value`, `step`, `is_integer`; as many decimals as the step, 3 at most (a step smaller than 0.0005 gives none); none with `is_integer`, which is `True` by default: pass `is_integer=False` for a slider with decimals |
| `SpinnerOption` | a choice with arrows | `choices`; `wrap_enabled` is not read |
| `DropdownOption` | a dropdown list | `choices` |
| `KeybindOption` | a key | the player clicks it, then presses the new key; Esc cancels. Only letters, digits, F1 to F12, the arrows, the control keys, the numeric keypad and the right, middle and side mouse buttons are taken, and the capture stops after 10 seconds without a key. With `is_rebindable=False`, the key is shown but cannot be changed |
| `ButtonOption` | a button | `on_press` |
| `GroupedOption` | a section title above its options | `display_name` |
| `NestedOption` | a tab, a sub-tab or a page | see "Laying out your options" |

<img src="site/images/option-types.jpg" width="1116" height="452" alt="Sliders, switches and a key in MODS">

A subclass of one of these types is shown as that type. An option of any other class is not shown, and neither is a
hidden option (`is_hidden=True`, `HiddenOption` included).

## Laying out your options

MODS lays out your mod's page in tabs, with the same rule for every mod:

1. Options that are in no `NestedOption` go in a **General** tab.
2. Each first-level `NestedOption` becomes a **tab**, named by its `display_name`.
3. Inside a tab, each `NestedOption` becomes a **sub-tab**. The tab's other options go in a General sub-tab.
4. Deeper down, a `NestedOption` becomes an **OPEN** row, which opens a screen laid out the same way. Beyond 4 levels,
   it is not shown.
5. A `GroupedOption` puts a **section title** above its options. A title followed at once by another title is not
   shown. Nested groups are flattened: an option placed after an inner group shows under that group's title. A group
   that holds nothing but pages shows no title, unless an option outside the group follows it: its title then shows
   above that option.

<img src="site/images/tabs.jpg" width="1200" height="112" alt="A mod's tab bar in MODS">

The SDK itself puts your options in an "Options" group and your keys (`@keybind`) in a "Keybinds" group
(`Mod.iter_display_options`). By default, the General tab therefore shows the "Options" title, and "Keybinds" if your
mod has keys. If your first option is a group, "Options" is not shown (rule 5). If your mod overrides
`iter_display_options`, MODS follows what it yields, like the console.

For example:

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

**Pass your options to `build_mod(options=[...])`.** Without that argument, `build_mod()` gathers your module's
options in an order that may change, and it skips `GroupedOption` and `NestedOption`. Also give each `NestedOption` a
`display_name`: without it, the tab shows the identifier as it is ("combat").

## The description panel

- When the player highlights an option, the panel shows its `description_title` (its `display_name` by default) and
  its `description`.
- The SDK turns the description's HTML into text: `<br>` becomes a line break. MODS shows it as text and merges
  blank lines that follow each other.
- When nothing is highlighted, the panel shows your mod's description in the General tab; in another tab or sub-tab,
  that of its `NestedOption`, and nothing if it has none.

## When a change reaches your mod

- MODS writes `option.value = new_value` on the game's thread, like the console. The SDK then calls
  `on_change_anytime`, then `on_change_while_enabled` if your mod is enabled.
- **These callbacks run before the value changes.** Read the new value from their `value` argument: `option.value`
  still holds the old one.
- **A slider being dragged sends one value every 100 ms at most**, and always the last one. Your callback may therefore
  run ten times a second: keep it light, with no file writes or costly searches.
- A button calls `on_press(option)`, on the game's thread too.
- The Enabled switch calls `mod.enable()` or `mod.disable()`, like the console.
- Saving goes through `mod.save_settings()`, the SDK's own: right after a change, and for a slider, when MODS closes or
  at the next change of another setting. A button saves nothing.

## Limits

| What | Limit | Beyond it |
|---|---|---|
| Mods | 64 | the next ones are not shown |
| Rows, all mods together | 3,000 | the next ones are not shown |
| Rows on one page | 100 | the next ones are not shown |
| Page levels | 4 | deeper pages are not shown |
| Name of an option or a choice | 80 characters | cut |
| Description | 600 characters | cut |
| Choices of a dropdown or an arrow choice | 64 | the whole option is not shown |

A row is an option, but also a section title, a tab or the Enabled switch. At the first level, the 100 rows cover the
General tab and the tabs together. A title or a tab that is cut takes everything it holds with it.

These are not shown either:
- a list with no choices, or with a choice that is not text;
- a slider whose minimum is not smaller than its maximum, or whose bound, step or value is NaN or infinite;
- a key whose name is not made of 1 to 32 letters or digits, for example a gamepad key. The `MODEL_BUILT` line does
  not count it.

If the function that lists your options fails, or if a slider's value is not a number at all (`None`, text), MODS
shows what came before, and counts your mod in `failed_mods`.

## Languages

MODS's own texts follow the game's language: English, French or Simplified Chinese, and English for any other
language. Your options' names and descriptions are shown as your mod gives them: MODS does not translate them.

## Tips

- Pass your options to `build_mod(options=[...])`, in the order you want to see them.
- Give short names, and a description to every option: that is what the player reads in the panel.
- Group related options with a `GroupedOption`, and split topics with `NestedOption`s. Two levels are enough for
  everything to fit in tabs and sub-tabs.
- Keep your `on_change` callbacks light, and read the new value from their argument.
- Hide your mod's internal values with `is_hidden=True` or a `HiddenOption`.

## Checking your mod

1. Install Mod Settings: both its files, `mod_settings.sdkmod` and `mod-settings_999_P.pak` (see the
   [README](README.md)).
2. Start the game, open the pause menu, choose MODS, then your mod.
3. Compare with the mods menu of the SDK's console: you should find the same options there.
4. If something is missing, look for the `[ModSettings] MODEL_BUILT` line in `unrealsdk.log`. It gives totals for
   all mods together, without saying which one: `unsupported` (unknown type, invalid values, or more than 64 choices),
   `truncated` (rows, tabs or mods cut by a limit, each cut counting as 1) and `failed_mods` (the number of mods whose
   listing failed). Hidden options are not counted.

## Full example

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
