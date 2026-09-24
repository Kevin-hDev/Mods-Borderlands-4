# Changelog

## 1.1.4 - 2026-09-25

- New Options page, opened by the gear at the top of the settings window: third person, its key, custom field of
  view and the menu language.
- On-foot third-person mode with an over-the-shoulder camera, off by default. Aiming switches to the game's own
  first-person view.
- A key turns third person on and off: P by default, changed on the Options page with a keyboard key or a mouse
  button other than the left one.
- Custom field of view from 70 to 150, off by default.
- Wall climb can lean up to 90 degrees, along the wall, with the same maximum distance in every direction.
- In third person, the character is animated while climbing.
- Fixed: calling a vehicle during a slide could make the slide resume when getting out of the vehicle.
- The camera comes from the shared [camera runtime](../camera_runtime/), which Omni Sprint carries too. If both
  mods are installed, Apex Movement's camera settings are the ones used. The separate one-move files do not carry it.

## 1.1.3 - 2026-09-23

- Add the same visual settings window as Apex Grapple, with English and French labels, controller navigation and saved section selection.
- Keep the window responsive while the game is paused, including console handoff and Close.
- Prevent the two Apex windows from taking input at the same time; if an old console page has changed, release it safely.
- Shorter setting descriptions, in English and French: each one now says what you get in a single plain sentence.
- Setting names, values, limits and gameplay behavior are unchanged.

## 1.1.2

Fixed: the dash kept the game's own length on C4SH and Loveless, the two characters the latest game update added.
Each of them has a dash of its own, where the first four share one, and the mod only looked for the shared one. It
now finds the dash of the character you play as soon as you load in, and every Dash distance setting gives the same
dash on every character.

The first four characters' dash is unchanged.

Tested on game version 1.10.2-4845623, with Vex, C4SH and Loveless.

## 1.1.1

Fixed: after riding a vehicle, turning a move off, or the whole mod, left its values in the game. The walk speed,
the air strafe and the heavier gravity stayed until the next launch, and the log said every value had been put
back. Getting into a vehicle takes your character away from you and gives the same one back when you get out; the
mod read that return as a new game, and forgot what it had borrowed.

The mod now keeps what it holds even when it has nothing to write, and reads the value back before saying the game
has it again.

The moves themselves are unchanged.

## 1.1.0

Added: **Glide**, a new setting for the game's own glide — nothing new to learn, nothing new to press. Hold jump in
the air as you already do, and the glide goes faster: sideways and backwards too, since the game's glide already
allows every direction. Its line in the mod menu has its own switch and one setting, Glide speed, from 100 to
250 % of the game's speed, 130 % by default.

The game's glide tops out at 1200 in every direction; at 130 % it tops out at 1560, and the acceleration rises with
it so a short glide gains as much as a long one. 250 % is 3000, the speed of the game's own extended glide.

The descent is not touched: gravity and fall speed stay the game's. A faster glide therefore also covers more
ground, from the same height.

Tested on game version 1.10.2-4845623.

## 1.0.2

Fixed:

- After getting out of a vehicle, the controller's crouch button could stay out of the mod's reach until the next
  area: no landing slide and no ground slam from the controller. The mod now reads the game's key list again every
  second and follows it.
- Switching the mod off at the title screen could write into game objects the game had already removed, and wrote
  errors in the log. It now leaves them alone: the game loads its own values again with your next game.
- Settings are now held to their slider's range. A value typed out of range in the console mod menu, or edited by
  hand in the settings file, is brought back within it, and a value that is not a number goes back to its default.
  The log says so.
- A move whose switch-off failed is now tried again, instead of staying half on while the menu shows it off. When a
  game value cannot be restored, the log now says how many, instead of saying they all were.

Changed, as asked in the comments:

- Dash distance now goes up to 1000 % (was 300 %), and Extra jump height up to 1000 (was 100). The defaults stay
  200 % and 20.
- Past 300 %, the dash lasts as long as a 300 % dash, so the game's dash animation plays only once, and starts
  faster instead: a strong push that slows down to the game's dash speed, then ends as the game's dash does.

Also: unused code and outdated comments removed. The moves feel the same as in 1.0.1.

## 1.0.1

Fixed: the mod menu showed a move both on and off. Inside a move's line, the title said "(On)" and the line under
it "(Off)" (or the reverse) as soon as its switch differed from its default. The move itself was running as the
title said; only the second line was wrong.

## 1.0.0 — first public release

The moves, each with its own settings and, except the movement speeds, its own switch: movement speeds, auto sprint,
omnidirectional slides with the Axle slide, a longer dash, the ground slam and landing slide, air/tap strafe, heavier
falls and the wall climb.

Ships as the full mod pack, `apex_movement.sdkmod`, and as one file per move, which can be installed side by side.

Built and tested on game version 1.8.1-4709277, in the first area of the game, single player, with a controller and
with mouse and keyboard.
