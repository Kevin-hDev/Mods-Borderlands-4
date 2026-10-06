# Changelog

## 1.1.5 - 2026-10-06

- New WINDOW button at the top of the menu, beside THEME: three sizes, LARGE (default), FULL SCREEN and NORMAL (the previous size). More room, same text size. Each mod keeps its own.
- The Orbit camera now opens from first person too. Leaving it brings back the view you had: in third person, the same shoulder and settings.
- Smooth camera transitions: switching between first person, third person and the Orbit camera glides instead of jumping. On by default, with its own switch. Its duration, Transition animation, is shared with the shoulder switch.
- Aiming in the Orbit camera follows your Aim View setting: over the shoulder or first person. Release to go back to Orbit.

## 1.1.4 - 2026-10-06

- The menu now opens from the console whatever your console key is, for example "+". With some keys, the console does not reopen by itself when the menu closes: just press your console key.

## 1.1.3 - 2026-10-06

- Fixed the switch to first person during native wall climbing and the camera jump when pulling over the ledge.
- Added smooth shoulder switching, enabled by default, with an on/off option and a 0.05–1 second duration slider in Camera; default duration: 0.20 seconds.
- Added smooth camera recentering during native climbing.
- Reduced redundant game-code checks while aiming to avoid the severe FPS drop with additional aim zoom.
- Organized Camera settings into four tabs and improved the menus: themes, Escape to close, retained focus and background blur.
- Existing saved settings, weapon-specific zoom and the aim-view selection are preserved.

## 1.1.2 - 2026-10-06

- Fixed a severe FPS drop when aiming in third person with additional aim zoom enabled.
- Removed redundant per-frame checks of unchanged game code while preserving live camera and weapon validation.
- Existing settings, weapon-specific zoom and smooth aiming transitions are preserved.

## 1.1.1 - 2026-10-06

- New Camera framing controls: Aim Zoom (Wide, Standard, Close), Shoulder Spacing (Tight, Standard, Open), and Camera Height (Standard, Higher, Lower), each with a custom slider.
- Defaults: 15% additional aim zoom, 10% wider shoulder spacing, and standard height. Weapon-specific zoom is preserved; sniper rifles remain in first person.
- Fixed: increasing zoom could shift the aimed point when entering aim. The reticle stays centered and framing preserves the aimed point when obstacles allow it.
- Improved camera handling near walls, pillars, and tight spaces: smooth recovery when the view clears, with lateral centering when the shoulder side is obstructed.
- Reduced work on the first aim to address the observed first-session stall.
- Improved settings and menus: confirmation after saving, rollback on save failure, and clearer feedback.

## 1.1.0 - 2026-10-04

- Third-person aiming with native weapon zoom and a visible reticle.
- Saved Camera setting to choose third-person or first-person aiming; third person is the default when enabled.
- Crouch and switch shoulders while aiming. Sniper rifles stay in first person; heavy and unsupported weapons retain the native view.
- Smooth aim-in and aim-out zoom, including quick repeated aiming.

## 1.0.3 - 2026-10-02

- Fixed: in third person, landing a ground slam switched the view to first person for a moment.

## 1.0.2 - 2026-09-27

- Fixed: the third-person toggle did nothing for characters using an alternate player animation class.

## 1.0.1 - 2026-09-27

- A settings window, in English and French, with a Camera page and a Commands page.
- Shoulder switching: the camera moves to the left or right shoulder. Key 6 by default.
- Orbit camera: the camera turns freely around the character. Key 7 by default. Two more keys, none set by default,
  move it closer or farther away.
- Commands page: every camera key, for keyboard and mouse and for controller, with PlayStation or Xbox icons.
- Loot reach: pick up loot and open containers from farther away, from 1× to 3×, 2× by default.
- Fixed: in third person, you had to aim next to an item to pick it up.
- Fixed: when downed, the view switched to an offset first-person view; third person now stays in place.

## 1.0.0 - 2026-09-25

- Initial public source release.
- Native over-the-shoulder camera on foot, with first-person aiming.
- Configurable third-person shortcut, P by default.
- FOV slider from 70 to 150, active while the mod is enabled.
- Restores third person after sliding and leaving a vehicle.
