"""Every word Companions' window shows exists in French and in Chinese: its texts, its setting rows and its pages'
sentences, with the same places to fill; no English left in Chinese but the mods' names; no half-width punctuation in a
Chinese sentence; the game's words named as the Chinese game names them (It Follows' test_chinese_texts.py counted
them in the game's zh-Hans texts), never a word the game does not use; a button a sentence names written as it
shows, in 「」."""

import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

sdk_stubs.install()
from companions import menu, panel_common_en, panel_en, panel_fr, panel_zh, settings  # noqa: E402

CHINESE = re.compile(r"[㐀-鿿]")
PLACES = re.compile(r"\{[^{}]*\}")
LATIN_PUNCTUATION = re.compile(r"[,.:;()!?\[\]\"]")
# The mods' names stay in Latin letters; a value's own words are a sign and a number.
KEPT = ("It Follows", "Companions", "unrealsdk.log")
VALUES = ("value_times", "value_percent", "value_bonus")
# The game's own words, as It Follows' test reads them in the game's zh-Hans texts.
NAMES = ((r"\bvault hunters?\b|\bhunter's\b", "秘藏猎人"), (r"\bshields?\b", "护盾"), (r"\bhealth\b", "生命值"),
         (r"\bcompanions?\b", "伙伴"), (r"\bspeed\b", "速度"), (r"\bdeath\b", "死亡"), (r"\bpaus", "暂停"),
         (r"\bload a game\b", "存档"), (r"^options$", "选项"), (r"\bpress a key\b", "按任意键"))
NOT_THE_GAME = ("首领", "血量", "阵亡", "躲避", "同伴", "点击")
QUOTED = re.compile(r"「([^」]*)」")
failures = []


def check(condition: bool, message: str) -> None:
    if not condition:
        failures.append(message)


def bare(text: str) -> str:
    text = PLACES.sub("", text)
    for kept in KEPT:
        text = text.replace(kept, "")
    return text


def same_table(label: str, reference: dict, table: dict) -> None:
    check(set(table) == set(reference), f"{label}: missing {sorted(set(reference) - set(table))}, "
                                        f"extra {sorted(set(table) - set(reference))}")
    for key in set(reference) & set(table):
        check(sorted(PLACES.findall(reference[key])) == sorted(PLACES.findall(table[key])), f"{label}:{key} places")


own = {key: text for key, text in panel_en.TEXT.items() if key not in panel_common_en.TEXT}
same_table("FR", own, {key: text for key, text in panel_fr.TEXT.items() if key in own or key not in
                       panel_common_en.TEXT})
same_table("ZH", own, {key: text for key, text in panel_zh.TEXT.items() if key in own or key not in
                       panel_common_en.TEXT})
rows = [option.identifier for option in (*settings.TEAM, settings.bars)]
pages = [group.identifier.removesuffix("_menu") for group in menu.MENU]
for table, name in ((panel_fr, "FR"), (panel_zh, "ZH")):
    check(sorted(table.OPTIONS) == sorted(rows), f"{name}: a setting row without its words")
    check(sorted(table.GROUPS) == sorted(pages), f"{name}: a page without its sentence")
chinese = {**{key: panel_zh.TEXT[key] for key in own},
           **{f"group:{key}": text for key, text in panel_zh.GROUPS.items()},
           **{f"option:{key}": " ".join(words) for key, words in panel_zh.OPTIONS.items()}}
for key, text in chinese.items():
    if not text or key in VALUES:
        continue
    check(bool(CHINESE.search(text)), f"ZH:{key} is not Chinese")
    check(not re.search(r"[A-Za-z]", bare(text)), f"ZH:{key} keeps English: {text}")
    check(not LATIN_PUNCTUATION.search(bare(text)), f"ZH:{key} has half-width punctuation: {text}")
    check(not any(word in text for word in NOT_THE_GAME), f"ZH:{key} uses a word the game does not: {text}")
english = {**own, **{f"option:{option.identifier}": f"{option.display_name} {option.description}"
                     for option in (*settings.TEAM, settings.bars)}}
for key, text in english.items():
    zh = chinese.get(key, "")
    for pattern, word in NAMES:
        if re.search(pattern, bare(text), re.IGNORECASE):
            check(word in zh, f"ZH:{key} should name {word} as the game does: {zh}")
for key, text in chinese.items():
    for quoted in QUOTED.findall(text):
        check(quoted in panel_zh.TEXT.values(), f"ZH:{key} quotes a button that does not show: {quoted}")

for failure in failures:
    print(f"ECHEC | {failure}")
print("RESULTAT:", "TOUS LES TESTS PASSENT" if not failures else f"{len(failures)} ECHEC(S)")
sys.exit(1 if failures else 0)
