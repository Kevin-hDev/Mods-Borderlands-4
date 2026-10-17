"""French texts of Co-op Duel's window: the player is addressed as "tu", as in our other windows."""

from .panel_common_fr import TEXT as COMMON

TEXT = {
    **COMMON,
    "duel": "DUEL",
    "duel_how": "Tirez-vous dessus. Celui qui tombe reste au sol 3 secondes, puis se relève sur place, et la manche "
                "suivante commence. Les ennemis du coin vous attaquent tous les deux. Seul l'hôte a besoin de ce mod.",
    "start": "LANCER LE DUEL", "stop": "ARRÊTER LE DUEL",
    "host": "Hôte", "guest": "Invité",
    "banner_start": "DUEL", "banner_round": "MANCHE {round}", "banner_over": "FIN DU DUEL",
    "banner_refused": "CO-OP DUEL",
    "options": "OPTIONS", "ready_options": "Enregistré au fur et à mesure.",
    "open_key_label": "Ouvrir ce menu", "open_key_hint": "La touche qui ouvre Co-op Duel en jeu.",
    "duel_key_label": "Lancer ou arrêter le duel",
    "duel_key_hint": "La touche qui lance le duel, ou l'arrête, sans ouvrir ce menu.",
    "press_key": "APPUIE SUR UNE TOUCHE",
    "key_taken": "Cette touche sert déjà à l'autre raccourci : choisis-en une autre.",
    "ready_duel": "Mets-toi à côté de l'autre joueur, tous les deux à pied, puis appuie sur LANCER LE DUEL.",
    "ready_on": "Un duel est en cours. ARRÊTER LE DUEL le termine et remet tout le monde à la normale.",
    "start_off": "Co-op Duel est éteint. Ta partie n'est pas modifiée. Allume-le en bas à gauche, puis relance le "
                 "duel.",
    "start_already_on": "Un duel est déjà en cours. Ta partie n'est pas modifiée. Arrête-le avant d'en lancer un "
                        "autre.",
    "start_not_host": "Seul l'hôte de la partie peut lancer un duel. Ta partie n'est pas modifiée. Demande à l'hôte "
                      "de le lancer.",
    "start_no_character": "Pas de duel ici. Ta partie n'est pas modifiée. Charge une partie, puis relance le duel.",
    "start_in_vehicle": "Pas de duel en véhicule. Ta partie n'est pas modifiée. Descendez tous les deux, puis relance "
                        "le duel.",
    "start_no_guest": "Aucun autre joueur dans ta partie. Ta partie n'est pas modifiée. Invite un ami, puis relance "
                      "le duel.",
    "start_too_many": "Un duel se joue à deux seulement pour l'instant. Ta partie n'est pas modifiée. Joue-le avec un "
                      "seul invité.",
    "start_player_down": "Un joueur est à terre. Ta partie n'est pas modifiée. Attends que les deux soient relevés, "
                         "puis relance le duel.",
    "start_team_refused": "Le jeu a refusé le duel. Ta partie n'est pas modifiée. Réessaie ; la raison est dans "
                          "unrealsdk.log.",
    "start_refused": "Le duel n'a pas pu commencer. Ta partie n'est pas modifiée. Réessaie ; la raison est dans "
                     "unrealsdk.log.",
}

GROUPS = {"duel": "", "options": ""}

OPTIONS: dict = {}
