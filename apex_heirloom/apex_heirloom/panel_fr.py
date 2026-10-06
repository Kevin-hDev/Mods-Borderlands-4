"""French Apex Heirloom texts: Apex Grapple's words for the page name, the icons and the reset of the COMMANDS page
(panel_controls_text.py), the rest this mod's own.

The heirloom's are those of the sketches Kevin chose on 2026-09-26 and 29 (cosmetics/heirloom/docs/esquisses_menu/,
A, U1 to U3 and H2), the sentence at the top of its page his own; the COMMANDS page's cards those of sketch I1
(2026-09-30).
"""

from . import heirloom_settings
from .panel_common_fr import TEXT as COMMON
from .panel_controls_text import FR as CONTROLS

TEXT = {
    **COMMON, **CONTROLS, "heirloom": "HEIRLOOM", "holster": "RANGEMENT", "no_key": "AUCUNE",
    "applies": "Quitte le menu et change d'arme pour appliquer le changement.",
    "refused_part": "Un autre fichier installé fait déjà tourner cette partie. Éteins-le d'abord.",
    "command_put_away": "RANGER L'ARME",
    "command_put_away_desc": "La touche qui range ton arme, maintenue ou appuyée. Grisée quand le Rangement est sur "
                             "NON.",
    "command_inspect": "ANIMATION",
    "command_inspect_desc": "Fais tourner ton heirloom dans ta main quand ton arme est rangée. Grisée quand le "
                            "Heirloom est sur NON.",
    "keyboard": "CLAVIER / SOURIS", "controller": "MANETTE",
    "change_keyboard": "CHOISIR UNE TOUCHE", "change_controller": "CHOISIR UN BOUTON",
    "press_keyboard": "APPUIE SUR UNE TOUCHE", "press_controller": "APPUIE SUR UN BOUTON",
    "escape_hint": "Échap annule la saisie. La touche console est réservée.",
    "controls_reset": "Commandes d’origine restaurées.",
    "duplicate_put_away": "Non enregistrée : cette touche range déjà ton arme. Touche précédente gardée.",
    "duplicate_inspect": "Non enregistrée : cette touche joue déjà l'animation de ton heirloom. Touche précédente "
                         "gardée.",
    "wheel_key": "Non enregistrée : la molette change d'arme dans le jeu. Touche précédente gardée.",
    "invalid_keyboard": "Non enregistrée : choisis une touche du clavier ou un bouton de la souris. Touche précédente "
                        "gardée.",
    "invalid_controller": "Non enregistré : choisis un bouton de la manette. Bouton précédent gardé.",
}
GROUPS = {"heirloom": "Ton heirloom dans ta main droite quand ton arme est rangée.",
          "holster": "Si tes touches rangent ton arme."}
OPTIONS = {
    "heirloom": ("Heirloom", "NON : tes mains restent vides quand ton arme est rangée, comme dans le jeu."),
    "model": ("Modèle", "Le heirloom que tu tiens."),
    **{option.identifier: ("Skin", "L'aspect de ton heirloom. Grisé quand il n'en a qu'un.")
       for option in heirloom_settings.SKINS.values()},
    "glow": ("Lumière", "La force de la lumière de la lame. Grisé quand le skin n'en a pas."),
    "mode": ("Mode", "Apex : toutes les animations du heirloom. Borderlands : les nôtres au repos, en marchant et en "
                     "courant, celles du jeu pour le reste."),
    **{option.identifier: ("Taille du heirloom", "La taille du heirloom choisi dans ta main. 100 : sa taille "
                                                 "d'origine.") for option in heirloom_settings.SIZES.values()},
    "draw_start": ("Début de la sortie",
                   "Plus la valeur est haute, plus tes mains apparaissent tôt quand tu ranges ton arme."),
    "draw_speed": ("Vitesse de la sortie", "La vitesse à laquelle tes mains sortent le heirloom."),
    "holster": ("Rangement", "NON : tes touches ne rangent plus ton arme."),
    "keyboard_hold": ("Clavier : maintenir", "Maintiens la touche au lieu d'un seul appui."),
    "controller_hold": ("Manette : maintenir", "Maintiens le bouton, car carré recharge sur un appui."),
    "hold_time": ("Durée du maintien", "Temps à maintenir la touche ou le bouton, en secondes."),
}
# The heirlooms' names in French; the skins keep their English ones, as Kevin chose (panel_en.CHOICES).
CHOICES = {"jakobs_knife": "Couteau Jakobs", "axe": "Hache", "own": "D'origine"}
