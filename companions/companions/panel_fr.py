"""Companions' window in French: sketch A's words (esquisses_mod_companions, decision 68 of docs/renforts), the
cards' and the keys' as It Follows says them."""

from .panel_common_fr import TEXT as COMMON

TEXT = {
    **COMMON,
    "hunters": "CHASSEURS DE L'ARCHE", "allies": "ALLIÉS", "team_settings": "RÉGLAGES DE L'ÉQUIPE",
    "options": "OPTIONS",
    "team_count": "ÉQUIPE {count} / {most}",
    "team_none": "Aucun compagnon pour l'instant : choisis-en un pour l'ajouter à l'équipe.",
    "outfit": "TENUE", "outfit:own": "DE BASE", "outfit:player": "TES COULEURS",
    "team_launch": "LANCER L'ÉQUIPE", "team_stop": "ARRÊTER L'ÉQUIPE",
    "cards_locked": "Arrête l'équipe pour la changer.",
    "settings_locked": "Arrête l'équipe pour changer ses réglages : elle garde ceux de son lancement.",
    "team_elsewhere": "It Follows contrôle les compagnons. Utilise son menu.",
    "team_outdated": "Ta version d'It Follows est trop ancienne pour partager les compagnons, même désactivée : "
                     "mets-la à jour, puis relance le jeu.",
    "team_mismatch": "It Follows et Companions ne sont pas à des versions compatibles, aucune équipe ne part : "
                     "mets les deux à jour, puis relance le jeu.",
    "ready_cards": "Clique sur un compagnon pour l'ajouter à l'équipe, puis LANCER L'ÉQUIPE.",
    "team_on_notice": "Ton équipe te suit. Arrête-la ici pour la changer.",
    "ready_settings": "Les réglages de l'équipe valent pour tous tes compagnons.",
    "team_full": "L'équipe est complète : {most} compagnons au plus.",
    "team_empty": "Ajoute d'abord au moins un compagnon.",
    "team_busy": "Tes choix sont en cours d'enregistrement : relance l'équipe.",
    "team_off": "Companions est désactivé : active-le en bas à gauche, puis lance l'équipe.",
    "team_not_started": "L'équipe n'a pas démarré. La raison est dans unrealsdk.log.",
    "team_already_on": "L'équipe est déjà lancée.",
    "team_main_menu": "Charge d'abord une partie, puis lance l'équipe.",
    "team_stopped": "L'équipe est arrêtée : tes compagnons ne te suivent plus.",
    "key_label": "Touche du menu", "press_key": "APPUIE SUR UNE TOUCHE", "no_key": "AUCUNE",
    "key_hint": "Ouvre ce menu pendant le jeu ; le jeu se met en pause tant qu'il est ouvert, sauf en coop. Clique "
                "sur la case pour choisir une touche.",
    "team_key_label": "Touche de l'équipe",
    "team_key_hint": "Lance ton équipe, ou l'arrête, pendant que tu joues. Clique sur la touche pour la changer.",
    "key_taken": "Cette touche est déjà l'autre touche de Companions : choisis-en une autre.",
    "value_times": "×{value}", "value_percent": "{value} %", "value_bonus": "+{value} %", "value_seconds": "{value} s",
    "value_never": "JAMAIS",
}

GROUPS = {"hunters": "Les chasseurs de l'Arche se battent avec leurs armes seulement, sans leurs compétences.",
          "allies": "", "settings": "Pour tous tes compagnons."}

OPTIONS = {
    "health_times": ("Vie", "Un multiple de la vie de ton chasseur."),
    "shield_percent": ("Bouclier", "Une part de leur vie. 0 % : pas de bouclier."),
    "shield_refill_s": ("Recharge du bouclier", "Le temps avant qu'un bouclier cassé revienne."),
    "speed_percent": ("Vitesse", "En plus de leur vitesse de base."),
    "back_after_s": ("Retour après la mort", "Il revient près de toi après ce temps."),
    "companion_bars": ("Barres de vie à gauche", "La vie de chaque compagnon en bas à gauche de l'écran, comme un "
                                                 "coéquipier en coop."),
}
