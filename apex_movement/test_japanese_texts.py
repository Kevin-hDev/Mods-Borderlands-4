"""Every word Apex Movement's window shows exists in Japanese (2026-10-21), in Japanese characters: no English left in
the Japanese window, and no Simplified Chinese character slipped into it."""

import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import sdk_stubs  # noqa: E402

sdk_stubs.install()
from apex_movement import panel_en, panel_fr, panel_framing_text, panel_glyphs, panel_header, panel_i18n  # noqa: E402
from apex_movement import panel_ja, panel_profile_text  # noqa: E402

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


def same_table(label, reference, japanese):
    check(set(japanese) == set(reference), f"{label}: missing {sorted(set(reference) - set(japanese))}, "
                                           f"extra {sorted(set(japanese) - set(reference))}")
    for key in set(reference) & set(japanese):
        for other, ja in zip(*(value if isinstance(value, tuple) else (value,)
                               for value in (reference[key], japanese[key]))):
            check(sorted(PLACES.findall(other)) == sorted(PLACES.findall(ja)), f"{label}:{key} placeholders")
            check(ja in SAME or JAPANESE.search(ja), f"{label}:{key} not Japanese: {ja!r}")
            check(japanese_only(ja.replace("·", "")), f"{label}:{key} has a character Japanese does not write: {ja!r}")


check("JA" in panel_i18n.TABLES, "the window offers Japanese")
# English and French together: French alone has the aim notices, English names every other key.
same_table("window", {**panel_en.TEXT, **panel_fr.TEXT}, panel_ja.TEXT)
same_table("options", panel_fr.OPTIONS, panel_ja.OPTIONS)
same_table("pages", panel_fr.GROUPS, panel_ja.GROUPS)
same_table("framing", panel_framing_text.FR, panel_framing_text.JA)
same_table("profiles", panel_profile_text.FR, panel_profile_text.JA)
check(panel_i18n.text("language_name", "JA") == "日本語", "the language button names Japanese in its own words")
check(panel_i18n.text("close", "JA") == "閉じる" and panel_i18n.text("camera", "JA") == "カメラ", "window words")
check(panel_profile_text.text("profile_save", "JA") == "保存", "profile words in Japanese")
check(panel_header.language_button("JA") == "日本語", "the header button named in Japanese")
check(panel_glyphs.label("Gamepad_FaceButton_Bottom", "PS5", "JA") == "×ボタン", "PlayStation shapes in Japanese")
check(panel_glyphs.label("Gamepad_DPad_Up", "PS5", "ZH") == "方向键上", "Chinese keeps its own words")

for message in failures:
    print("FAILED |", message)
print(f"RESULTAT: {'OK' if not failures else 'ECHEC'} | every word of Apex Movement's window exists in Japanese")
raise SystemExit(1 if failures else 0)
