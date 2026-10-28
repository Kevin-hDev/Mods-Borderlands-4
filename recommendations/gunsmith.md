# Gunsmith

Gunsmith brings weapon customization into your inventory. Break down the guns you don't need, discover their parts, and rebuild compatible weapons around the way you play.

![The Gunsmith tab in the inventory, with the weapon preview and its parts](images/gunsmith/menu-1.jpg){: width="1600" height="906"}

## What it does

- **Discover once, reuse freely.** Disassembling a gun permanently unlocks its recoverable part variants. There are no duplicate copies to manage: your discoveries become a reusable collection.
- **See the change before you commit.** The game's own weapon preview shows the gun. Hover over a part to highlight it, click to select it, compare the proposed stats, then apply the swap.
- **Find the part that matters.** Installed and available parts are listed separately. Search, filter by category, and sort by stats.
- **Turn unwanted loot into parts.** Disassemble selected guns, or all the weapons marked as junk.
- **Bring a favourite up to your level.** Upgrade a supported weapon to your character's level from the workbench.
- **Share Discoveries** (new in 1.0.8). Turn it on to merge the parts unlocked by all your characters, and share the ones they discover next.

Swaps stay within the same weapon family: disassembling a Jakobs revolver can unlock parts for other compatible Jakobs revolvers, but a sniper barrel does not go on a pistol.

![Choosing a part in Gunsmith, with the proposed stats](images/gunsmith/menu-2.jpg){: width="1600" height="879" loading="lazy"}

## How to use it

Open **Inventory > Gunsmith**, next to the ECHO Logs tab, or hover over a weapon card and press **G**.

- Left click: select a part.
- Hold the right mouse button: rotate the weapon.
- Mouse wheel over the preview: zoom.
- Mouse wheel over the part list: scroll.
- **Reset Preview** restores the starting view; **Change Weapon** chooses another weapon.

Only weapons that are not equipped can be modified. Move the weapon from your four weapon slots to your backpack first.

## Installation

Gunsmith runs in native C++, with the game's own inventory interface and weapon preview. It does not need the Python SDK, a Python installation, or any activation in a menu: the loader and runtime it needs are included.

1. Close Borderlands 4.
2. Download Gunsmith from its Nexus page and extract it.
3. Copy the extracted `OakGame` folder into your Borderlands 4 installation folder, and let the folders merge.
4. Launch the game, load your character, and open **Inventory > Gunsmith**.

To update, close the game and copy the new version over the old one. The full instructions, including how to uninstall, are on the Nexus page.

## Know before you build

- Back up your saves. Disassembly consumes weapons, and uninstalling does not give them back or undo saved weapon changes.
- Only compatible parts are supported; mixing different weapon types is not included.
- Required and legendary modules may need to be replaced instead of removed.
- The first use of thumbnails can cause brief hitches.
- Multiplayer, controllers, ultrawide screens, and other versions of the game have not been checked yet.
- Other mods that change the inventory interface may conflict.

The full list is on the Nexus page.

## Reporting a bug

Report bugs on the Nexus page, with:

- your Gunsmith version;
- your game version, and whether it is Steam or Epic;
- your game language;
- the file `unrealsdk.log`.
