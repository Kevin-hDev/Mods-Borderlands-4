"""Companions' window in English, its first language: its pages, its cards, its settings and its keys. The words are
sketch A's (esquisses_mod_companions, chosen by Kevin, decision 68 of docs/renforts), put in English; the cards' and
the keys' are It Follows' own for the same things. The setting rows' words are the settings' own (settings.py)."""

from .panel_common_en import TEXT as COMMON

TEXT = {
    **COMMON,
    "hunters": "VAULT HUNTERS", "allies": "ALLIES", "team_settings": "TEAM SETTINGS", "options": "OPTIONS",
    "team_count": "TEAM {count} / {most}",
    "team_none": "No companion yet: choose one to add it to the team.",
    "outfit": "OUTFIT", "outfit:own": "BASE", "outfit:player": "YOUR COLOURS",
    "team_launch": "LAUNCH THE TEAM", "team_stop": "STOP THE TEAM",
    "cards_locked": "Stop the team to change it.",
    "settings_locked": "Stop the team to change its settings: it keeps the ones it started with.",
    "team_elsewhere": "It Follows controls the companions. Use its menu.",
    "team_outdated": "Your It Follows is too old to share the companions, even when switched off: update it, "
                     "then restart the game.",
    "team_mismatch": "It Follows and Companions are at versions that do not work together, so no team starts: "
                     "update both, then restart the game.",
    "ready_cards": "Choose a companion to add it to the team, then LAUNCH THE TEAM.",
    "team_on_notice": "Your team follows you. Stop it here to change it.",
    "ready_settings": "The team's settings apply to all your companions.",
    "team_full": "The team is full: {most} companions at most.",
    "team_empty": "Add at least one companion first.",
    "team_busy": "Your choices are being saved: launch the team again.",
    "team_off": "Companions is disabled: enable it at the bottom left, then launch the team.",
    "team_not_started": "The team did not start. The reason is in unrealsdk.log.",
    "team_already_on": "The team is already on.",
    "team_main_menu": "Load a game first, then launch the team.",
    "team_stopped": "The team stopped: your companions no longer follow you.",
    "key_label": "Menu key", "press_key": "PRESS A KEY", "no_key": "NONE",
    "key_hint": "Opens this menu while you play; the game pauses while it is open, except in co-op. Select the "
                "field to choose a key.",
    "team_key_label": "Team key",
    "team_key_hint": "Launches your team, or stops it, while you play. Select the key to change it.",
    "key_taken": "That key is already Companions' other key: choose another one.",
    "value_times": "×{value}", "value_percent": "{value}%", "value_bonus": "+{value}%", "value_seconds": "{value} s",
    "value_never": "NEVER",
}
