"""English texts of Hunter Change's window. The class names are the game's own: Loveless "the Hacker" on 2K's page;
C4SH "the Rogue" read on one secondary source only (Borderlands wiki, 2026-09-28)."""

from .panel_common_en import TEXT as COMMON

TEXT = {
    **COMMON,
    "appearance": "APPEARANCE",
    "applies": "Applies at once, for this game.",
    "your_hunter": "YOUR HUNTER",
    "chosen": "CHOSEN",
    "no_game": "Load a game to choose a look.",
    "own_look": "You play {played}. Choose a hunter to wear their look.",
    "worn_look": "You play {played} with {worn}'s look. Choose {own} to get yours back.",
    "class:DarkSiren": "SIREN",
    "class:ExoSoldier": "EXO-SOLDIER",
    "class:Gravitar": "GRAVITAR",
    "class:Paladin": "FORGEKNIGHT",
    "class:RoboDealer": "ROGUE",
    "class:CorpoHacker": "HACKER",
    "hunter": "HUNTER",
    "keeps": "Same level, same backpack, same story. Each hunter keeps their skill tree.",
    "switch_nowhere": "Load a game, or select one at the title screen, to change its hunter.",
    "switch_busy": "Hunter Change is changing this game's hunter. Wait a few seconds, then open this window again.",
    "why:no_save": "This game's hunter cannot be changed: the mod does not find its save in the game's saves folder. "
                   "Your game is untouched and plays as before.",
    "why:two_saves": "This game's hunter cannot be changed: this game is in several save files, and the mod cannot "
                     "tell which one the game uses. Your game is untouched and plays as before. If one is an old copy "
                     "you no longer need, move it out of the game's saves folder to change hunters.",
    "why:saves_unsure": "This game's hunter cannot be changed for now: the mod could not read all of the game's saves; "
                        "another program, such as OneDrive, may have been using them. Your game is untouched. Open "
                        "this window again in a moment.",
    "why:save_damaged": "This game's hunter cannot be changed: its save could not be read whole, so the mod leaves it "
                        "untouched.",
    "why:unknown_hunter": "This game's hunter cannot be changed: the mod does not know this game's hunter yet. Your "
                          "game is untouched and plays as before.",
    "why:trees_unreadable": "No hunter can be changed: the mod's file of kept skill trees could not be read. Your "
                            "games are untouched and play as before.",
    "why:not_this_hunter": "This game's hunter cannot be changed: its save does not show the hunter you play. "
                           "Load it again.",
    "switch_in_game": "You play {current}. Choose a hunter to become them in this game.",
    "switch_at_title": "This game's hunter is {current}. Choose a hunter: the change is made at once.",
    "confirm": "You will become {new} in this game: same level, same backpack, same story. For each hunter, the first "
               "time you become them in this game, their skill tree starts over with all your points to spend; the "
               "next times, the points you already spent stay in place. {old}'s skill tree is kept for {old}'s return. "
               "{tree} The game saves your game and takes you back to the main menu. There, wait 5 seconds, click "
               "another game, then this one again: it will show {new}. Then Continue.",
    "tree_first": "{new} has no skill tree in this game yet: all your points will be free to spend.",
    "tree_back": "{new} gets their skill tree back, with the points you spent.",
    "leave_button": "RETURN TO MAIN MENU",
    "cancel_button": "CANCEL",
    "said:done": "{new} is now this game's hunter. Close this window, click another game, then this one again: it "
                 "will show {new}.",
    "said:no_save": "The mod did not find this game's save. Nothing was changed: your game plays as before.",
    "said:two_saves": "This game is in several save files, and the mod cannot tell which one the game uses. Nothing "
                      "was changed: your game plays as before. If one is an old copy you no longer need, move it out "
                      "of the game's saves folder to change hunters.",
    "said:saves_unsure": "The mod could not read all of the game's saves; another program, such as OneDrive, may have "
                         "been using them. Nothing was changed. Try again in a moment.",
    "said:save_damaged": "This game's save could not be read whole. Nothing was changed: the mod leaves it untouched.",
    "said:changed": "This game's save changed meanwhile. Nothing was changed. Try again.",
    "said:unsafe": "This game's skill tree could not be changed safely. Nothing was changed: the game plays as before.",
    "said:trees": "The mod's file of kept skill trees could not be read. Nothing was changed: the game plays as "
                  "before.",
    "said:not_written": "The save could not be written. Nothing was changed. Try again.",
    "said:unverified": "The save was written but could not be read back. Click another game, then this one again, to "
                       "see it.",
    "said:restore_failed": "The save could not be written or put back. Do not load this game and ask for help on the "
                           "mod's page: the mod kept a backup copy of it.",
    "said:no_return": "The game could not go back to the main menu. Nothing was changed. Try again.",
    "said:gave_up": "The game took too long to reach the main menu. Nothing was changed. Try again.",
    "said:loaded": "A game was loaded before the hunter could be changed. Nothing was changed. Try again.",
    "said:error": "Something went wrong while the save was being changed. Click another game, then this one again, "
                  "to see its hunter.",
}
