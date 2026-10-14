"""Every word Apex Grapple's window shows exists in Chinese: no English left in the Chinese window (2026-10-13)."""

import pathlib
import re
import sys
from types import SimpleNamespace

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import sdk_stubs  # noqa: E402

sdk_stubs.install()
from apex_grapple import panel_en, panel_fr, panel_glyphs, panel_i18n, settings  # noqa: E402
from apex_grapple import panel_zh  # noqa: E402

# Words that stay as they are in Chinese: the game's name and the console brands printed on the controllers.
SAME = {"BL4", "PLAYSTATION", "XBOX"}
CHINESE = re.compile(r"[㐀-鿿]")
PLACES = re.compile(r"\{\w+\}")
failures = []


def check(condition, message):
    if not condition:
        failures.append(message)


def same_table(label, reference, chinese):
    check(set(chinese) == set(reference), f"{label}: missing {sorted(set(reference) - set(chinese))}, "
                                          f"extra {sorted(set(chinese) - set(reference))}")
    for key in set(reference) & set(chinese):
        for other, zh in zip(*(value if isinstance(value, tuple) else (value,)
                               for value in (reference[key], chinese[key]))):
            check(sorted(PLACES.findall(other)) == sorted(PLACES.findall(zh)), f"{label}:{key} placeholders")
            check(zh in SAME or CHINESE.search(zh), f"{label}:{key} not Chinese: {zh!r}")


check("ZH" in panel_i18n.TABLES, "the window offers Chinese")
same_table("window", {**panel_en.TEXT, **panel_fr.TEXT}, panel_zh.TEXT)
same_table("options", panel_fr.OPTIONS, panel_zh.OPTIONS)
check(set(panel_zh.OPTIONS) == {option.identifier for option in settings.ALL}, "every setting has its Chinese row")
same_table("pages", panel_fr.GROUPS, panel_zh.GROUPS)
# The names a choice's buttons write, by row: every name of every row has its words in the three languages.
named = {f"{option.identifier}:{choice}" for option in settings.ALL for choice in getattr(option, "choices", ())}
check(set(panel_en.CHOICES) == named == set(panel_fr.CHOICES), "every choice has its English and French words")
same_table("choices", {**panel_en.CHOICES, **panel_fr.CHOICES}, panel_zh.CHOICES)

# The lookups route Chinese once LANGUAGES lists it, which the lead switches on with the font (menu_languages.py).
offered = panel_i18n.TABLES
panel_i18n.TABLES = {**offered, "ZH": panel_zh}
option = SimpleNamespace(identifier="grapple_range", display_name="Range", description="English")
check(panel_i18n.text("controls", "ZH") == "按键" and panel_i18n.text("close", "ZH") == "关闭", "window words")
check(panel_i18n.option_text(option, "ZH") == panel_zh.OPTIONS["grapple_range"], "setting rows in Chinese")
check(panel_i18n.group_text(None, "pull", "ZH") == panel_zh.GROUPS["pull"], "page sentences in Chinese")
check(panel_i18n.text("close", "FR") == panel_fr.TEXT["close"], "French unchanged")
check(panel_i18n.option_text(option, "EN") == ("Range", "English"), "English from the SDK option")
panel_i18n.TABLES = offered
check(panel_glyphs.label("Gamepad_DPad_Up", "PS5", "ZH") == "方向键上", "controller names in Chinese")

for message in failures:
    print("FAILED |", message)
print(f"RESULTAT: {'OK' if not failures else 'ECHEC'} | every word of Apex Grapple's window exists in Chinese")
raise SystemExit(1 if failures else 0)
