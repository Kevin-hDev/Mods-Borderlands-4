"""It Follows' window in French, its second language: the sketches' words (esquisses_menu, validated by Kevin), and the
normal mode's (spec-mode-normal.md, decision 80)."""

from .panel_common_fr import TEXT as COMMON
from .panel_companion_texts import FR as COMPANIONS, OPTIONS_FR

TEXT = {
    **COMMON,
    **COMPANIONS,
    "run": "MODE HORDE [BETA]", "normal": "MODE NORMAL", "history": "HISTORIQUE", "options": "OPTIONS",
    "running_tag": "EN COURS",
    "run_settings": "RÉGLAGES DU RUN", "run_live": "RUN EN COURS · {level}",
    "kills": "TUÉS", "deaths": "MORTS", "time": "TEMPS", "start": "START", "stop": "STOP",
    "caution": "Des dizaines d'ennemis, jusqu'à plus d'une centaine selon le niveau choisi, te chassent en même "
               "temps : ce mode demande beaucoup à ton PC. Si le jeu ralentit, baisse « Ennemis maximum », choisis "
               "un niveau plus bas, baisse les graphismes du jeu ou ferme ce qui tourne en arrière-plan.",
    "locked": "Arrête le run pour changer ces réglages.",
    "help_run_title": "COMMENT SE DÉROULE UN RUN",
    "help_run": "Un run démarre tranquillement : les ennemis aux alentours commencent à te poursuivre.\n\n"
                "S'il n'y a pas d'ennemis près de toi au lancement du run, va les chercher : sinon, il ne se passe "
                "rien.\n\n"
                "Plus tu tues d'ennemis, plus ils seront nombreux.\n\n"
                "Tous les 100 ennemis tués, ils se renforcent aussi de 1 % : c'est le pourcentage HARDCORE de la "
                "barre, remis à 0 à chaque run.\n\n"
                "Les types d'ennemis qui te suivent dépendent de la zone où tu joues et de celles que tu traverses."
                "\n\n"
                "Pour que les ennemis varient, déplace-toi à travers la carte.",
    "ready_run": "Prêt : appuie sur START, le menu se ferme et le run commence.",
    "paused_run": "Le jeu est en pause tant que ce menu est ouvert.",
    "ready_history": "Les 20 derniers runs, gardés d'un lancement du jeu à l'autre.",
    "ready_options": "Enregistré au fur et à mesure.",
    "start_busy": "Tes réglages s'enregistrent : appuie de nouveau sur START.",
    "start_off": "It Follows est désactivé : active-le, puis appuie sur START.",
    "start_in_vehicle": "Pas de run en véhicule : descends-en, puis appuie sur START.",
    "start_no_character": "Pas de run ici : charge d'abord une partie.",
    "start_coop": "La Horde ne marche qu'en partie solo pour l'instant. Ta partie n'est pas modifiée.",
    "start_already_running": "Un run est déjà en cours.",
    "start_normal_on": "Arrête d'abord le mode normal, puis appuie sur START.",
    "run_blocked": "Le mode normal est en cours : arrête-le sur sa page pour lancer un run.",
    "normal_settings": "MODE NORMAL", "normal_lead": "Un début de refonte des ennemis du jeu, qui évoluera encore.",
    "normal_live": "MODE NORMAL EN COURS · {level}",
    "normal_playing": "Les ennemis sont renforcés pendant que tu joues. STOP les rend tels que le jeu les a faits.",
    "normal_waiting": "Il démarre dès que tu es à pied dans une partie chargée.",
    "normal_locked": "Arrête le mode normal pour changer ces réglages.",
    "normal_blocked": "Un run de la Horde est en cours : arrête-le pour lancer le mode normal.",
    "normal_level:Bandit": "Plus d'ennemis, un peu plus rapides et plus résistants. Ils esquivent plus vite et te "
                           "poursuivent plus loin. Un bouclier pour ceux qui n'en ont pas, si tu veux.",
    "normal_level:Senior": "Encore plus d'ennemis, plus rapides et plus résistants. Des esquives plus vives, des "
                           "poursuites plus longues. Un bouclier pour chaque ennemi qui n'en a pas.",
    "normal_level:Predator": "Encore plus d'ennemis, très rapides et très résistants. Des esquives fulgurantes, et "
                             "ils te poursuivent bien plus loin. Un bouclier pour chaque ennemi qui n'en a pas, qui "
                             "revient 10 secondes après avoir été cassé.",
    "normal_level:God": "Autant d'ennemis qu'en Predator, bien plus résistants mais un peu moins rapides. Un bouclier "
                        "pour chaque ennemi qui n'en a pas, qui revient 10 secondes après avoir été cassé. Plus de "
                        "munitions, d'argent et d'expérience. Pensé pour jouer avec tes compagnons.",
    "hardcore_settings": "HARDCORE", "hardcore_lead": "Une difficulté qui monte lentement, tout au long du jeu.",
    "hardcore_badge": "HARDCORE {percent} %", "hardcore_badge_paused": "HARDCORE {percent} % · EN PAUSE",
    "help_hardcore_title": "LE MODE HARDCORE",
    "help_hardcore": "Dans Borderlands 4, le niveau des ennemis suit celui de ton chasseur : le jeu ne devient jamais "
                     "vraiment plus difficile, il reste même très facile.\n\n"
                     "Le mode Hardcore change ça. Il ne modifie rien quand tu l'actives. Ensuite, les ennemis se "
                     "renforcent de 1 % tous les 100 ennemis tués, lentement et régulièrement, tout au long du jeu. Ça "
                     "s'ajoute au niveau choisi.\n\n"
                     "Celui-ci agit seulement pendant que le mode normal est lancé : le mode Horde a le sien, qui "
                     "repart de 0 à chaque run. Le pourcentage atteint s'affiche en haut du menu.\n\n"
                     "Tu peux mettre la progression en pause pour garder la difficulté qui te convient, ou désactiver "
                     "le mode à tout moment : ta progression est gardée, et tu la retrouves en le réactivant.",
    "ready_normal": "Prêt : appuie sur START, le menu se ferme et le mode normal commence.",
    "normal_waiting_notice": "Le mode normal est en cours : il démarre dès que tu es à pied dans une partie chargée.",
    "start_horde_running": "Arrête d'abord le run de la Horde, puis appuie sur START.",
    "start_already_on": "Le mode normal est déjà en cours.",
    "normal_start_failed": "Le mode normal n'a pas pu démarrer. Ta partie n'est pas modifiée. La raison est dans "
                           "unrealsdk.log.",
    "normal_stop_unsaved": "Le mode normal est arrêté, mais ce choix n'a pas pu être enregistré : il peut se rallumer "
                           "au prochain lancement.",
    "start_failed": "Le run n'a pas pu démarrer. La raison est dans unrealsdk.log. Si des ennemis se comportent "
                    "bizarrement, quitte vers le menu principal et recharge ta partie.",
    "start_refused": "Le run n'a pas pu démarrer ici. Ta partie n'est pas modifiée. La raison est dans unrealsdk.log.",
    "start_place_caption": "LE LIEU", "start_map_caption": "SUR LA CARTE",
    "start_choose": "CHOISIR", "start_chosen": "CHOISI", "start_back": "RETOUR",
    "colour_preview": "APERÇU", "colour_back": "RETOUR",
    "help_start_title": "POINT DE DÉPART",
    "help_start": "Choisis où commence ton run de la Horde.\n\n"
                  "Allume Point de départ, puis ouvre l'onglet d'un lieu à côté de RÉGLAGES DU RUN : sa photo, et où "
                  "il se trouve sur la carte. Appuie sur CHOISIR.\n\n"
                  "Au START, l'écran devient noir le temps du voyage et du chargement du lieu, puis le run commence "
                  "dès que l'image revient.\n\n"
                  "Éteint, le run commence là où tu te tiens, comme avant. Ton dernier choix est gardé.",
    "locked_trip": "En route vers le point de départ : le run commence à l'arrivée.",
    "start_not_open_world": "Pas de point de départ d'ici : retourne dans le monde ouvert, puis appuie sur START.",
    "start_trip_going": "Tu es déjà en route vers le point de départ.",
    "start_move_failed": "Le jeu a refusé le voyage : tu n'as pas bougé, et le run n'a pas commencé. Appuie de "
                         "nouveau sur START.",
    "start_no_floor": "Le point de départ n'a pas chargé à temps : tu as été ramené là où tu étais, et le run n'a "
                      "pas commencé. Appuie de nouveau sur START.",
    "start_character_gone": "Le voyage s'est arrêté en route (un changement de carte) : le run n'a pas commencé.",
    "start_hold_failed": "Le voyage s'est arrêté sur une erreur : tu as été ramené là où tu étais, et le run n'a "
                         "pas commencé. La raison est dans unrealsdk.log.",
    "start_arrival_coop": "Quelqu'un a rejoint ta partie pendant le voyage : la Horde ne marche qu'en partie solo pour "
                          "l'instant, et le run n'a pas commencé. Tu restes au point de départ.",
    "start_arrival_refused": "Tu es au point de départ, mais le run n'a pas pu y commencer. Appuie de nouveau sur "
                             "START ; la raison est dans unrealsdk.log.",
    "history_title": "20 DERNIERS RUNS", "history_empty": "Aucun run pour l'instant : tes runs s'afficheront ici.",
    "col_when": "QUAND", "col_level": "NIVEAU", "col_limit": "DURÉE", "col_held": "TENU", "col_kills": "TUÉS",
    "col_deaths": "MORTS", "col_end": "FIN",
    "clock_time": "{hour} H {minute:02d}", "today": "AUJOURD'HUI {time}", "yesterday": "HIER {time}",
    "day": "{day} {month} {time}", "months": "JANV. FÉVR. MARS AVR. MAI JUIN JUIL. AOÛT SEPT. OCT. NOV. DÉC.",
    "end:time_up": "TEMPS ÉCOULÉ", "end:stopped": "STOP", "end:left_game": "PARTIE QUITTÉE",
    "end:mod_disabled": "MOD DÉSACTIVÉ", "end:interrupted": "ARRÊTÉ SEUL",
    "level_number": "niveau {number}",
    "result:time_up": "TEMPS ÉCOULÉ", "result:stopped": "RUN ARRÊTÉ", "result:interrupted": "RUN ARRÊTÉ SEUL",
    "result_sentence:time_up": "Tu as tenu {held} au {level}. Les ennemis arrêtent de venir.",
    "result_sentence:stopped": "Tu as tenu {held} au {level}. Les ennemis arrêtent de venir.",
    "result_sentence:interrupted": "Le run s'est arrêté seul après {held} au {level} : les ennemis arrêtent de "
                                   "venir. Ta partie n'est pas modifiée. La raison est dans unrealsdk.log.",
    "key_label": "Touche du menu", "press_key": "APPUIE SUR UNE TOUCHE",
    "key_hint": "Ouvre ce menu pendant le jeu ; le jeu se met en pause tant qu'il est ouvert. Clique sur la touche "
                "pour la changer.",
    "welcome_title": "BIENVENUE DANS IT FOLLOWS",
    "welcome_lead": "It Follows réunit deux modes, indépendants l'un de l'autre. Le mode Horde : appuie sur START, "
                    "tous les ennemis autour de toi viennent vers toi et te suivent partout. Ceux que tu croises en "
                    "chemin rejoignent la horde, et ceux que tu tues reviennent. Tiens aussi longtemps que tu peux.",
    "welcome_film_title": "LE FILM IT FOLLOWS",
    "welcome_film": "Quelque chose marche vers toi, sans jamais s'arrêter, où que tu ailles.",
    "welcome_zombies_title": "CALL OF DUTY : BLACK OPS ZOMBIES",
    "welcome_zombies": "Une horde qui revient sans fin et grossit avec le niveau. Tu tues, tu cours, tu survis.",
    "welcome_next": "SUIVANT",
    "updates_title": "MISE À JOUR {version}",
    "updates_count": "{page} / {pages}",
    "updates_next": "SUIVANT",
    "welcome_normal_lead": "Le mode normal : joue ta partie comme d'habitude. Les ennemis que tu croises sont plus "
                           "nombreux, plus rapides et plus résistants, esquivent plus vite et te poursuivent plus "
                           "loin. Il est pensé d'abord pour commencer ou recommencer le jeu depuis le début, un peu "
                           "comme quatre niveaux de NG+, et reste utilisable en cours de partie.",
    "welcome_levels_title": "QUATRE NIVEAUX",
    "welcome_levels": "Bandit, Senior, Predator et God, d'une partie plus dure à une partie bien plus dure.",
    "welcome_evolving_title": "EN ÉVOLUTION",
    "welcome_evolving": "Un début de refonte des ennemis du jeu, qui évoluera encore d'une version à l'autre.",
    "welcome_go": "C'EST PARTI",
}

