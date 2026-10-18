"""Every word It Follows shows exists in Chinese: its window, its setting rows and their choices, its bar in the game
and its update notes, with no English left but the mod's name, the log's file name and the tags the game itself writes
in Latin letters; the game's words named as the Chinese game names them, the buttons a sentence names written as the
buttons show them, a date written as Chinese writes one (2026-10-17)."""

import pathlib
import re
import sys
import time
from types import SimpleNamespace

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

sdk_stubs.install()
from it_follows import options, panel_en, panel_fr, panel_i18n, panel_words, release_notes, texts  # noqa: E402
from it_follows import panel_zh  # noqa: E402
from it_follows.normal import options as normal_options  # noqa: E402

NOTES = HERE.parents[3] / "publication" / "nexus" / "it_follows"
VERSIONS = {"1.0.4": "1.0.4", "1.0.3": "1.0.3", "1.0.2": "1.0.2", "1.0.1": "archive/1.0.1"}
# Words that stay as they are in Chinese: the game's name in the theme's button, a percent, a buff's plus.
SAME = {"BL4"}
CHINESE = re.compile(r"[㐀-鿿]")
PLACES = re.compile(r"\{[^{}]*\}")
# Half-width punctuation has no place in a Chinese sentence; the log's file name keeps its dot.
LATIN_PUNCTUATION = re.compile(r"[,.:;()!?\[\]\"]")
KEPT = ("unrealsdk.log",)
# The game's own zh-Hans texts (Steam build 1.10.2, read 2026-10-17), counted in panel_zh's docstring: an English text
# naming one names it this way. The mod's name is taken out of the English first.
NAMES = (
    (r"\bvault hunters?\b|\bhunter's\b", "秘藏猎人"), (r"\benem(y|ies)\b", "敌人"), (r"\bkill(s|ed)?\b", "击杀"),
    (r"\bdeaths?\b", "死亡"), (r"\bboss(es)?\b", "Boss"), (r"\bshields?\b", "护盾"), (r"\brecharges?\b", "充能"),
    (r"\bhealth\b", "生命值"), (r"\bdodg", "闪避"), (r"\bcompanions?\b", "伙伴"), (r"\blevels?\b", "等级"),
    (r"\bdifficulty\b", "难度"), (r"\bmap\b", "地图"), (r"\bzones?\b", "区域"), (r"\bpaus", "暂停"),
    (r"\barmed\b|\bweapons?\b", "武器"), (r"\bbullets?\b", "子弹"), (r"\bstraighter\b|\baccura", "精准"),
    (r"\bspeed\b", "速度"), (r"\bdamage\b", "伤害"), (r"\bchase", "追击"), (r"\bon foot\b", "步行"), (r"\bvehicle\b", "载具"),
    (r"\bget out of it\b", "退出载具"), (r"\bmain menu\b", "退出至主菜单"), (r"\bload (a|your) game\b", "存档"),
    (r"\bsolo\b", "单人"), (r"\bgraphics\b", "图形"), (r"\bborderlands 4\b", "《无主之地4》"), (r"\bhardcore\b", "硬核"),
    (r"\bhorde\b", "敌群"), (r"\bbandit\b", "匪徒"), (r"\bsenior\b", "资深"), (r"\bpredator\b", "掠食者"),
    (r"\bbuff\b", "增益"), (r"\bnormal mode\b", "普通模式"), (r"^options$", "选项"), (r"\bpress a key\b", "按任意键"),
)
# Read in the game's texts and set aside: 首领 0 and BOSS 0 against Boss 85, 血量 0, 阵亡 0, 躲避 0 in a dodge, 同伴
# below 伙伴, 快速旅行 0, 强盗 below 匪徒 for a bandit; 点击 is a mouse word for a menu also used with a controller.
NOT_THE_GAME = ("首领", "BOSS", "血量", "阵亡", "躲避", "同伴", "快速旅行", "强盗", "点击")
QUOTED = re.compile(r"「([^」]*)」")
failures = []


