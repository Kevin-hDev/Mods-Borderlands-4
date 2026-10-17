"""French texts of Co-op Duel's window: the player is addressed as "tu", as in our other windows."""

from .panel_common_fr import TEXT as COMMON

TEXT = {
    **COMMON,
    "duel": "DUEL",
    "duel_how": "Tirez-vous dessus. Celui qui tombe reste au sol, protégé, jusqu'à la fin de la manche, et un "
                "coéquipier peut le relever. La dernière équipe debout gagne la manche, puis tout le monde se relève "
                "sur place. À deux équipes, les ennemis du coin attaquent tout le monde. Seul l'hôte a besoin de ce "
                "mod.",
    "start": "LANCER LE DUEL", "stop": "ARRÊTER LE DUEL",
    "host": "Hôte",
    "banner_start": "DUEL", "banner_round": "MANCHE {round}", "banner_over": "FIN DU DUEL",
    "banner_refused": "CO-OP DUEL",
    "banner_draw": "NULLE", "team_name": "ÉQUIPE {team}", "player_fallback": "Joueur {number}",
    "teams": "ÉQUIPES", "teams_each": "CHACUN POUR SOI", "teams_vs": "CONTRE", "teams_one": "UNE SEULE ÉQUIPE",
    "ready_teams": "Choisis l'équipe de chaque joueur. Un joueur seul dans son équipe joue pour lui.",
    "teams_allies": "Trois équipes ou plus : les bandits ou les soldats de l'Ordre du coin peuvent se battre aux côtés "
                    "d'une équipe.",
    "teams_alone": "Aucun autre joueur dans ta partie. Invite un ami : il apparaîtra ici.",
    "teams_locked": "Un duel est en cours. Arrête-le dans la page DUEL avant de changer les équipes.",
    "teams_not_host": "Seul l'hôte de la partie range les équipes.",
    "options": "OPTIONS", "ready_options": "Enregistré au fur et à mesure.",
    "open_key_label": "Ouvrir ce menu", "open_key_hint": "La touche qui ouvre Co-op Duel en jeu.",
    "duel_key_label": "Lancer ou arrêter le duel",
    "duel_key_hint": "La touche qui lance le duel, ou l'arrête, sans ouvrir ce menu.",
    "press_key": "APPUIE SUR UNE TOUCHE",
    "key_taken": "Cette touche sert déjà à l'autre raccourci : choisis-en une autre.",
    "ready_duel": "Mets-toi près des autres joueurs, tout le monde à pied, puis appuie sur LANCER LE DUEL.",
    "ready_on": "Un duel est en cours. ARRÊTER LE DUEL le termine et remet tout le monde à la normale.",
    "start_off": "Co-op Duel est éteint. Ta partie n'est pas modifiée. Allume-le en bas à gauche, puis relance le "
                 "duel.",
    "start_already_on": "Un duel est déjà en cours. Ta partie n'est pas modifiée. Arrête-le avant d'en lancer un "
                        "autre.",
    "start_not_host": "Seul l'hôte de la partie peut lancer un duel. Ta partie n'est pas modifiée. Demande à l'hôte "
                      "de le lancer.",
    "start_no_character": "Pas de duel ici. Ta partie n'est pas modifiée. Charge une partie, puis relance le duel.",
    "start_in_vehicle": "Pas de duel en véhicule. Ta partie n'est pas modifiée. Descendez tous, puis relance le duel.",
    "start_player_away": "Un joueur n'a pas encore de personnage : il arrive ou réapparaît. Ta partie n'est pas "
                         "modifiée. Attends-le, puis relance le duel.",
    "start_one_team": "Tous les joueurs sont dans la même équipe. Ta partie n'est pas modifiée. Sépare-les dans la "
                      "page ÉQUIPES, puis relance le duel.",
    "start_no_guest": "Aucun autre joueur dans ta partie. Ta partie n'est pas modifiée. Invite un ami, puis relance "
                      "le duel.",
    "start_player_down": "Un joueur est à terre. Ta partie n'est pas modifiée. Attends que tout le monde soit relevé, "
                         "puis relance le duel.",
    "start_team_refused": "Le jeu a refusé le duel. Ta partie n'est pas modifiée. Réessaie ; la raison est dans "
                          "unrealsdk.log.",
    "start_refused": "Le duel n'a pas pu commencer. Ta partie n'est pas modifiée. Réessaie ; la raison est dans "
                     "unrealsdk.log.",
    "stop_player_joined": "Un joueur a rejoint la partie. Range-le dans une équipe dans la page ÉQUIPES, puis relance "
                          "le duel.",
    "stop_teams_left": "Il ne reste qu'une équipe. Sépare les joueurs dans la page ÉQUIPES, ou invite un ami, puis "
                       "lance un nouveau duel.",
}

GROUPS = {"duel": "", "teams": "", "options": ""}

OPTIONS: dict = {}
