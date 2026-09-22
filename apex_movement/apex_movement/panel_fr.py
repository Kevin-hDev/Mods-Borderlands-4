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
    "movement": "Régle la vitesse de marche et de course.",
    "auto_sprint": "Cours automatiquement quand le stick est poussé à fond.",
    "slides": "Règle le départ, la distance et la vitesse des glissades.",
    "axle_slide": "Dirige et accélère les glissades à la manière d'Axle.",
    "dash": "Règle la distance du dash.",
    "glide": "Règle la vitesse du vol plané.",
    "air_crouch": "Frappe le sol et glisse à l'atterrissage.",
    "air_strafe": "Change rapidement de direction dans les airs.",
    "heavier_fall": "Règle la pesanteur et la hauteur des sauts.",
    "wall_climb": "Règle la grimpe, la direction et le délai avant de se raccrocher.",
}

OPTIONS = {
    "walk_speed": ("Vitesse de marche", "Vitesse au sol en marchant. La valeur du jeu est 540."),
    "sprint_speed": ("Vitesse de course", "Vitesse en courant. La valeur du jeu est 828."),
    "auto_sprint": ("Activé", "Cours quand le stick est poussé à fond, dans la limite d'angle du jeu."),
    "slides": ("Activé", "Des glissades plus rapides et longues. Désactivé, le jeu reprend les siennes."),
    "momentum_slides": ("Suivre l'élan", "La glissade suit ton déplacement au lieu du viseur."),
    "slide_speed": ("Vitesse de départ", "Vitesse au début d'une glissade."),
    "slide_distance": ("Distance sur le plat", "Distance sur terrain plat ; les pentes la modifient."),
    "slide_downhill_pull": ("Effet des pentes", "Force avec laquelle les pentes accélèrent ou ralentissent la glissade."),
    "slide_max_speed": ("Vitesse maximale", "Vitesse maximale d'une glissade, même en forte descente."),
    "axle_slide": ("Activé", "Dirige et amplifie chaque glissade comme Axle."),
    "axle_steering": ("Direction", "Vitesse de rotation d'une glissade avec le stick."),
    "axle_speed_boost": ("Gain de vitesse", "Pourcentage de vitesse ajouté à la glissade normale."),
    "axle_flat_distance_boost": ("Distance sur le plat", "Pourcentage de distance ajouté sur terrain plat."),
    "axle_slope_boost": ("Effet des pentes", "Pourcentage de distance ajouté sur les pentes."),
    "dash": ("Activé", "Un dash plus long ; désactivé, celui du jeu revient."),
    "dash_distance": ("Distance du dash", "Pourcentage de la distance du jeu ; 100 correspond au jeu."),
    "glide": ("Activé", "Un vol plané plus rapide ; désactivé, celui du jeu revient."),
    "glide_speed": ("Vitesse du vol plané", "Pourcentage de la vitesse du jeu dans toutes les directions."),
    "air_crouch": ("Activé", "Frappe avec saut + accroupissement, ou glisse en atterrissant accroupi."),
    "landing_slide_min_speed": ("Vitesse minimale d'arrivée", "Vitesse nécessaire pour glisser à l'atterrissage."),
    "air_strafe": ("Activé", "Change rapidement de direction en l'air et au sol."),
    "air_acceleration": ("Accélération aérienne", "Vitesse à laquelle la direction change en l'air et au sol."),
    "heavier_fall": ("Activé", "Accélère la chute tout en préservant la hauteur des sauts."),
    "fall_weight": ("Poids de chute", "Multiplicateur de gravité. 1 correspond au jeu de base."),
    "jump_height_bonus": ("Hauteur de saut ajoutée", "Hauteur ajoutée à tous les types de saut."),
    "wall_climb": ("Activé", "Grimpe les murs en les visant et en avançant vers eux."),
    "climb_height": ("Hauteur de grimpe", "Hauteur de la grimpe en pourcentage de la taille du personnage."),
    "climb_speed": ("Vitesse de grimpe", "Vitesse verticale de la grimpe."),
    "climb_lean": ("Grimpe en diagonale", "Angle latéral autorisé pour grimper."),
    "reclimb_delay": ("Délai avant une nouvelle grimpe", "Attente après une grimpe inachevée ; atterrir l'efface."),
}
