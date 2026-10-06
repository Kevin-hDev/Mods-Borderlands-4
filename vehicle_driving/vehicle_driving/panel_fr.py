"""French Vehicle Driving pages and options."""

from .panel_common_fr import TEXT as COMMON
from .panel_controls_text import FR as CONTROLS

# The CAMERA page's key card says what Apex Heirloom's COMMANDS page says: one way to choose a key in every menu.
TEXT = {
    **COMMON, **CONTROLS, "driving": "CONDUITE", "handling": "TENUE DE ROUTE", "boost": "TURBO", "combat": "COMBAT",
    "camera": "CAMÉRA", "no_key": "AUCUNE",
    "command_view": "CHANGER DE VUE",
    "command_view_desc": "La touche qui passe à la vue suivante, au volant.",
    "keyboard": "CLAVIER / SOURIS", "controller": "MANETTE",
    "change_keyboard": "CHOISIR UNE TOUCHE", "change_controller": "CHOISIR UN BOUTON",
    "press_keyboard": "APPUIE SUR UNE TOUCHE", "press_controller": "APPUIE SUR UN BOUTON",
    "escape_hint": "Échap annule la saisie. La touche console est réservée.",
    "controls_reset": "Commandes d’origine restaurées.",
    "invalid_keyboard": "Non enregistrée : choisis une touche du clavier ou un bouton de la souris. Touche précédente "
                        "gardée.",
    "invalid_controller": "Non enregistré : choisis un bouton de la manette. Bouton précédent gardé.",
}

GROUPS = {
    "driving": "Vitesse, marche arrière, direction et sauts du véhicule.",
    "handling": "Contrôle du véhicule dans les virages.",
    "boost": "Durée du turbo et poussée en l'air.",
    "combat": "Solidité du véhicule et dégâts de ses armes.",
    "camera": "La vue de caméra au volant, et la place de la vue Personnalisée.",
}

OPTIONS = {
    "max_speed": ("Vitesse maximale", "100 % = la vitesse du jeu, boost compris."),
    "acceleration": ("Accélération", "100 % = l'accélération du jeu."),
    "turn_speed": ("Vitesse de rotation", "100 % = valeur du jeu."),
    "jump_height": ("Hauteur de saut", "100 % = valeur du jeu."),
    "reverse_speed": ("Marche arrière", "100 % = la vitesse du jeu en marche arrière."),
    "grip": ("Adhérence", "Le véhicule tient sa trajectoire au lieu de déraper."),
    "turn_loss": ("Perte de vitesse en virage", "Part de la vitesse perdue dans un virage à angle droit."),
    "boost_duration": ("Durée du turbo", "100 % = la durée du turbo du jeu."),
    "unlimited_boost": ("Turbo illimité", "La jauge du turbo ne se vide jamais."),
    "air_push": ("Poussée en l'air", "100 % = la poussée du turbo au sol, en saut et en chute."),
    "toughness": ("Solidité du véhicule", "200 % = deux fois moins de dégâts reçus."),
    "weapon_damage": ("Dégâts des armes", "100 % = les dégâts du jeu, mitrailleuse et roquettes."),
    "vehicle_view": ("Vue du véhicule", "La vue de caméra au volant."),
    "custom_forward": ("Avant / arrière", "Vue personnalisée : caméra en avant (+) ou en arrière (-)."),
    "custom_side": ("Gauche / droite", "Vue personnalisée : caméra à droite (+) ou à gauche (-)."),
    "custom_height": ("Haut / bas", "Vue personnalisée : caméra en haut (+) ou en bas (-)."),
}

# The views' names, as the spec names them in French (section 2).
CHOICES = {"Far": "Éloignée", "Default": "Par défaut", "Close": "Proche", "Closer": "Très proche",
           "Closest": "Au plus près", "Custom": "Personnalisée"}
