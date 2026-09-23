"""French Vehicle Driving pages and options."""

from .panel_common_fr import TEXT as COMMON

TEXT = {**COMMON, "driving": "CONDUITE", "handling": "TENUE DE ROUTE"}

GROUPS = {
    "driving": "Vitesse, direction et sauts du véhicule.",
    "handling": "Contrôle du véhicule dans les virages.",
}

OPTIONS = {
    "max_speed": ("Vitesse maximale", "100 % = la vitesse du jeu, boost compris."),
    "acceleration": ("Accélération", "100 % = l'accélération du jeu."),
    "turn_speed": ("Vitesse de rotation", "100 % = valeur du jeu."),
    "jump_height": ("Hauteur de saut", "100 % = valeur du jeu."),
    "grip": ("Adhérence", "Le véhicule tient sa trajectoire au lieu de déraper."),
    "turn_loss": ("Perte de vitesse en virage", "Part de la vitesse perdue dans un virage à angle droit."),
}
