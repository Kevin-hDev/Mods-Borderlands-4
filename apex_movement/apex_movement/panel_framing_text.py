"""Framing presentation text; percentages are relative to the historical camera."""
from .camera_control_config import FRAMING_GROUPS as GROUPS

FR = {
    "zoom": ("ZOOM EN VISÉE", "Supplément au zoom natif de chaque arme."),
    "horizontal": ("ÉCART À L'ÉPAULE", "Écart personnage-viseur. Le viseur reste centré."),
    "height": ("HAUTEUR DE CAMÉRA", "Monte ou descend la caméra. Le viseur reste centré."),
    "Wide": "Large", "Standard": "Standard", "Close": "Rapprocher",
    "Tight": "Serrer", "Open": "Ouvert",
    "Higher": "Plus haut", "Lower": "Plus bas", "Custom": "Personnalisé",
    "unavailable": "Aperçu du cadrage indisponible ici.",
    "zoom_unavailable": "Zoom supplémentaire en visée indisponible ; la position de la caméra est affichée.",
    "position_unavailable": "Position de caméra indisponible ; le zoom supplémentaire en visée est affiché.",
}
EN = {
    "zoom": "Additional magnification over each weapon's native zoom.",
    "horizontal": "Character-to-crosshair spacing. The crosshair stays centered.",
    "height": "Moves the camera up or down. The crosshair stays centered.",
    "unavailable": "Framing preview unavailable here.",
    "zoom_unavailable": "Additional aiming zoom unavailable; the camera position is shown.",
    "position_unavailable": "Camera position unavailable; additional aiming zoom is shown.",
}


def text(key, language):
    if language != "FR":
        definition = next((group for group in GROUPS if group.key == key), None)
        if definition is not None:
            return definition.title.upper(), EN[key]
    return (FR if language == "FR" else EN).get(key, key)
