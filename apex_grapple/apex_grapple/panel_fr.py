"""French labels and explanations for all gameplay and interface controls."""

TEXT = {
    "shot": "LE TIR", "pull": "LA TRACTION", "release": "DÉCROCHAGE", "look": "APPARENCE", "controls": "COMMANDES",
    "close": "FERMER", "restore": "RÉGLAGES D’ORIGINE", "undo": "ANNULER LE RESET",
    "enabled": "ACTIVÉ", "disabled": "DÉSACTIVÉ", "on": "OUI", "off": "NON",
    "by": "PAR", "version": "VERSION", "settings": "RÉGLAGES",
    "ready": "Sauvegarde automatique. Fermer revient à la liste des mods.",
    "saved": "Enregistré.", "failed": "Impossible d’enregistrer les réglages. Réessaie.",
    "rollback_abandoned": "Changement annulé. Le rétablissement n’a pas été confirmé ; relance le jeu avant de changer les réglages.",
    "toggle_failed": "Impossible d’activer ou de désactiver le mod. Rien n’a changé. La raison est dans unrealsdk.log.",
    # The update notes' pop-up (panel_updates.py).
    "updates_title": "MISE À JOUR {version}", "updates_count": "{page} / {pages}", "updates_next": "SUIVANT",
    "refused": "Attribution refusée. Cette touche est réservée ou déjà utilisée.",
    "restored": "Réglages d’origine restaurés. Tu peux annuler cette restauration.",
    "undone": "Réglages précédents rétablis.",
    "controls_intro": "Choisis un emplacement, puis appuie sur une touche clavier, souris ou manette. Les choix complets sont enregistrés automatiquement.",
    "two": "Deux touches à maintenir ensemble", "first": "1. CHOISIR UNE TOUCHE",
    "second": "2. CHOISIR LA DEUXIÈME TOUCHE", "listening": "APPUIE SUR TA TOUCHE",
    "reset_controls": "TOUCHES D’ORIGINE", "one_hint": "Choisis une touche. Elle sera enregistrée immédiatement.",
    "two_hint": "Choisis deux touches du même périphérique. Maintiens-les ensemble pour lancer le grappin.",
    "escape_hint": "Échap annule la saisie. La touche console est réservée. Chaque touche garde son action normale lorsqu’elle est pressée seule.",
    "keyboard": "Clavier / souris", "gamepad": "Manette", "game_controls": "Commandes du jeu",
    "invalid_keys": "Non enregistré. Choisis des touches différentes du même périphérique. Échap et la touche console sont réservées.",
    "controls_saved": "Commandes enregistrées.", "controls_reset": "Commandes du grappin restaurées.",
    "current_controls": "Touches actuelles",
    "controller_icons": "ICÔNES MANETTE", "PS5": "PLAYSTATION", "XSX": "XBOX",
    "game_controls_pending": "Commandes du jeu (disponibles en partie)",
    "reserved_key": "Non enregistré : cette touche est réservée à la console ou à l’annulation. Commandes précédentes conservées.",
    "theme": "THÈME :", "theme:EMBER": "BRAISE", "theme:DARK": "SOMBRE", "theme:LIGHT": "CLAIR", "theme:BL4": "BL4",
    "theme_later": "Thème enregistré. Il s’affichera à la prochaine ouverture du menu.",
    "window_size": "FENÊTRE :", "window_size:LARGE": "GRANDE", "window_size:FULL": "PLEIN ÉCRAN",
    "window_size:NORMAL": "NORMALE",
    "window_size_later": "Taille de la fenêtre enregistrée. Elle s’affichera à la prochaine ouverture du menu.",
    "look_missing": "Le pistolet grappin ne peut pas s’afficher : ses fichiers manquent ou ne vont plus avec cette "
                    "version du jeu. Ta partie n’est pas touchée et le grappin garde l’apparence classique. Installe "
                    "les fichiers du pistolet grappin, puis relance le jeu.",
    "look_failed": "Le pistolet grappin s’est arrêté après une erreur. Ta partie n’est pas touchée et le grappin garde "
                   "l’apparence classique jusqu’au prochain lancement du jeu. La raison est dans unrealsdk.log.",
    "look_unknown_hunter": "Ce chasseur n’a pas encore le pistolet grappin : le grappin garde l’apparence "
                           "classique.",
}
OPTIONS = {
    "grapple_range": ("Portée", "Distance max. du crochet. 3000 = 30 mètres."),
    "hook_speed": ("Vitesse du crochet", "Vitesse du crochet jusqu'à sa cible."),
    "melee_wins": ("Priorité au corps à corps", "Sur un ennemi, la touche frappe au lieu de lancer le grappin."),
    "stamina_cost": ("Coût en endurance", "Part de la barre d'endurance dépensée par tir. 33 = trois tirs, 0 = gratuit."),
    "punch_range": ("Portée du corps à corps", "Un ennemi plus proche que cette distance reçoit un coup de poing."),
    "keyboard_hold": ("Clavier : maintenir pour le grappin", "Maintenir la touche lance le grappin ; un appui bref sur la touche du corps à corps frappe."),
    "controller_hold": ("Manette : maintenir pour le grappin", "Maintenir le bouton lance le grappin ; un appui bref sur le bouton du corps à corps frappe."),
    "hold_time": ("Durée du maintien", "Temps à maintenir, en secondes."),
    "keep_game_grapple": ("Garder le grappin du jeu", "Les points d’accroche du jeu gardent le grappin du jeu."),
    "show_rope": ("Afficher la corde", "Affiche la corde et l’animation du bras."),
    "pull_strength": ("Force de traction", "Force avec laquelle la corde te tire."),
    "pull_speed_cap": ("Vitesse max. de traction", "Vitesse max. donnée par la corde. Ton élan s’y ajoute."),
    "rope_carry": ("Portage par la corde", "Part du poids portée par la corde : à 100 %, elle te porte ; à 0 %, la gravité agit pendant toute la traction."),
    "steer_strength": ("Force de direction", "À quel point le stick courbe ta trajectoire."),
    "steer_speed_cap": ("Vitesse max. de direction", "Vitesse latérale maximale ajoutée par le stick pendant la traction."),
    "release_on_key_up": ("Maintenir pour continuer à tirer", "Relâcher la touche lâche le grappin. Un appui bref tire jusqu’au bout."),
    "arrival_distance": ("Distance d’arrivée", "La traction s’arrête à cette distance de l’accroche."),
    "longest_pull": ("Durée max. de traction", "En secondes. 0 = sans limite."),
    "takeoff_lift": ("Élan au décollage", "Petit saut au départ depuis le sol. À 0, tu pars au ras du sol."),
    "ground_grace": ("Temps de décollage", "Le sol est ignoré ce temps-là au départ, pour décoller."),
    "release_on_landing": ("Lâcher à l’atterrissage", "Toucher le sol met fin à la traction."),
    "block_jump": ("Garder le saut en se détachant", "Sauter pour lâcher le grappin ne consomme pas de saut."),
    "look": ("Apparence", "Pistolet grappin : notre pistolet, notre corde et notre crochet. Classique : le geste et la "
                          "corde du jeu."),
    "rope_look": ("Corde", "Fil : un fil de lumière enroulé autour. Cœur : la lumière entre les brins. Lueur : un halo "
                           "autour."),
    "rope_thickness": ("Épaisseur", "L’épaisseur de la corde."),
    "glow_face": ("Face de la lueur", "Avec la lueur, à quel point la corde elle-même s’allume."),
    "rope_light": ("Lumière", "La force de la lumière de la corde."),
    "rope_colour": ("Couleur de la lumière", "La couleur de la lumière de la corde."),
    "rope_movement": ("Mouvement de la corde", "Combien la corde pend et ondule quand le crochet part et revient."),
    "hook_size": ("Taille du crochet", "La taille du crochet planté dans le mur."),
    "holster": ("Étui en troisième personne", "En troisième personne, le chasseur porte l’étui du pistolet "
                                             "grappin à la hanche."),
    "game_rope_colour": ("Couleur de la corde du jeu", "La couleur de la corde du jeu, avec l’apparence "
                                                       "classique."),
}
GROUPS = {
    "shot": "Portée, vitesse du crochet et corps à corps.",
    "pull": "Force de la corde, vitesse et contrôle de la trajectoire.",
    "release": "Ce qui termine la traction. La vitesse atteinte est conservée.",
    "look": "Ce que tu vois quand tu tires : le pistolet, la corde et le crochet.",
}
# The words agree with their row: MOYENNE thickness and light, MOYEN movement and size (Kevin, 2026-10-14, sketch A).
CHOICES = {
    "look:GRAPPLE_GUN": "Pistolet grappin", "look:CLASSIC": "Classique",
    "rope_look:A": "Fil", "rope_look:B": "Cœur", "rope_look:C": "Lueur",
    "rope_thickness:K": "Fine", "rope_thickness:L": "Moyenne", "rope_thickness:M": "Épaisse",
    "rope_light:1": "Faible", "rope_light:2": "Moyenne", "rope_light:3": "Forte",
    "rope_movement:G": "Léger", "rope_movement:H": "Moyen", "rope_movement:I": "Fort",
    "hook_size:A": "Petit", "hook_size:B": "Moyen", "hook_size:C": "Grand",
    "holster:WITH": "Avec", "holster:WITHOUT": "Sans",
    "glow_face:D": "Éteinte", "glow_face:E": "Légère", "glow_face:F": "Forte",
    "rope_colour:ORANGE": "Orange", "rope_colour:RED": "Rouge", "rope_colour:PURPLE": "Violet",
    "rope_colour:WHITE": "Blanc", "rope_colour:BLUE": "Bleu", "rope_colour:TURQUOISE": "Turquoise",
    "rope_colour:YELLOW": "Jaune", "rope_colour:GOLD": "Doré", "rope_colour:GREEN": "Vert",
    "game_rope_colour:ORANGE": "Orange", "game_rope_colour:RED": "Rouge", "game_rope_colour:PURPLE": "Violet",
    "game_rope_colour:WHITE": "Blanc", "game_rope_colour:BLUE": "Bleu", "game_rope_colour:TURQUOISE": "Turquoise",
    "game_rope_colour:YELLOW": "Jaune", "game_rope_colour:GOLD": "Doré", "game_rope_colour:GREEN": "Vert",
}
