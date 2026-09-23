# Changelog

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
