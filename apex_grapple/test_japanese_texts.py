"""Every word Apex Grapple's window shows exists in Japanese (2026-10-21), in Japanese characters: no English left in
the Japanese window, and no Simplified Chinese character slipped into it."""

import pathlib
import re
import sys
from types import SimpleNamespace

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import sdk_stubs  # noqa: E402

sdk_stubs.install()
from apex_grapple import panel_choices, panel_en, panel_fr, panel_glyphs, panel_header, panel_i18n  # noqa: E402
from apex_grapple import panel_ja, settings  # noqa: E402

# Words that stay as they are in Japanese: the game's name and the console brands printed on the controllers.
SAME = {"BL4", "PLAYSTATION", "XBOX"}
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
same_table("window", {**panel_en.TEXT, **panel_fr.TEXT}, panel_ja.TEXT)
same_table("options", panel_fr.OPTIONS, panel_ja.OPTIONS)
check(set(panel_ja.OPTIONS) == {option.identifier for option in settings.ALL}, "every setting has its Japanese row")
same_table("pages", panel_fr.GROUPS, panel_ja.GROUPS)
same_table("choices", {**panel_en.CHOICES, **panel_fr.CHOICES}, panel_ja.CHOICES)

option = SimpleNamespace(identifier="grapple_range", display_name="Range", description="English")
check(panel_i18n.text("close", "JA") == "閉じる", "window words")
check(panel_i18n.option_text(option, "JA") == panel_ja.OPTIONS["grapple_range"], "setting rows in Japanese")
check(panel_i18n.group_text(None, "pull", "JA") == panel_ja.GROUPS["pull"], "page sentences in Japanese")
rope = next(option for option in settings.ALL if option.identifier == "rope_colour")
check(panel_choices.label("RED", "JA", rope) == panel_ja.CHOICES["rope_colour:RED"], "choice names in Japanese")
check(panel_header.language_button("JA") == "日本語", "the header button named in Japanese")
check(panel_glyphs.label("Gamepad_DPad_Up", "PS5", "JA") == "方向キー上", "controller names in Japanese")

for message in failures:
    print("FAILED |", message)
print(f"RESULTAT: {'OK' if not failures else 'ECHEC'} | every word of Apex Grapple's window exists in Japanese")
raise SystemExit(1 if failures else 0)
