"""Read the game's controller brushes; only weak table references survive an opening."""

from itertools import islice
import unrealsdk

from . import panel_preferences as preferences, report

MAX_TABLES, MAX_KEYS = 32, 512
BUTTONS = {
    "Gamepad_FaceButton_Bottom": ("Cross", "Croix", "A"),
    "Gamepad_FaceButton_Right": ("Circle", "Rond", "B"),
    "Gamepad_FaceButton_Left": ("Square", "Carré", "X"),
    "Gamepad_FaceButton_Top": ("Triangle", "Triangle", "Y"),
    "Gamepad_LeftShoulder": ("L1", "L1", "LB"),
    "Gamepad_RightShoulder": ("R1", "R1", "RB"),
    "Gamepad_LeftTrigger": ("L2", "L2", "LT"),
    "Gamepad_RightTrigger": ("R2", "R2", "RT"),
    "Gamepad_LeftThumbstick": ("L3", "L3", "LS"),
    "Gamepad_RightThumbstick": ("R3", "R3", "RS"),
    "Gamepad_Special_Left": ("Create", "Create", "View"),
    "Gamepad_Special_Right": ("Options", "Options", "Menu"),
    "Gamepad_DPad_Up": ("D-pad up", "Croix directionnelle haut", "D-pad up"),
    "Gamepad_DPad_Down": ("D-pad down", "Croix directionnelle bas", "D-pad down"),
    "Gamepad_DPad_Left": ("D-pad left", "Croix directionnelle gauche", "D-pad left"),
    "Gamepad_DPad_Right": ("D-pad right", "Croix directionnelle droite", "D-pad right"),
}


def label(key, family, language):
    choices = BUTTONS.get(key)
    return choices[2 if family == "XSX" else int(language == "FR")] if choices else key


class Catalogue:
    def __init__(self):
        self.tables = {}
        try:
            objects = unrealsdk.find_all("CommonInputBaseControllerData", exact=False)
            for index, obj in enumerate(islice(objects, MAX_TABLES + 1)):
                if index == MAX_TABLES:
                    raise ValueError("Too many controller tables")
                family = str(obj.GamepadName)
                if family in preferences.CONTROLLER_ICONS and family not in self.tables:
                    self.tables[family] = unrealsdk.unreal.WeakPointer(obj)
        except Exception:
            self.tables.clear()
            report.error_once("panel:icons", "Controller icons unavailable; using button names.")

    def brush(self, family, key):
        if family not in preferences.CONTROLLER_ICONS or key not in BUTTONS:
            return None
        pointer = self.tables.get(family)
        table = pointer() if pointer is not None else None
        if table is None:
            return None
        try:
            entries = table.InputBrushDataMap
            if len(entries) > MAX_KEYS:
                raise ValueError("Too many icon entries")
            for entry in entries:
                if str(entry.Key.KeyName) == key:
                    brush = entry.KeyBrush
                    return brush if brush.ResourceObject is not None else None
        except Exception:
            report.error_once("panel:icon_brush", "Controller icon unavailable; using button name.")
        return None
