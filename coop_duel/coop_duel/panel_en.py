"""English texts of Co-op Duel's window, its first language: its page, the message on the screen, and why a duel
does not start (each refusal says its real cause, that the game is not changed, and what to do)."""

from .panel_common_en import TEXT as COMMON

TEXT = {
    **COMMON,
    "duel": "DUEL",
    "duel_how": "Shoot each other. A player who falls stays down, safe, until the round ends, and a teammate can get "
                "them back up. The last team standing wins the round, then everyone gets back up on the spot. With two "
                "teams, enemies nearby attack everyone. Only the host needs this mod.",
    "start": "START DUEL", "stop": "STOP DUEL",
    "host": "Host",
    "banner_start": "DUEL", "banner_round": "ROUND {round}", "banner_over": "DUEL OVER",
    "banner_refused": "CO-OP DUEL",
    "banner_draw": "DRAW", "team_name": "TEAM {team}", "player_fallback": "Player {number}",
    "teams": "TEAMS", "teams_each": "EACH FOR THEMSELVES", "teams_vs": "VS", "teams_one": "ONE TEAM ONLY",
    "ready_teams": "Choose each player's team. A player alone in a team plays for themselves.",
    "teams_allies": "Three teams or more: nearby bandits or Order soldiers may fight alongside a team.",
    "teams_alone": "No other player in your game. Invite a friend: they will show up here.",
    "teams_locked": "A duel is on. Stop it on the DUEL page before changing the teams.",
    "teams_not_host": "Only the host of the game arranges the teams.",
    "options": "OPTIONS", "ready_options": "Saved as you go.",
    "open_key_label": "Open this menu", "open_key_hint": "The key that opens Co-op Duel in game.",
    "duel_key_label": "Start or stop the duel",
    "duel_key_hint": "The key that starts the duel, or stops it, without opening this menu.",
    "press_key": "PRESS A KEY", "key_taken": "This key is already used by the other shortcut: choose another one.",
    "ready_duel": "Stand near the other players, everyone on foot, then press START DUEL.",
    "ready_on": "A duel is on. STOP DUEL ends it and puts everyone back to normal.",
    "start_off": "Co-op Duel is off. Your game is not changed. Switch it on at the bottom left, then start the duel "
                 "again.",
    "start_already_on": "A duel is already on. Your game is not changed. Stop it before starting a new one.",
    "start_not_host": "Only the host of the game can start a duel. Your game is not changed. Ask the host to start "
                      "it.",
    "start_no_character": "No duel here. Your game is not changed. Load a game, then start the duel again.",
    "start_in_vehicle": "No duel from a vehicle. Your game is not changed. Everyone gets out, then start the duel "
                        "again.",
    "start_player_away": "A player has no character yet: joining, or coming back. Your game is not changed. Wait for "
                         "them, then start the duel again.",
    "start_one_team": "Every player is in the same team. Your game is not changed. Split them on the TEAMS page, "
                      "then start the duel again.",
    "start_no_guest": "No other player in your game. Your game is not changed. Invite a friend, then start the duel "
                      "again.",
    "start_player_down": "A player is down. Your game is not changed. Wait until everyone is back up, then start the "
                         "duel again.",
    "start_team_refused": "The game refused the duel. Your game is not changed. Try again; the reason is in "
                          "unrealsdk.log.",
    "start_refused": "The duel could not start. Your game is not changed. Try again; the reason is in "
                     "unrealsdk.log.",
    "stop_player_joined": "A player joined the game. Put them in a team on the TEAMS page, then start the duel again.",
    "stop_teams_left": "Only one team is left. Split the players on the TEAMS page, or invite a friend, then start a "
                       "new duel.",
}
