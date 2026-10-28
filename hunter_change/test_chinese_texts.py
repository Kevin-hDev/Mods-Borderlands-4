"""Every word Hunter Change's window shows exists in Chinese: no English left in the Chinese window, the hunters named
as the Chinese game names them, and every refusal still saying the game is untouched (2026-10-13)."""

import pathlib
import re
import string
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import sdk_stubs  # noqa: E402

sdk_stubs.install()
from hunter_change import hunters, panel_en, panel_fr, panel_hunter_names, panel_i18n, panel_switch_text  # noqa: E402
from hunter_change import panel_zh  # noqa: E402
from hunter_change.switch_page import CARDS, CONFIRM, View  # noqa: E402

# Words that stay as they are in Chinese: the game's name.
SAME = {"BL4"}
CHINESE = re.compile(r"[㐀-鿿]")
PLACES = re.compile(r"\{\w+\}")
# Half-width punctuation has no place in a Chinese sentence; the mod's and OneDrive's names carry none.
LATIN_PUNCTUATION = re.compile(r"[,.:;()!?]")
# The French ways of saying the game is untouched, and the Chinese ones that must answer them.
UNTOUCHED_FR = ("pas touchée", "Rien n'a changé", "n'y touche pas")
UNTOUCHED_ZH = ("未受影响", "未做任何更改", "不会改动")
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


def formats(sentence):
    blanks = {field for _, field, _, _ in string.Formatter().parse(sentence) if field}
    try:
        return "{" not in sentence.format(**dict.fromkeys(blanks, "维克丝"))
    except (IndexError, KeyError, ValueError):
        return False


check("ZH" in panel_i18n.TABLES, "the window offers Chinese")
# English and French together: French alone has no key English lacks today, but a window key added in French only
# must not be forgotten.
same_table("window", {**panel_en.TEXT, **panel_fr.TEXT}, panel_zh.TEXT)
same_table("options", panel_fr.OPTIONS, panel_zh.OPTIONS)
same_table("pages", panel_fr.GROUPS, panel_zh.GROUPS)

# A key missing in Chinese is already reported by same_table.
OWN = [key for key in panel_fr.TEXT if key not in panel_fr.COMMON and key in panel_zh.TEXT]
check(all(formats(panel_zh.TEXT[key]) for key in OWN), "every Chinese sentence filled without error")
check(not [key for key in OWN if LATIN_PUNCTUATION.search(panel_zh.TEXT[key])], "full-width punctuation only")
check(not [key for key in (*OWN, *panel_zh.GROUPS) if "点击" in {**panel_zh.TEXT, **panel_zh.GROUPS}[key]],
      "选择, never 点击: the menu is also used with a controller")
check(all(any(word in panel_zh.TEXT[key] for word in UNTOUCHED_ZH)
          for key in OWN if any(word in panel_fr.TEXT[key] for word in UNTOUCHED_FR)),
      "every refusal still says the game is untouched")

check(set(panel_zh.NAMES) == {hunter.code for hunter in hunters.HUNTERS}
      and all(CHINESE.search(name) for name in panel_zh.NAMES.values()), "every hunter named in Chinese")
check(all(panel_hunter_names.name(hunter, language) == hunter.name
          for hunter in hunters.HUNTERS for language in ("EN", "FR")), "English and French keep the hunters' names")

# The window as it will be once Chinese is offered: its sentences name the hunters in Chinese.
vex, rafa = hunters.by_code("DarkSiren"), hunters.by_code("ExoSoldier")
offered = "ZH" in panel_i18n.TABLES
panel_i18n.TABLES.setdefault("ZH", panel_zh)
try:
    confirm = panel_switch_text.confirm(View(CONFIRM, True, vex, rafa, kept=False), "ZH")
    check(confirm.startswith("你将在此存档中成为拉法") and "维克丝的技能树" in confirm
          and "拉法在此存档中还没有技能树" in confirm, f"the change asked, in Chinese: {confirm!r}")
    check(panel_switch_text.state(View(CARDS, True, vex), "ZH") == "你正在使用维克丝。选择一名秘藏猎人，在此存档中换成该猎人。",
          "the HUNTER page's sentence, in Chinese")
    check(panel_i18n.text("class:Paladin", "ZH") == "锻造骑士" and panel_i18n.text("close", "ZH") == "关闭",
          "window words")
finally:
    if not offered:
        del panel_i18n.TABLES["ZH"]

# A Windows console prints in cp1252, where a Chinese failure message would crash the test before its RESULTAT.
sys.stdout.reconfigure(errors="backslashreplace")
for message in failures:
    print("FAILED |", message)
print(f"RESULTAT: {'OK' if not failures else 'ECHEC'} | every word of Hunter Change's window exists in Chinese")
raise SystemExit(1 if failures else 0)
