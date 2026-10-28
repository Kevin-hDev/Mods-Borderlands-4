"""Every word this window shows exists in Japanese (2026-10-21), in Japanese characters: no English left in the
Japanese window, and no Simplified Chinese character slipped into it."""

import re

import panel_fixture  # noqa: F401  (installs the fake SDK)
from third_person_fov import panel_en, panel_fr, panel_framing_text, panel_glyphs, panel_header, panel_i18n
from third_person_fov import panel_ja, panel_profile_text

# Words that stay as they are in Japanese: angles, the game's name and the field of view's.
SAME = {"360°", "180°", "BL4", "FOV"}
JAPANESE = re.compile(r"[ぁ-ゟ゠-ヿ一-鿿]")
PLACES = re.compile(r"\{\w+\}")
failures = []


def check(condition, message):
    if not condition:
        failures.append(message)


def japanese_only(text):
    """Whether every character is one Japanese writes: Simplified Chinese ones (镜, 关) are not in JIS X 0213."""
    try:
        text.encode("euc_jis_2004")
    except UnicodeEncodeError:
        return False
    return True


def same_table(label, french, japanese):
    check(set(japanese) == set(french), f"{label}: missing {sorted(set(french) - set(japanese))}, "
                                        f"extra {sorted(set(japanese) - set(french))}")
    for key in set(french) & set(japanese):
        for fr, ja in zip(*(value if isinstance(value, tuple) else (value,) for value in (french[key], japanese[key]))):
            check(sorted(PLACES.findall(fr)) == sorted(PLACES.findall(ja)), f"{label}:{key} placeholders")
            check(ja in SAME or JAPANESE.search(ja), f"{label}:{key} not Japanese: {ja!r}")
            check(japanese_only(ja.replace("·", "")), f"{label}:{key} has a character Japanese does not write: {ja!r}")


check("JA" in panel_i18n.TABLES, "the window offers Japanese")
check(set(panel_en.TEXT) <= set(panel_ja.TEXT), f"window: {sorted(set(panel_en.TEXT) - set(panel_ja.TEXT))}")
same_table("window", panel_fr.TEXT, panel_ja.TEXT)
same_table("options", panel_fr.OPTIONS, panel_ja.OPTIONS)
same_table("pages", panel_fr.GROUPS, panel_ja.GROUPS)
same_table("framing", panel_framing_text.FR, panel_framing_text.JA)
same_table("profiles", panel_profile_text.FR, panel_profile_text.JA)
check(panel_framing_text.text("zoom", "JA") == panel_framing_text.JA["zoom"], "framing words in Japanese")
check(panel_profile_text.text("profile_save", "JA") == "保存", "profile words in Japanese")
check(panel_i18n.text("close", "JA") == "閉じる" and panel_i18n.text("camera", "JA") == "カメラ", "window words")
check(panel_header.language_button("JA") == "日本語", "the button named in Japanese")
check(panel_glyphs.label("Gamepad_FaceButton_Bottom", "PS5", "JA") == "×ボタン", "PlayStation shapes in Japanese")
check(panel_glyphs.label("Gamepad_FaceButton_Bottom", "XSX", "JA") == "A", "Xbox letters stay")
check(panel_glyphs.label("Gamepad_DPad_Up", "XSX", "JA") == "方向キー上", "the game's D-pad words on both")
check(panel_glyphs.label("Gamepad_LeftShoulder", "PS5", "JA") == "L1", "printed names stay")
check(panel_glyphs.label("Gamepad_DPad_Up", "PS5", "ZH") == "方向键上", "Chinese keeps its own words")

for message in failures:
    print("FAILED |", message)
print(f"RESULTAT: {'OK' if not failures else 'ECHEC'} | every word of the window exists in Japanese")
raise SystemExit(1 if failures else 0)
