# FAQ

## Does Mod Settings work on the Epic Games version?

It has never been tried on the Epic Games version, only on the Steam version 1.11.0-4906557. If you try it, tell us
how it goes in an issue, with the SDK log.

## And in co-op?

It has never been tried in co-op. Mod Settings sends and receives nothing over the game's network: it only sets the
mods on your PC. What a mod does in co-op depends on that mod.

## Is the SDK console still useful?

Yes. MODS is another door to the same settings: a change made in one shows in the other, and MODS reads everything
again each time it opens. To turn Mod Settings itself on or off, use the console.

## How do I turn Mod Settings off?

In the SDK console: `~`, then `mods`, then Mod Settings. On its page in MODS, its Enabled switch does not respond:
turned off from there, it would cut the page while you use it. Once it is off, the MODS entry stays in the menu,
because it comes from the pak, and MODS shows "MOD SETTINGS DOES NOT ANSWER" when you open it. To make it go away, also remove the pak
`mod-settings_999_P.pak`.

## What happens to my settings if I remove Mod Settings?

Nothing changes. Your mods' settings are saved by the SDK in `...\Borderlands 4\sdk_mods\settings\`, one file per
mod, and they stay there. Remove Mod Settings' two files: the pause menu and the main menu come back as before.

## Why doesn't a mod have all its settings in MODS?

MODS shows what each mod declares to the SDK, like the console. A mod that has its own settings window may declare
only part of its settings there, or none. See [troubleshooting](TROUBLESHOOTING.md).

## Why doesn't Mod Settings have settings of its own?

Mod Settings is another door to the SDK console, nothing more: it shows and sets what each mod declares, without
adding settings of its own on top. Each extra feature would be one more thing to break at a game update, or to
conflict with the mods it shows. And an author who tries their mod in the console has also tried it in MODS.

## Does Mod Settings slow the game down?

With the menus closed, it does nothing. Each time MODS opens, and a first time when the game loads the pause menu or
the main menu, it reads the mods' settings again, which freezes the game for a short moment: 0.2 to 0.35 seconds the
first time after the game starts, then a few milliseconds to 50 milliseconds, with 22 to 29 mods installed (measured
in game).

## Does Mod Settings go on the Internet? Is it safe?

It does not go on the Internet. The page and the Python mod talk through a small service that only listens to your
PC, and that refuses requests from web pages open in your browser. The details are in [How it works](HOW_IT_WORKS.md).

## Can I reuse its code?

Yes, under the Mozilla Public License 2.0: see the License part of the [README](README.md).
