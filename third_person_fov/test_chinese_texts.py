"""Every word this window shows exists in Chinese: no English left in the Chinese window (2026-10-12)."""

import re

import panel_fixture  # noqa: F401  (installs the fake SDK)
from third_person_fov import panel_en, panel_fr, panel_framing_text, panel_glyphs, panel_i18n, panel_profile_text
from third_person_fov import panel_zh

# Words that stay as they are in Chinese: angles, the game's name and the field of view's.
SAME = {"360°", "180°", "BL4", "FOV"}
CHINESE = re.compile(r"[㐀-鿿]")
PLACES = re.compile(r"\{\w+\}")
failures = []


def check(condition, message):
    if not condition:
        failures.append(message)


def same_table(label, french, chinese):
    check(set(chinese) == set(french), f"{label}: missing {sorted(set(french) - set(chinese))}, "
                                       f"extra {sorted(set(chinese) - set(french))}")
    for key in set(french) & set(chinese):
        for fr, zh in zip(*(value if isinstance(value, tuple) else (value,) for value in (french[key], chinese[key]))):
            check(sorted(PLACES.findall(fr)) == sorted(PLACES.findall(zh)), f"{label}:{key} placeholders")
            check(zh in SAME or CHINESE.search(zh), f"{label}:{key} not Chinese: {zh!r}")


check("ZH" in panel_i18n.TABLES, "the window offers Chinese")
check(set(panel_en.TEXT) <= set(panel_zh.TEXT), f"window: {sorted(set(panel_en.TEXT) - set(panel_zh.TEXT))}")
same_table("window", panel_fr.TEXT, panel_zh.TEXT)
same_table("options", panel_fr.OPTIONS, panel_zh.OPTIONS)
same_table("pages", panel_fr.GROUPS, panel_zh.GROUPS)
same_table("framing", panel_framing_text.FR, panel_framing_text.ZH)
same_table("profiles", panel_profile_text.FR, panel_profile_text.ZH)
check(panel_framing_text.text("zoom", "ZH") == panel_framing_text.ZH["zoom"], "framing words in Chinese")
check(panel_profile_text.text("profile_save", "ZH") == "保存", "profile words in Chinese")
check(panel_i18n.text("close", "ZH") == "关闭" and panel_i18n.text("camera", "ZH") == "镜头", "window words")
check(panel_glyphs.label("Gamepad_FaceButton_Bottom", "PS5", "ZH") == "×键", "PlayStation shapes in Chinese")
check(panel_glyphs.label("Gamepad_FaceButton_Bottom", "XSX", "ZH") == "A", "Xbox letters stay")
check(panel_glyphs.label("Gamepad_DPad_Up", "XSX", "ZH") == "方向键上", "the D-pad in Chinese on both")
check(panel_glyphs.label("Gamepad_LeftShoulder", "PS5", "ZH") == "L1", "printed names stay")

for message in failures:
    print("FAILED |", message)
print(f"RESULTAT: {'OK' if not failures else 'ECHEC'} | every word of the window exists in Chinese")
raise SystemExit(1 if failures else 0)
