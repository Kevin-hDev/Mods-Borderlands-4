# Changelog

## 1.0.2 — 2026-09-22

- Preserve the game's valid contextual grapple interactions, including carryable objects, instead of replacing them with an Apex shot. Keep the native targeting area aligned with the game's indicator.
- Restore the grapple's launch, connection and pulling sounds, with cleanup when a shot is released or cancelled.
- Keep the existing hand animation, rope visuals, movement tuning and saved settings.

## 1.0.1 — 2026-09-22

- Remember the last settings tab when closing and reopening the menu, including after a game restart.
- Restore navigation focus to the selected tab for controller use.
- Keep the selected tab when restoring or undoing gameplay settings; fall back to the first tab if a saved tab is invalid.

## 1.0.0 — 2026-09-22

- Grapple toward surfaces with adjustable range, pulling force, steering, speed and release behavior.
- Support short pulls close to surfaces, releasing with jump, and nearby-enemy melee priority.
- Add the custom settings window with English and French, reset controls and keyboard/controller navigation.
- Capture keyboard, mouse and controller bindings, including two-button combinations.
- Display PlayStation or Xbox button icons and reserve console-opening inputs.
- Handle session changes and interrupted window cleanup, and fall back to button names if icon rendering fails.

Development-only investigation modes and command-line probes are not included in this source distribution.
