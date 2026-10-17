"""English texts of Co-op Duel's window, its first language: its page, the message on the screen, and why a duel
does not start (each refusal says its real cause, that the game is not changed, and what to do)."""

from .panel_common_en import TEXT as COMMON

TEXT = {
    **COMMON,
    "duel": "DUEL",
    "duel_how": "Shoot each other. The one who falls stays down 3 seconds, then gets back up on the spot, and the "
                "next round begins. Enemies nearby attack you both. Only the host needs this mod.",
    "start": "START DUEL", "stop": "STOP DUEL",
    "host": "Host", "guest": "Guest",
    "banner_start": "DUEL", "banner_round": "ROUND {round}", "banner_over": "DUEL OVER",
    "banner_refused": "CO-OP DUEL",
    "options": "OPTIONS", "ready_options": "Saved as you go.",
    "open_key_label": "Open this menu", "open_key_hint": "The key that opens Co-op Duel in game.",
    "duel_key_label": "Start or stop the duel",
    "duel_key_hint": "The key that starts the duel, or stops it, without opening this menu.",
    "press_key": "PRESS A KEY", "key_taken": "This key is already used by the other shortcut: choose another one.",
    "ready_duel": "Stand next to the other player, both on foot, then press START DUEL.",
    "ready_on": "A duel is on. STOP DUEL ends it and puts everyone back to normal.",
    "start_off": "Co-op Duel is off. Your game is not changed. Switch it on at the bottom left, then start the duel "
                 "again.",
    "start_already_on": "A duel is already on. Your game is not changed. Stop it before starting a new one.",
    "start_not_host": "Only the host of the game can start a duel. Your game is not changed. Ask the host to start "
                      "it.",
    "start_no_character": "No duel here. Your game is not changed. Load a game, then start the duel again.",
    "start_in_vehicle": "No duel from a vehicle. Your game is not changed. Both players get out, then start the duel "
                        "again.",
    "start_no_guest": "No other player in your game. Your game is not changed. Invite a friend, then start the duel "
                      "again.",
    "start_too_many": "A duel is for two players only for now. Your game is not changed. Play it with a single "
                      "guest.",
    "start_player_down": "A player is down. Your game is not changed. Wait until both are back up, then start the "
                         "duel again.",
    "start_team_refused": "The game refused the duel. Your game is not changed. Try again; the reason is in "
                          "unrealsdk.log.",
    "start_refused": "The duel could not start. Your game is not changed. Try again; the reason is in "
                     "unrealsdk.log.",
}