def check(condition, message):
    if not condition:
        failures.append(message)


def bare(text):
    text = PLACES.sub("", text)
    for kept in KEPT:
        text = text.replace(kept, "")
    return text


def chinese(text):
    return text in SAME or bool(CHINESE.search(text))


def same_places(label, other, zh):
    check(sorted(PLACES.findall(other)) == sorted(PLACES.findall(zh)), f"{label} placeholders")


def same_table(label, reference, table):
    check(set(table) == set(reference), f"{label}: missing {sorted(set(reference) - set(table))}, "
                                        f"extra {sorted(set(table) - set(reference))}")
    for key in set(reference) & set(table):
        other, zh = reference[key], table[key]
        same_places(f"{label}:{key}", other, zh)
        if other == "":
            check(zh == "", f"{label}:{key} stays empty as in French")
        elif not re.search(r"[A-Za-z]", PLACES.sub("", other)):
            check(not re.search(r"[A-Za-z]", PLACES.sub("", zh)), f"{label}:{key} no English word")
        else:
            check(chinese(zh), f"{label}:{key} not Chinese: {zh!r}")


def sentence_rules(label, english, zh, punctuation=True):
    """What any Chinese sentence keeps: full-width punctuation, no long dash, the game's words, the English's numbers,
    the mod's and the log's names."""
    check(not punctuation or not LATIN_PUNCTUATION.search(bare(zh)), f"{label}: full-width punctuation only")
    check("\u2014" not in zh and "\u2013" not in zh, f"{label}: no long dash")
    for wrong in NOT_THE_GAME:
        check(wrong not in zh, f"{label}: never {wrong}, not the game's word")
    for number in re.findall(r"\d+", english.replace("Borderlands 4", "")):
        check(number in zh, f"{label}: keeps {number}")
    for name in KEPT:
        check(name not in english or name in zh, f"{label}: keeps {name}")
    check("it follows" not in english.lower() or "it follows" in zh.lower(), f"{label}: keeps the mod's name")
    if "Your game is not changed" in english:
        check("你的游戏未做任何更改" in zh, f"{label}: says the game is not changed")
    plain = PLACES.sub("", english).lower().replace("it follows", "")
    for pattern, word in NAMES:
        if re.search(pattern, plain):
            check(word in zh, f"{label}: names {pattern} as the game, {word}")


# English and French together, English the meaning: a window key added in one language only must not be forgotten.
same_table("window", {**panel_fr.TEXT, **panel_en.TEXT}, panel_zh.TEXT)
same_table("pages", panel_fr.GROUPS, panel_zh.GROUPS)
check(set(panel_zh.OPTIONS) == set(panel_fr.OPTIONS), "the same setting rows as French")

own = {key: text for key, text in panel_zh.TEXT.items() if key not in panel_zh.COMMON}
for key, text in own.items():
    # A clock is no sentence: its colon stays between the hours and the minutes.
    sentence_rules(key, panel_en.TEXT[key], text, punctuation=key != "clock_time")

rows = {option.identifier: option for option in (*options.RUN, *options.DISPLAY, *normal_options.PAGE)}
for key, (name, description) in panel_zh.OPTIONS.items():
    option = rows.get(key)
    check(option is not None, f"option {key}: a row of the mod")
    check(chinese(name) and chinese(description), f"option {key}: in Chinese")
    if option is not None:
        sentence_rules(f"option {key} name", option.display_name, name)
        sentence_rules(f"option {key}", option.description, description)

