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
ZH = {
    "zoom": ("瞄准倍率", "在每把武器原有的倍率上额外放大。"),
    "horizontal": ("肩部间距", "角色与准星之间的间距。准星保持居中。"),
    "height": ("镜头高度", "升高或降低镜头。准星保持居中。"),
    "Wide": "广角", "Standard": "标准", "Close": "放大",
    "Tight": "贴近", "Open": "拉开",
    "Higher": "更高", "Lower": "更低", "Custom": "自定义",
    "unavailable": "此处无法预览构图。",
    "zoom_unavailable": "瞄准额外倍率不可用；显示的是镜头位置。",
    "position_unavailable": "镜头位置不可用；显示的是瞄准额外倍率。",
}
JA = {
    "zoom": ("照準ズーム", "各武器本来のズームに加える倍率。"),
    "horizontal": ("肩との間隔", "キャラクターと照準の間隔。照準は中央のままです。"),
    "height": ("カメラの高さ", "カメラを上げ下げします。照準は中央のままです。"),
    "Wide": "広角", "Standard": "標準", "Close": "拡大",
    "Tight": "狭め", "Open": "広め",
    "Higher": "高め", "Lower": "低め", "Custom": "カスタム",
    "unavailable": "ここでは構図のプレビューを表示できません。",
    "zoom_unavailable": "照準の追加ズームを表示できません。カメラの位置を表示しています。",
    "position_unavailable": "カメラの位置を表示できません。照準の追加ズームを表示しています。",
}
TRANSLATED = {"FR": FR, "ZH": ZH, "JA": JA}
EN = {
    "zoom": "Additional magnification over each weapon's native zoom.",
    "horizontal": "Character-to-crosshair spacing. The crosshair stays centered.",
    "height": "Moves the camera up or down. The crosshair stays centered.",
    "unavailable": "Framing preview unavailable here.",
    "zoom_unavailable": "Additional aiming zoom unavailable; the camera position is shown.",
    "position_unavailable": "Camera position unavailable; additional aiming zoom is shown.",
}


def text(key, language):
    table = TRANSLATED.get(language)
    if table is None:
        definition = next((group for group in GROUPS if group.key == key), None)
        if definition is not None:
            return definition.title.upper(), EN[key]
    return (EN if table is None else table).get(key, key)