GROUPS = {"run": "", "normal": "", "companions": "", "history": "", "options": ""}

OPTIONS = {
    **OPTIONS_FR,
    "start_point": ("Point de départ", "Lance le run depuis un lieu de la carte choisi dans les onglets en haut, "
                                       "au lieu de là où tu te tiens."),
    "level": ("Niveau", "Plus le niveau est haut, plus il y a d'ennemis autour de toi."),
    "speed": ("Vitesse des ennemis", "La vitesse de course des ennemis qui te chassent."),
    "buff": ("Buff", "BUFF : les ennemis ont plus de vie et tu reçois plus de dégâts. BUFF+ : encore plus."),
    "duration": ("Durée", "Le run s'arrête tout seul à la fin. Illimitée : jusqu'à STOP."),
    "max_enemies": ("Ennemis maximum", "Le plus d'ennemis qui te chassent en même temps. Moins : ton PC est moins "
                                       "chargé."),
    "manage_far": ("Gérer les ennemis éloignés", "Un ennemi resté loin derrière toi est ramené derrière toi. "
                                                 "Toujours activé pour l'instant : ce réglage sera revu dans une "
                                                 "prochaine version."),
    "bar": ("Barre en jeu", "Tes tués, tes morts et le temps, en haut à gauche de l'écran pendant un run."),
    "bar_size": ("Taille de la barre", "Sa taille à l'écran."),
    "lost_loot": ("Butin perdu : 400 objets", "La machine du butin perdu garde jusqu'à 400 objets au lieu de la "
                                              "limite du jeu. Désactivé : les objets qu'elle contient y restent."),
    "stretch_1610": ("Résolution 16:10", "Joue en plein écran dans la résolution 16:10 de la hauteur de ton écran, "
                                         "2304×1440 sur un écran 1440p ; sur un écran 16:9, l'image est étirée. "
                                         "Désactivée : ta résolution et ton mode d'affichage reviennent."),
    "saturated_colours": ("Profil de couleurs", "Des couleurs plus vives dans tout le jeu."),
    "normal_level": ("Niveau", "La difficulté donnée aux ennemis du jeu."),
    "normal_allies": ("Ennemis alliés", "Tous les ennemis dans une même équipe : ils ne se battent plus entre eux."),
    "normal_fast_dodges": ("Esquives accélérées",
                           "Les ennemis esquivent plus vite que dans le jeu. Désactivé : la vitesse d'esquive du jeu."),
    "normal_speed": ("Vitesse des ennemis",
                     "Réduite : en Senior, Predator et God, les ennemis courent, esquivent et frappent moins vite."),
    "normal_shields": ("Boucliers", "Les ennemis sans bouclier en reçoivent un, de 40 % de leur vie. Une fois cassé, "
                                    "il ne revient pas."),
    "normal_no_staggers": ("Sans sursaut", "En Predator et God : les ennemis ne sursautent plus et ne tombent plus "
                                           "sous tes tirs."),
    "normal_hardcore": ("Hardcore", "Les ennemis se renforcent à mesure que tu tues, lentement, tout au long du jeu."),
    "normal_hardcore_progress": ("Progression", "Désactivée : la difficulté atteinte reste telle quelle, sans monter."),
}

CHOICES = {"level:25": "Niveau 1", "level:40": "Niveau 2", "level:60": "Niveau 3", "level:80": "Niveau 4",
           "level:100": "Niveau 5", "Normal": "Normale", "+10%": "+10 %", "+20%": "+20 %", "+30%": "+30 %",
           "+40%": "+40 %", "+50%": "+50 %", "Unlimited": "Illimitée", "Small": "Petite", "Medium": "Moyenne",
           "Large": "Grande", "buff:Normal": "Normal", "normal_speed:Increased": "Augmentée",
           "normal_speed:Reduced": "Réduite", "colour_profile:Profile 1": "Profil 1",
           "colour_profile:Profile 2": "Profil 2", "colour_profile:Profile 3": "Profil 3"}
