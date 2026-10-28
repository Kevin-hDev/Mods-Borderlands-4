# Troubleshooting

Look for what you see. Each entry says why it happens and what to do.

Mod Settings' lines in the SDK log start with `[ModSettings]`. The log is
`...\Borderlands 4\OakGame\Binaries\Win64\Plugins\unrealsdk.log`, and it is rewritten at each launch of the game:
copy it before relaunching. If nothing here helps, open an issue on GitHub with that file.

## For players

### There is no MODS entry in the menu

**Why:** the MODS entry comes from the pak `mod-settings_999_P.pak`. It is not in
`...\Borderlands 4\OakGame\Content\Paks\`, or another mod also replaces the pause menu or the main menu: only one of
the two can win.

**What to do:** put the pak in its place; it is in the Nexus file "Mod Settings Paks". If another mod changes these
menus, remove it to try.

### MODS shows "MOD SETTINGS DOES NOT ANSWER"

**Why:** the page is there, but the Python mod does not answer. The Python SDK is not installed,
`mod_settings.sdkmod` is not in `...\Borderlands 4\sdk_mods\`, Mod Settings is turned off in the SDK console, or it
could not start.

**What to do:** install the SDK and `mod_settings.sdkmod` (see the [README](README.md)). Open the SDK console (`~`,
then `mods`) and check that Mod Settings is on. Otherwise, look for `[ModSettings]` in the log:

- no line: the SDK did not load Mod Settings, or it is turned off;
- `START_FAILED port_in_use_or_refused`: another program uses port 38791, or Mod Settings was just turned off and has
  not freed it yet. Wait a few seconds, then turn Mod Settings off and on again in the console;
- `START_TIMEOUT`: turn Mod Settings off and on again in the console;
- another `START_FAILED` line: turn Mod Settings off and on again in the console. If it comes back, report it with
  the log.

### MODS shows "THE MOD LIST IS NOT READY"

**Why:** the Python mod answers, but it has not finished reading the list of mods yet. If the message comes back each
time and the log has `MODEL_TOO_BIG`, the list of your mods is too big for MODS.

**What to do:** close MODS and open it again. If the message comes back, report it with the log.

### MODS shows "KEY CAPTURE NEEDS MOD SETTINGS"

**Why:** changing a key goes through the Python mod. It does not answer, or it has not sent the list of mods yet.

**What to do:** wait a moment, then try again. If the message comes back, see "MOD SETTINGS DOES NOT ANSWER", above.

### MODS shows "CHANGE REFUSED" followed by a number

**Why:** the change was not applied, and the row shows the mod's value again. The number says why:

- 0: Mod Settings did not answer in time, or it is turned off (see "MOD SETTINGS DOES NOT ANSWER", above);
- 409: the page still had the old list of settings, for example because a setting changed while MODS was opening;
- 403: this setting cannot be changed;
- 400: the value is outside what the mod accepts;
- 503: the game has too many changes waiting.

**What to do:** make the change again. If it is still refused, close MODS and open it again.

### A mod is not in the list

**Why:** MODS shows the Python SDK's mods, the same as the SDK console. A mod installed another way, for example a
lone `.pak` file, is not there. Beyond 64 mods, the next ones are not shown.

**What to do:** check whether the mod is in the SDK console (`~`, then `mods`). If it is there and not in MODS,
report it with the log.

### A mod shows "No settings", or fewer settings than in its own window

**Why:** MODS shows what the mod declares to the SDK, like the console. A mod that has its own settings window may
declare only part of its settings there, or none.

**What to do:** set this mod in its own window, opened as its author says. If its author wants it shown in full in
MODS, the [guide for mod authors](MOD_AUTHORS.md) explains how.

### A slider went back to its old value after a crash

**Why:** a slider is saved when you close MODS, or at the next change of another setting. A crash before that loses
its last value.

**What to do:** set it again, then close MODS.

### In the main menu, Escape opens "Quit Game"

**Why:** in the main menu, MODS is drawn inside the menu's page. For the game, Escape then means "quit", and it opens
that window in its own code, which a mod cannot hold back. In the pause menu, Escape works normally.

**What to do:** click Cancel, or use BACK and CLOSE.

### The pause menu or the main menu misbehaves after a game update

**Why:** the pak holds copies of these menus, made on the tested version of the game. An update that changes them
makes them outdated (see [How it works](HOW_IT_WORKS.md)).

**What to do:** remove `mod-settings_999_P.pak` until Mod Settings is updated. Your settings do not change.

### MODS is in English while the game is in another language

**Why:** MODS' texts exist in English, French and Simplified Chinese. For other languages, they stay in English. The
settings' names and descriptions are the ones each mod gives, often in English.

**What to do:** no setting changes this. If you want MODS in your language, ask for it in an issue.

## For mod authors

The [guide for mod authors](MOD_AUTHORS.md) explains how MODS shows your options. Here, only the symptoms, and the
part of the guide that answers them.

### An option of your mod does not show

**Why:** MODS does not read its type, its values are not valid, it goes over a limit, or it is hidden.

**What to do:** look for the `[ModSettings] MODEL_BUILT` line in the log. Its counters `unsupported`, `truncated` and
`failed_mods` say what was left out, as totals for all mods together. The guide explains it under "Checking your mod", with "Option types" and
"Limits".

### All your options are in the General tab, or their order changes

**Why:** without `build_mod(options=[...])`, the SDK gathers your module's options in an order that may change, and
it skips your `GroupedOption` and `NestedOption`.

**What to do:** pass your options to `build_mod(options=[...])`. See "Laying out your options" in the guide.

### Your `on_change` function reads the old value

**Why:** the SDK calls it before changing the value.

**What to do:** read the new value from its `value` argument. See "When a change reaches your mod" in the guide.

### The game stutters when a slider of your mod is dragged

**Why:** a slider sends its value up to ten times a second, and your `on_change` function is called each time.

**What to do:** keep it light: no file writes and no costly searches.

### MODS takes a while to open with your mod

**Why:** each time it opens, MODS calls the function that lists each mod's options (`iter_display_options`), on the game's
thread. If yours does heavy work, the game freezes while it runs, and MODS may show the previous list until the next
opening.

**What to do:** keep this function light: it should yield your options, without computing or loading anything.
