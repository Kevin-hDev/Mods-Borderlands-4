"""French Benefix Ohm Attack texts: Apex Grapple's words for the page name, the icons and the reset of the COMMANDS page
(panel_controls_text.py), the rest this mod's own, as sketches M1 and C wrote them (Kevin, 2026-10-01,
docs/attaque-rayon/esquisses_menu/). Kevin kept the elements' names on 2026-10-01.
"""

from .panel_common_fr import TEXT as COMMON
from .panel_controls_text import FR as CONTROLS

TEXT = {
    **COMMON, **CONTROLS, "beam": "RAYON", "no_key": "AUCUNE",
    "energy": "ÉNERGIE",
    "energy_desc": "Le rayon a sa propre énergie, de 100. Vide, le rayon s'arrête.",
    "lock": "VERROU",
    "bounce": "REBOND",
    "bounce_desc": "Le rayon saute de sa cible vers un second ennemi.",
    "command_fire": "LANCER LE RAYON",
    "command_fire_desc": "La touche à tenir pour lancer le rayon. Aucune par défaut : choisis la tienne.",
    "keyboard": "CLAVIER / SOURIS", "controller": "MANETTE",
    "change_keyboard": "CHOISIR UNE TOUCHE", "change_controller": "CHOISIR UN BOUTON",
    "press_keyboard": "APPUIE SUR UNE TOUCHE", "press_controller": "APPUIE SUR UN BOUTON",
    "escape_hint": "Échap annule la saisie. La touche console est réservée.",
    "controls_reset": "Commandes d’origine restaurées.",
    "wheel_key": "Non enregistrée : la molette ne peut pas être tenue. Touche précédente gardée.",
    "invalid_keyboard": "Non enregistrée : choisis une touche du clavier ou un bouton de la souris. Touche précédente "
                        "gardée.",
    "invalid_controller": "Non enregistré : choisis un bouton de la manette. Bouton précédent gardé.",
}
GROUPS = {"beam": "Tiens la touche du rayon : ta main gauche se lève et lance un rayon sur ce que tu vises.",
          "lock": "Le rayon se verrouille sur l'ennemi qu'il touche, comme celui de la Benefix Ohm I Got."}
OPTIONS = {
    "element": ("Élément", "Ce dont le rayon est fait : feu, électrique, corrosif, cryo, radiation, ou cinétique "
                           "(sans élément, blanc)."),
    "damage": ("Dégâts par seconde", "Les dégâts au niveau 1. Le rayon grandit avec ton niveau à partir de cette "
                                     "valeur."),
    "width": ("Distance d'accroche", "À quelle distance de ton viseur le rayon attrape un ennemi, en centimètres. "
                                     "0 : il faut viser l'ennemi."),
    "lock": ("Verrouillage", "Le rayon reste sur l'ennemi qu'il a touché, même quand ton viseur s'en écarte."),
    "lock_delay": ("Temps avant le verrou", "Les secondes que le rayon doit rester sur un ennemi avant de se "
                                            "verrouiller."),
    "lock_angle": ("Angle de rupture", "L'écart de ton viseur avec l'ennemi, en degrés, au-delà duquel le verrou "
                                       "lâche."),
    "bounce": ("Rebond", "Le second ennemi doit être à moins de 20 mètres du premier."),
    "show_bar": ("Barre d'énergie", "Affiche la barre d'énergie sous ta barre d'endurance pendant que le rayon sert."),
    "drain": ("Énergie par seconde", "Ce que le rayon dépense. 0 : l'énergie ne baisse jamais."),
    "regen": ("Recharge par seconde", "La vitesse à laquelle l'énergie revient."),
    "regen_delay": ("Délai avant recharge", "Les secondes sans tirer avant que l'énergie revienne."),
}
CHOICES = {"Fire": "Feu", "Shock": "Électrique", "Corrosive": "Corrosif", "Cryo": "Cryo", "Radiation": "Radiation",
           "Kinetic": "Cinétique"}
