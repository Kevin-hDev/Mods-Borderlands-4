"""French texts of Hunter Change's window. The class names are the game's own, read on its list of characters
(Kevin's capture, 2026-09-28)."""

from .panel_common_fr import TEXT as COMMON

TEXT = {
    **COMMON,
    "appearance": "APPARENCE",
    "applies": "S'applique tout de suite, pour cette partie.",
    "your_hunter": "TON CHASSEUR",
    "chosen": "CHOISI",
    "no_game": "Charge une partie pour choisir une apparence.",
    "own_look": "Tu joues {played}. Choisis un chasseur pour prendre son apparence.",
    "worn_look": "Tu joues {played}. Apparence portée : {worn}. Choisis {own} pour retrouver la tienne.",
    "class:DarkSiren": "SIRÈNE",
    "class:ExoSoldier": "EXOSOLDAT",
    "class:Gravitar": "GRAVITAR",
    # On one line it runs out of its card (essai 38): the break is written here, where it cannot depend on how the
    # game wraps one hyphenated word.
    "class:Paladin": "CHEVALIER-\nFORGERON",
    "class:RoboDealer": "ESCROC",
    "class:CorpoHacker": "HACKEUSE",
    "hunter": "CHASSEUR",
    "keeps": "Même niveau, même sac, même histoire. Chaque chasseur garde son arbre de compétences.",
    "switch_nowhere": "Charge une partie, ou sélectionne-la à l'écran titre, pour changer son chasseur.",
    "switch_busy": "Hunter Change est en train de changer le chasseur de cette partie. Attends quelques secondes, puis "
                   "rouvre cette fenêtre.",
    "why:no_save": "Le chasseur de cette partie ne peut pas être changé : le mod ne trouve pas sa sauvegarde dans le "
                   "dossier des sauvegardes du jeu. Ta partie n'est pas touchée et se joue comme avant.",
    "why:two_saves": "Le chasseur de cette partie ne peut pas être changé : cette partie est dans plusieurs fichiers "
                     "de sauvegarde, et le mod ne sait pas lequel le jeu utilise. Ta partie n'est pas touchée et se "
                     "joue comme avant. Si l'un est une ancienne copie dont tu n'as plus besoin, déplace-le hors du "
                     "dossier des sauvegardes du jeu pour pouvoir changer de chasseur.",
    "why:saves_unsure": "Le chasseur de cette partie ne peut pas être changé pour l'instant : le mod n'a pas pu lire "
                        "toutes les sauvegardes du jeu ; un autre programme, comme OneDrive, les utilisait peut-être. "
                        "Ta partie n'est pas touchée. Rouvre cette fenêtre dans un moment.",
    "why:save_damaged": "Le chasseur de cette partie ne peut pas être changé : sa sauvegarde n'a pas pu être lue en "
                        "entier, donc le mod n'y touche pas.",
    "why:unknown_hunter": "Le chasseur de cette partie ne peut pas être changé : le mod ne connaît pas encore le "
                          "chasseur de cette partie. Ta partie n'est pas touchée et se joue comme avant.",
    "why:trees_unreadable": "Aucun chasseur ne peut être changé : le fichier des arbres de compétences gardés par le "
                            "mod est illisible. Tes parties ne sont pas touchées et se jouent comme avant.",
    "why:not_this_hunter": "Le chasseur de cette partie ne peut pas être changé : sa sauvegarde ne montre pas le "
                           "chasseur que tu joues. Recharge-la.",
    "switch_in_game": "Tu joues {current}. Choisis un chasseur pour le devenir dans cette partie.",
    "switch_at_title": "Le chasseur de cette partie est {current}. Choisis un chasseur : le changement se fait tout de "
                       "suite.",
    "confirm": "Tu vas devenir {new} dans cette partie : même niveau, même sac, même histoire. Pour chaque chasseur, "
               "la première fois que tu le deviens dans cette partie, son arbre de compétences est remis à zéro et "
               "tous tes points sont à placer ; les fois suivantes, les points que tu lui as déjà placés restent en "
               "place. {old} garde le sien pour son retour. {tree} Le jeu enregistre ta partie et te ramène au menu "
               "principal. Là, attends 5 secondes, clique sur une autre partie, puis de nouveau sur celle-ci : elle "
               "affichera {new}. Puis Continuer.",
    "tree_first": "{new} n'a pas encore d'arbre de compétences dans cette partie : tous tes points seront à placer.",
    "tree_back": "{new} retrouve le sien, avec les points que tu lui avais placés.",
    "leave_button": "REVENIR AU MENU PRINCIPAL",
    "cancel_button": "ANNULER",
    "said:done": "{new} est maintenant le chasseur de cette partie. Ferme cette fenêtre, clique sur une autre partie, "
                 "puis de nouveau sur celle-ci : elle affichera {new}.",
    "said:no_save": "Le mod n'a pas trouvé la sauvegarde de cette partie. Rien n'a changé : ta partie se joue comme "
                    "avant.",
    "said:two_saves": "Cette partie est dans plusieurs fichiers de sauvegarde, et le mod ne sait pas lequel le jeu "
                      "utilise. Rien n'a changé : ta partie se joue comme avant. Si l'un est une ancienne copie dont tu "
                      "n'as plus besoin, déplace-le hors du dossier des sauvegardes du jeu pour pouvoir changer de "
                      "chasseur.",
    "said:saves_unsure": "Le mod n'a pas pu lire toutes les sauvegardes du jeu ; un autre programme, comme OneDrive, "
                         "les utilisait peut-être. Rien n'a changé. Réessaie dans un moment.",
    "said:save_damaged": "La sauvegarde de cette partie n'a pas pu être lue en entier. Rien n'a changé : le mod n'y "
                         "touche pas.",
    "said:changed": "La sauvegarde de cette partie a changé entre-temps. Rien n'a changé. Réessaie.",
    "said:unsafe": "L'arbre de compétences de cette partie n'a pas pu être changé sans risque. Rien n'a changé : la "
                   "partie se joue comme avant.",
    "said:trees": "Le fichier des arbres de compétences gardés par le mod est illisible. Rien n'a changé : la partie "
                  "se joue comme avant.",
    "said:not_written": "La sauvegarde n'a pas pu être écrite. Rien n'a changé. Réessaie.",
    "said:unverified": "La sauvegarde est écrite mais n'a pas pu être relue. Clique sur une autre partie, puis de "
                       "nouveau sur celle-ci, pour la voir.",
    "said:restore_failed": "La sauvegarde n'a pas pu être écrite ni remise. Ne charge pas cette partie et demande de "
                           "l'aide sur la page du mod : le mod en a gardé une copie de sécurité.",
    "said:no_return": "Le jeu n'a pas pu revenir au menu principal. Rien n'a changé. Réessaie.",
    "said:gave_up": "Le jeu a mis trop de temps à revenir au menu principal. Rien n'a changé. Réessaie.",
    "said:loaded": "Une partie a été chargée avant que le chasseur puisse être changé. Rien n'a changé. Réessaie.",
    "said:error": "Un problème est survenu pendant le changement de la sauvegarde. Clique sur une autre partie, puis "
                  "de nouveau sur celle-ci, pour voir son chasseur.",
}

GROUPS = {
    "appearance": "Prends l'apparence d'un autre chasseur. Tu gardes ton niveau et ton arbre de compétences.",
    "hunter": "Deviens un autre chasseur dans cette partie.",
}

OPTIONS: dict = {}
