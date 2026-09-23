"""French Movement pages and settings; common window messages share Grapple's source."""

from .panel_common_fr import TEXT as COMMON

TEXT = {
    **COMMON,
    "movement": "DÉPLACEMENT", "auto_sprint": "COURSE AUTOMATIQUE", "slides": "GLISSADES",
    "axle_slide": "GLISSADE AXLE", "dash": "DASH", "glide": "VOL PLANÉ",
    "air_crouch": "FRAPPE AU SOL ET GLISSADE", "air_strafe": "DIRECTION AÉRIENNE",
    "heavier_fall": "CHUTE PLUS LOURDE", "wall_climb": "GRIMPE",
}

GROUPS = {
    "movement": "Vitesse de marche et de course.",
    "auto_sprint": "Cours automatiquement quand le stick est poussé à fond.",
    "slides": "Départ, distance et vitesse des glissades.",
    "axle_slide": "Dirige et accélère les glissades à la manière d'Axle.",
    "dash": "Distance du dash.",
    "glide": "Vitesse du vol plané.",
    "air_crouch": "Frappe le sol et glisse à l'atterrissage.",
    "air_strafe": "Change rapidement de direction dans les airs.",
    "heavier_fall": "Pesanteur et hauteur des sauts.",
    "wall_climb": "Grimpe, direction et délai avant de se raccrocher.",
}

OPTIONS = {
    "walk_speed": ("Vitesse de marche", "Valeur du jeu : 540."),
    "sprint_speed": ("Vitesse de course", "Valeur du jeu : 828."),
    "auto_sprint": ("Activé", "Courir en poussant le stick à fond."),
    "slides": ("Activé", "Des glissades plus rapides et plus longues."),
    "momentum_slides": ("Suivre l'élan", "La glissade suit ton déplacement au lieu du viseur."),
    "slide_speed": ("Vitesse de départ", "Vitesse au début d'une glissade."),
    "slide_distance": ("Distance sur le plat", "Distance sur terrain plat."),
    "slide_downhill_pull": ("Effet des pentes", "Les pentes accélèrent ou freinent la glissade."),
    "slide_max_speed": ("Vitesse maximale", "Vitesse maximale d'une glissade."),
    "axle_slide": ("Activé", "Des glissades qu'on dirige, et plus rapides, comme Axle."),
    "axle_steering": ("Direction", "Vitesse de rotation d'une glissade avec le stick."),
    "axle_speed_boost": ("Gain de vitesse", "Vitesse en plus, en pourcentage."),
    "axle_flat_distance_boost": ("Distance sur le plat", "Distance en plus sur le plat, en pourcentage."),
    "axle_slope_boost": ("Effet des pentes", "Distance en plus en pente, en pourcentage."),
    "dash": ("Activé", "Un dash plus long."),
    "dash_distance": ("Distance du dash", "En pourcentage. 100 = le dash du jeu."),
    "glide": ("Activé", "Un vol plané plus rapide."),
    "glide_speed": ("Vitesse du vol plané", "En pourcentage. 100 = la vitesse du jeu."),
    "air_crouch": ("Activé", "Frappe avec saut + accroupissement, ou glisse en atterrissant accroupi."),
    "landing_slide_min_speed": ("Vitesse minimale d'arrivée", "Vitesse nécessaire pour glisser à l'atterrissage."),
    "air_strafe": ("Activé", "Change rapidement de direction en l'air et au sol."),
    "air_acceleration": ("Accélération aérienne", "Vitesse à laquelle la direction change en l'air et au sol."),
    "heavier_fall": ("Activé", "Tomber plus vite sans sauter moins haut."),
    "fall_weight": ("Poids de chute", "Force de la gravité. 1 = celle du jeu."),
    "jump_height_bonus": ("Hauteur de saut ajoutée", "Hauteur en plus pour tous les sauts."),
    "wall_climb": ("Activé", "Grimper sur les murs."),
    "climb_height": ("Hauteur de grimpe", "En pourcentage de la taille du personnage."),
    "climb_speed": ("Vitesse de grimpe", "Vitesse de montée."),
    "climb_lean": ("Grimpe en diagonale", "Jusqu'où la grimpe peut partir en biais."),
    "reclimb_delay": ("Délai avant une nouvelle grimpe", "Attente avant de pouvoir regrimper. Toucher le sol l'annule."),
}
