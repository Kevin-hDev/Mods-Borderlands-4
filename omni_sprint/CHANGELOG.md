# Changelog

## 1.0.5 - 2026-10-02

- Fixed: in third person, landing a ground slam switched the view to first person for a moment.

## 1.0.4 - 2026-09-27

- Fixed: the third-person toggle did nothing for characters using an alternate player animation class.

## 1.0.3 - 2026-09-27

- Shoulder switching: the third-person camera moves to the left or right shoulder. Key 6 by default.
- Orbit camera: the camera turns freely around the character. Key 7 by default. Two more keys, none set by default,
  move it closer or farther away.
- New Commands page: every camera key, for keyboard and mouse and for controller, with PlayStation or Xbox icons.
- Loot reach: pick up loot and open containers from farther away, from 1× to 3×, 2× by default.
- Fixed: in third person, you had to aim next to an item to pick it up.
- Fixed: when downed, the view switched to an offset first-person view; third person now stays in place.

## 1.0.2 - 2026-09-25

- Adds a settings window.
- Third-person mode with an over-the-shoulder camera on foot, off by default. Aiming switches to the game's own
  first-person view.
- A key turns third person on and off: P by default, changed in the mod menu with a keyboard key or a mouse button
  other than the left one.
- Custom FOV now comes from the shared [camera runtime](../camera_runtime/), which Apex Movement carries too. If
  both mods are installed, Apex Movement's camera settings are the ones used.

## 1.0.1

- Give third-person backward ground sprint a running animation while keeping the game's sprint speed.
- Add optional Custom FOV (70–150), off by default. Disabling it restores the player's previous game FOV; restoration
  after a menu transition and a full restart was verified with a custom FOV of 140 and a native FOV of 110.
- Keep animation and FOV cleanup tied to the current player and leave their game values alone when another system has
  changed them.

## 1.0.0

First release.

- Sprint in every direction: the game's sprint angle limit goes from 60 to 180 degrees, at the game's own sprint
  speed.
- Switched off in the mod menu, the game's limit is put back.