# A sentence naming a button names it as the button shows it; a row or a card's title it names, as it shows. The
# starting point's help names its CHOOSE and the card its tabs sit beside (decision 140).
buttons = {panel_zh.TEXT[key] for key in ("start", "stop", "start_choose", "start_back")}
rows_shown = {name for name, _description in panel_zh.OPTIONS.values()} | {panel_zh.TEXT["run_settings"]}
sentences = {**own, **{f"option {key}": text for key, (_name, text) in panel_zh.OPTIONS.items()}}
english = {**panel_en.TEXT, **{f"option {key}": rows[key].description for key in panel_zh.OPTIONS if key in rows}}
for key, text in sentences.items():
    for quoted in QUOTED.findall(text):
        check(quoted in buttons | rows_shown, f"{key}: 「{quoted}」 is no button, row or title of the window")
    for button in ("start", "stop"):
        word = panel_en.TEXT[button]
        if re.search(rf"\b{word}\b", english.get(key, "")) and english.get(key) != word:
            check(f"「{panel_zh.TEXT[button]}」" in text, f"{key}: names the {button} button as it shows")
check("「最大敌人数」" in own["caution"], "caution: Max enemies named as its row shows it")
# The switch at the bottom left shows 已启用 / 已停用: a sentence about it uses the same verbs.
check(panel_zh.COMMON["enabled"].removeprefix("已") in own["start_off"], "start_off: switch it on as the switch says")
check(panel_zh.COMMON["disabled"] in own["start_off"], "start_off: off as the switch says")

# Every choice of every row has its Chinese name, or is a number French and Chinese write alike.
for option in rows.values():
    for choice in getattr(option, "choices", ()):
        name = panel_zh.CHOICES.get(f"{option.identifier}:{choice}") or panel_zh.CHOICES.get(choice)
        check(name is not None or choice.isdigit(), f"choice {option.identifier}:{choice} named in Chinese")
        if name is not None:
            check(chinese(name) or not re.search(r"[A-Za-z]", name), f"choice {choice}: {name!r} not Chinese")
check(set(panel_fr.CHOICES) <= set(panel_zh.CHOICES), f"French choices missing: "
                                                        f"{sorted(set(panel_fr.CHOICES) - set(panel_zh.CHOICES))}")
check(panel_zh.CHOICES.get("level:40") == "等级 2" and panel_zh.CHOICES.get("30 min") == "30 分钟", "a level, a time limit")
levels_named = [panel_zh.CHOICES.get(name, name) for name in ("Bandit", "Senior", "Predator")]
check(levels_named == ["匪徒", "资深", "掠食者"], "the normal mode's levels as the game names a bandit and a predator")
check(all(level in own["welcome_levels"] for level in levels_named), "welcome_levels: the three levels")


# The dates, read through panel_words.py as the window reads them; Chinese put in for this check only.
def moment(day, hour, minute):
    return int(time.mktime((2026, 10, day, hour, minute, 0, 0, 0, -1)))


wired = "ZH" in panel_i18n.TABLES
panel_i18n.TABLES.setdefault("ZH", panel_zh)
now = moment(14, 18, 0)
check(panel_words.when(moment(14, 9, 7), "ZH", now) == "今天 09:07", "today in Chinese")
check(panel_words.when(moment(13, 23, 5), "ZH", now) == "昨天 23:05", "yesterday in Chinese")
check(panel_words.when(moment(2, 20, 15), "ZH", now) == "10月2日 20:15", "a date as Chinese writes it")
check(panel_words.level_in_sentence(60, "ZH") == "等级 3", "a level in a sentence")
held = panel_zh.TEXT["result_sentence:time_up"].format(held="04:37", level=panel_words.level_in_sentence(60, "ZH"))
check(held == "你在等级 3 下坚持了 04:37。敌人不再前来。", "a run's result")
check(len(panel_zh.TEXT["months"].split()) == 12, "twelve months")
if not wired:
    del panel_i18n.TABLES["ZH"]

