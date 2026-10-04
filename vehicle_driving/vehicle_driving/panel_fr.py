"""French Vehicle Driving pages and options."""

from .panel_common_fr import TEXT as COMMON

TEXT = {**COMMON, "driving": "CONDUITE", "handling": "TENUE DE ROUTE", "boost": "TURBO", "combat": "COMBAT"}

GROUPS = {
    "driving": "Vitesse, marche arrière, direction et sauts du véhicule.",
    "handling": "Contrôle du véhicule dans les virages.",
    "boost": "Durée du turbo et poussée en l'air.",
    "combat": "Solidité du véhicule et dégâts de ses armes.",
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
}
