"""French Apex Heirloom texts: the CONTROLS page's words from Apex Grapple's menu, the rest this mod's own.

The heirloom's are those of the sketches Kevin chose on 2026-09-26 and 29 (cosmetics/heirloom/docs/esquisses_menu/,
A, U1 to U3 and H2), the sentence at the top of its page his own.
"""

from . import heirloom_settings
from .panel_common_fr import TEXT as COMMON
from .panel_controls_text import FR as CONTROLS

TEXT = {
    **COMMON, **CONTROLS, "heirloom": "HEIRLOOM", "holster": "RANGEMENT", "first": "CHOISIR UNE TOUCHE",
    "no_key": "Aucune", "applies": "Quitte le menu et change d'arme pour appliquer le changement.",
    "refused_part": "Un autre fichier installé fait déjà tourner cette partie. Éteins-le d'abord.",
    "controls_intro": "Choisis une touche : clavier, souris ou manette.",
    "escape_hint": "Échap annule la saisie. La touche console est réservée.",
    "invalid_keys": "Non enregistré. Choisis une touche du clavier, un bouton de la souris ou de la manette.",
    "controls_reset": "Commandes d’origine restaurées.",
}
GROUPS = {"heirloom": "Ton heirloom dans ta main droite quand ton arme est rangée.",
          "holster": "Comment chaque touche range ton arme."}
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