# The bar in the game.
check(texts.CHINESE in texts.LANGUAGES, "the bar offers Chinese")
bar = texts.bar(texts.CHINESE, 12, 1, 37, 3, 277.9)
check(bar == "击杀 12   死亡 1   敌群 37   硬核 3%   04:37", f"the bar in Chinese: {bar!r}")
line = texts._BAR[texts.CHINESE]
same_places("bar", texts._BAR[texts.ENGLISH], line)
check(not re.search(r"[A-Za-z]", PLACES.sub("", line)), "the bar: no English word")



def nexus_points(version: str, folder: str) -> tuple[list[str], list[str]] | None:
    """A version's Nexus notes, English and Chinese points, their files checked; None without the Chinese file."""
    english_file, chinese_file = NOTES / folder / "changelog_en.md", NOTES / folder / "changelog_zh.md"
    check(chinese_file.is_file(), f"{folder}: changelog_zh.md")
    if not chinese_file.is_file():
        return None
    en_lines = english_file.read_text(encoding="utf-8").splitlines()
    zh_lines = chinese_file.read_bytes().decode("utf-8").splitlines()
    check(b"\r" not in chinese_file.read_bytes(), f"{folder}: LF line endings")
    check(zh_lines[0] == en_lines[0] == f"## It Follows {version}", f"{folder}: the English heading")
    return ([point[2:] for point in en_lines if point.startswith("- ")],
            [point[2:] for point in zh_lines if point.startswith("- ")])


# The update notes: as many points as the English, each the Chinese of its English one. The Nexus notes live in the
# private repository only: the public copy checks the window's own notes instead (release_notes.py).
for version, folder in VERSIONS.items():
    if NOTES.is_dir():
        points = nexus_points(version, folder)
    else:
        window = dict(release_notes.NOTES).get(version, {})
        points = list(window.get("en", ())), list(window.get("zh", ()))
        check(bool(points[1]), f"{version}: the window's notes in Chinese")
    if points is None:
        continue
    en_points, zh_points = points
    check(len(zh_points) == len(en_points), f"{folder}: {len(zh_points)} points for {len(en_points)}")
    for index, (en_point, zh_point) in enumerate(zip(en_points, zh_points)):
        check(chinese(zh_point), f"{folder} point {index + 1}: in Chinese")
        sentence_rules(f"{folder} point {index + 1}", en_point, zh_point)
        for quoted in QUOTED.findall(zh_point):
            check(quoted in rows_shown | set(panel_zh.CHOICES.values()), f"{folder}: 「{quoted}」 as the window shows")
    # The Nexus note may end with points about the mod's page rather than the game, which the window never shows: 1.0.4's
    # « Translation » (Kevin, 17 October 2026: « c'est le changelog pour nexus mod ! »).
    shown = dict(release_notes.NOTES).get(version, {}).get("zh") or ()
    check(bool(shown) and shown == tuple(zh_points[:len(shown)]),
          f"{version}: the window's notes in Chinese (docs/RUN/outils/release_notes.py)")

# Wiring: the window offers Chinese (outils/menu_languages.py).
check(panel_i18n.TABLES.get("ZH") is panel_zh, "the window offers Chinese (outils/menu_languages.py)")
group = SimpleNamespace(description="English")
check(panel_i18n.text("run", "ZH") == panel_zh.TEXT["run"] and panel_i18n.text("close", "ZH") == "关闭", "window words")
check(panel_i18n.text("start_coop", "ZH") == panel_zh.TEXT["start_coop"], "refusals in Chinese")
check(panel_i18n.group_text(group, "run", "ZH") == "", "page sentences in Chinese")
check(panel_i18n.text("start", "FR") == "START", "French unchanged")
check(panel_i18n.text("start", "EN") == "START", "English unchanged")

# A Windows console prints in cp1252, where a Chinese failure message would crash the test before its RESULTAT.
sys.stdout.reconfigure(errors="backslashreplace")
for message in failures:
    print("FAILED |", message)
print(f"RESULTAT: {'OK' if not failures else 'ECHEC'} | every word of It Follows exists in Chinese")
raise SystemExit(1 if failures else 0)
