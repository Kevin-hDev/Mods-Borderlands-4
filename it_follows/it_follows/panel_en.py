"""It Follows' window in English, its first language: its pages, its run, its normal mode, its history, its welcome and
its result. The words are the sketches' (esquisses_menu, validated by Kevin), put in English; the normal mode's are
spec-mode-normal.md's (decision 80)."""

from .panel_common_en import TEXT as COMMON

TEXT = {
    **COMMON,
    "run": "HORDE MODE [BETA]", "normal": "NORMAL MODE", "history": "HISTORY", "options": "OPTIONS",
    "running_tag": "RUNNING",
    "run_settings": "RUN SETTINGS", "run_live": "RUN IN PROGRESS · {level}",
    "kills": "KILLS", "deaths": "DEATHS", "time": "TIME", "start": "START", "stop": "STOP",
    "caution": "Dozens of enemies, up to over a hundred depending on the level chosen, hunt you at once: this mode "
               "asks a lot of your PC. If the game slows down, lower Max enemies, choose a lower level, lower the "
               "game's graphics or close what runs in the background.",
    "locked": "Stop the run to change these settings.",
    "help_run_title": "HOW A RUN GOES",
    "help_run": "A run starts quietly: the enemies nearby start chasing you.\n\n"
                "If there are no enemies near you when the run starts, go and find them: otherwise, nothing "
                "happens.\n\n"
                "The more enemies you kill, the more of them there will be.\n\n"
                "Every 100 enemies killed, they also grow 1% stronger: the HARDCORE percent in the bar, back to 0 "
                "at each run.\n\n"
                "The types of enemies that follow you depend on the zone you play in and the ones you cross.\n\n"
                "To make the enemies vary, travel across the map.",
    "ready_run": "Ready: press START, the menu closes and the run begins.",
    "paused_run": "The game is paused while this menu is open.",
    "ready_history": "The last 20 runs, kept from one game launch to the next.",
    "ready_options": "Saved as you go.",
    "start_busy": "Your settings are being saved: press START again.",
    "start_off": "It Follows is off: switch it on, then press START.",
    "start_in_vehicle": "No run from a vehicle: get out of it, then press START.",
    "start_no_character": "No run here: load a game first.",
    "start_coop": "The Horde only works in solo games for now. Your game is not changed.",
    "start_already_running": "A run is already going.",
    "start_normal_on": "Stop the normal mode first, then press START.",
    "run_blocked": "The normal mode is on: stop it on its page to start a run.",
    "normal_settings": "NORMAL MODE", "normal_lead": "A first overhaul of the game's enemies, still evolving.",
    "normal_live": "NORMAL MODE ON · {level}",
    "normal_playing": "The enemies are stronger while you play. STOP gives them back as the game made them.",
    "normal_waiting": "It starts as soon as you are on foot in a loaded game.",
    "normal_locked": "Stop the normal mode to change these settings.",
    "normal_blocked": "A Horde run is going: stop it to turn the normal mode on.",
    "normal_level:Bandit": "More enemies, a little faster and tougher. They dodge faster and chase you farther. "
                           "A shield for those without one, if you want.",
    "normal_level:Senior": "Even more enemies, faster and tougher. Quicker dodges, longer chases. A shield for "
                           "every enemy without one.",
    "normal_level:Predator": "Even more enemies, very fast and very tough. Lightning dodges, and they chase you "
                             "much farther. A shield for every enemy without one, back 10 seconds after it breaks.",
    "hardcore_settings": "HARDCORE", "hardcore_lead": "A difficulty that rises slowly, all game long.",
    "hardcore_badge": "HARDCORE {percent}%", "hardcore_badge_paused": "HARDCORE {percent}% · PAUSED",
    "help_hardcore_title": "THE HARDCORE MODE",
    "help_hardcore": "In Borderlands 4, the enemies' level follows your hunter's: the game never really gets harder, "
                     "it even stays very easy.\n\n"
                     "The Hardcore mode changes that. It changes nothing when you switch it on. Then the enemies grow "
                     "1% stronger every 100 enemies killed, slowly and steadily, all game long. It adds to the level "
                     "chosen.\n\n"
                     "This one only works while the normal mode is on: the Horde mode has its own, which starts "
                     "again at each run. The percent reached shows at the top of the menu.\n\n"
                     "You can pause its progress to keep the difficulty that suits you, or switch the mode off at any "
                     "time: your progress is kept, and you find it again when you switch it back on.",
    "ready_normal": "Ready: press START, the menu closes and the normal mode begins.",
    "normal_waiting_notice": "The normal mode is on: it starts as soon as you are on foot in a loaded game.",
    "start_horde_running": "Stop the Horde run first, then press START.",
    "start_already_on": "The normal mode is already on.",
    "normal_start_failed": "The normal mode could not start. Your game is not changed. The reason is in "
                           "unrealsdk.log.",
    "normal_stop_unsaved": "The normal mode is stopped, but this could not be saved: it may turn on again at the next "
                           "launch.",
    "start_failed": "The run could not start. The reason is in unrealsdk.log. If enemies act strangely, quit to the "
                    "main menu and load your game again.",
    "start_refused": "The run could not start here. Your game is not changed. The reason is in unrealsdk.log.",
    "history_title": "LAST 20 RUNS", "history_empty": "No run yet: your runs will be listed here.",
    "col_when": "WHEN", "col_level": "LEVEL", "col_limit": "TIME LIMIT", "col_held": "HELD", "col_kills": "KILLS",
    "col_deaths": "DEATHS", "col_end": "END",
    "clock_time": "{hour:02d}:{minute:02d}", "today": "TODAY {time}", "yesterday": "YESTERDAY {time}",
    "day": "{month} {day} {time}", "months": "JAN FEB MAR APR MAY JUN JUL AUG SEP OCT NOV DEC",
    "end:time_up": "TIME UP", "end:stopped": "STOP", "end:left_game": "GAME LEFT", "end:mod_disabled": "MOD OFF",
    "end:interrupted": "STOPPED BY ITSELF",
    "level_number": "level {number}",
    "result:time_up": "TIME UP", "result:stopped": "RUN STOPPED", "result:interrupted": "RUN STOPPED BY ITSELF",
    "result_sentence:time_up": "You held {held} at {level}. The enemies stop coming.",
    "result_sentence:stopped": "You held {held} at {level}. The enemies stop coming.",
    "result_sentence:interrupted": "The run stopped by itself after {held} at {level}: the enemies stop coming. "
                                   "Your game is not changed. The reason is in unrealsdk.log.",
    "key_label": "Menu key", "press_key": "PRESS A KEY",
    "key_hint": "Opens this menu during the game; the game pauses while it is open. Click the key to change it.",
    "welcome_title": "WELCOME TO IT FOLLOWS",
    "welcome_lead": "It Follows holds two modes, independent of each other. The Horde mode: press START, every enemy "
                    "around you comes for you and follows you everywhere. Those you meet on the way join the horde, "
                    "and those you kill come back. Hold on as long as you can.",
    "welcome_film_title": "THE FILM IT FOLLOWS",
    "welcome_film": "Something walks towards you, never stopping, wherever you go.",
    "welcome_zombies_title": "CALL OF DUTY: BLACK OPS ZOMBIES",
    "welcome_zombies": "A horde that comes back without end and grows with the level. You kill, you run, you survive.",
    "welcome_next": "NEXT",
    "updates_title": "UPDATE {version}",
    "updates_count": "{page} / {pages}",
    "updates_next": "NEXT",
    "welcome_normal_lead": "The normal mode: play your game as usual. The enemies you meet are more numerous, faster "
                           "and tougher, dodge faster and chase you farther. It is made first for starting or "
                           "restarting the game from the beginning, a little like three levels of NG+, and still "
                           "works mid-game.",
    "welcome_levels_title": "THREE LEVELS",
    "welcome_levels": "Bandit, Senior and Predator, from a harder game to a much harder one.",
    "welcome_evolving_title": "STILL EVOLVING",
    "welcome_evolving": "A first overhaul of the game's enemies, which will keep evolving from one version to the "
                        "next.",
    "welcome_go": "LET'S GO",
}

# The names the choices' buttons write (panel_choices.label): a level by its place, never its number of enemies
# (decisions 53 and 70).
CHOICES = {"level:25": "Level 1", "level:40": "Level 2", "level:60": "Level 3", "level:80": "Level 4",
           "level:100": "Level 5"}
