# BetterRewards

BetterRewards combines reward adjustments for solo Hard and Ultimate Vault Hunter (UVH) play, an experimental level 100 cap, and a Return to vanilla and disable feature. The creator made it for a longer character progression, less repetitive grinding, and a reason to keep looking for better equipment. It is a public beta.

![A vending machine offering a level 100 shield](images/betterrewards/vending-level-100.jpg){: width="1600" height="902"}

## XP and cash

| Current mode | Character XP | Unlocked specialization XP | Cash income |
|---|---|---|---|
| Hard, without UVH active | ×1.25 | ×1.25 | ×1.25 |
| UVH | ×1.30 | ×1.30 | ×1.30 |

These multipliers apply on top of the actual vanilla rewards for each mode. The Hard and UVH bonuses replace each other; they do not stack. All currently supported UVH stages use the same settings, which may be adjusted by difficulty or UVH stage in future updates.

- The specialization bonus applies only once specialization has been unlocked.
- Purchase costs and other currencies are unaffected.
- Only solo Hard and UVH play is adjusted. Easy and Normal rewards are unchanged.
- Enemies get no damage, health or quantity multipliers, although extra levels and skill points make the player stronger.

## Choose your loot preset: install one only

| Preset | Hard | UVH |
|---|---|---|
| Standard | ×1.50 | ×1.75 |
| Enhanced | ×3.00 | ×3.50 |
| Insane | ×10.00 | ×12.00 |
| MaxLoot | ×10,000 | ×10,000 |

The presets adjust legendary and pearlescent drop weights, and the drop chances of mapped dedicated boss loot. MaxLoot is meant for testing or loot-heavy fun. All four presets currently use the same XP and cash settings.

## Level 100 (experimental)

- After finishing the main story and unlocking UVH, enter solo UVH with BetterRewards enabled: this registers that character for the level 100 cap.
- The character stays qualified when you return to another solo difficulty.
- A character that entered UVH before must enter it again with the mod enabled to be registered.
- No levels, XP or skill points are given directly: keep leveling normally.
- Levels 71 to 100 award skill points as usual, for 30 extra character skill points in total.
- Equipment and enemies follow the game's usual relative-level rules; some enemies may go above level 100.

![The skills screen of a level 100 character](images/betterrewards/skills-level-100.jpg){: width="1600" height="898" loading="lazy"}

## Installation

BetterRewards needs the community BL4 PythonSDK (Oak2 Mod Manager), installed separately: [installation guide](https://bl-sdk.github.io/oak2-mod-db/).

1. Save and fully exit the game, then back up your character and shared saves.
2. Install the BL4 PythonSDK by following its guide.
3. Download one of the four ZIPs, one per loot preset, from the Nexus page.
4. Extract its `bl4_hard_rewards` folder into the game's `sdk_mods` folder.
5. Enable BetterRewards in the SDK Mods menu if needed.

To update or switch presets, replace the supplied files in the same folder. Keep your `level80_unlocks.json`, SDK settings, `return_python_backups`, `return_python_state.json` and any older `return_jobs` backups. Do not rename folders to run several copies.

A mod disabled after returning to vanilla stays disabled until you enable it again. If you have already confirmed Return to vanilla, let it finish and wait for "Saved data verified; Mod DISABLED" before updating or switching presets.

## Before uninstalling or returning to vanilla

**Do not simply delete the mod and then load a high-level character.** Returning lowers levels, and enabling the mod again does not restore your previous high-level progress.

To uninstall the mod and return to vanilla:

1. Save normally, and temporarily turn off Steam Cloud for this game.
2. Move gear above level 70 from storage, Lost Loot and the Reward Center into your current character's backpack, then save again. World-boss reward packages are in the Reward Center, not in Lost Loot.
3. Load a solo character and leave any vehicle. Find BetterRewards in the SDK Mods menu, select Return to vanilla and disable, or Disable, then read and confirm the prompt.
4. Wait for "Converted; guard remains ON", then immediately save and return to the main menu. Do not continue farming.
5. At the main menu, wait for "Saved data verified; Mod DISABLED". The process is complete only once this message appears. Fully exit the game, restart, and check your character, equipment and skill points.

The mod's messages appear in Chinese and English, and its menu option reads "返回原版并停用 / Return to vanilla and disable".

If the mod finds high-level data on another character, in shared data or in unclaimed items, the conversion stops and the mod stays enabled. Do not uninstall it until you see "Saved data verified; Mod DISABLED". One operation converts only one high-level character.

What the return changes:

- A character above level 70 goes down to level 70, with a total of 69 character skill points. Its allocated character skills are reset and must be assigned again.
- Carried and equipped gear above level 70 goes down to level 70, with stats adjusted to its new level.
- Specialization, money and mission progress are kept.

The process first makes a local backup of the account's most recently saved files. The conversion itself covers the loaded character and its carried and equipped items. The backups are in `bl4_hard_rewards/return_python_backups/job-id/original`: copy them outside the mod folder before removing the mod. If you used an older version and have a `return_jobs` folder, keep its backups too.

Everything happens on your computer; no save is uploaded, and no PowerShell, browser or outside tool is needed. The automatic check supports the Windows Steam save layout with a single identifiable Steam account folder.

## Compatibility

- Windows x64, Steam, solo play.
- This version is adapted for Steam BuildID 26007962. After a game update, check the Nexus page for compatibility before loading high-level characters.
- Avoid combining it with other mods or trainers that change the same XP, cash, loot or level-cap systems.

## Reporting a bug

Report bugs on the Nexus page, with:

- your BetterRewards version;
- your loot preset;
- your game difficulty;
- your other installed mods;
- what you were doing when the problem happened.
