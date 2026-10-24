"""Tests the companions' bars at the left of the screen (companions/bars.py) and their names (bars_names.py):
shown as the mod's option says; the two packages' names read from the constants, released ones, none when
unread or one is no package's name; the game's Paks found from where the mod lies, the package found there or
not; each companion followed rank by rank with its name shown, its health and shield, then each dead one on its
way back, its health empty and marked dead, a called one not shown, MOST at most; published every EVERY_S of
the team's beat with whether the option shows them and the hunter aimed at, a failure stopping them, said, once;
started when either package is installed, the service's port held or the constants unread said; the game's
language asked only with the parameters expected, the names of its table, its language without the country,
the English for a name it lacks or a table that cannot be read; the team publishing them on its beat and
stopping them with itself. It Follows' option and its session starting them: its test_session_team.py."""

import json
import math
import pathlib
import sys
import tempfile
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

import companion_fixture as fake  # noqa: E402
from characters.companions import bars, bars_names, team as team_module  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def notes(event: str) -> list[dict]:
    found = [json.loads(text.removeprefix("[Characters] ")) for text in state["info"]
             if text.startswith("[Characters] {")]
    return [line for line in found if line["event"] == event]


def ns(**fields: object) -> types.SimpleNamespace:
    return types.SimpleNamespace(**fields)


check("published every quarter of a second", bars.EVERY_S == 0.25)

game_dir = pathlib.Path("W:/Games/Borderlands 4")
inside = game_dir / "sdk_mods" / "it_follows.sdkmod" / "it_follows" / "characters" / "companions" / "bars.py"
check("the game's Paks found from where the mod lies", bars.paks(inside) == game_dir / "OakGame" / "Content" / "Paks"
      and bars.paks(pathlib.Path("C:/elsewhere/it_follows/companions/bars.py")) is None)
# Kept until the end: start() below looks there for the package.
folder = tempfile.TemporaryDirectory()
root = pathlib.Path(folder.name)
installed_here = root / "SDK_Mods" / "companions" / "characters" / "companions" / "bars.py"


def read(name: str) -> str:
    return (HERE / "characters" / "assets" / name).read_text(encoding="utf-8")


PAKS = bars.packages(read)
check("the packages' names, their released ones, from the constants", PAKS == {
      "bars": "it-follows-companion-bars_999_P.pak", "names": "it-follows-hunter-names_999_P.pak"})
check("the constants unread: no package", bars.packages({}.get) == {} and bars.packages(lambda name: "{") == {})
check("a name that is a path, or no package's: none", bars.packages(lambda name: json.dumps({
      "barsPak": "../evil_P.pak", "namesPak": "it-follows-hunter-names_999_P.pak"})) == {}
      and bars.packages(lambda name: json.dumps({"barsPak": "bars.txt", "namesPak": "n_P.pak"})) == {}
      and bars.packages(lambda name: json.dumps({"barsPak": 3, "namesPak": "n_P.pak"})) == {})
check("no package in Paks: not installed", bars.installed(installed_here, read=read) is False)
(root / "OakGame" / "Content" / "Paks").mkdir(parents=True)
(root / "OakGame" / "Content" / "Paks" / PAKS["bars"]).write_bytes(b"pak")
check("the package in Paks: installed, whatever the folder's case", bars.installed(installed_here, read=read) is True
      and bars.installed(installed_here, "names", read) is False
      and bars.installed(installed_here, read={}.get) is False)


def follow(name: str, rank: int, health: float | None, shield: float | None) -> types.SimpleNamespace:
    return ns(companion=name, rank=rank, tough=ns(health=lambda: health, shield_share=lambda: shield))


NAMES = {"Decrepit Frame": "Châssis vétuste", "Vex": "Vex"}
follows = [follow("Vex", 2, 0.5, 0.25), follow("Decrepit Frame", 0, 1.0, None)]
waiting = [{"companion": "Rafa", "after_s": 45.0}, {"companion": "Crankus", "after_s": 0.0}]
check("each followed rank by rank, its name shown; then each dead one, empty, marked; one called not shown",
      bars.rows(follows, waiting, NAMES) == [("Châssis vétuste", 1.0, None, False), ("Vex", 0.5, 0.25, False),
                                             ("Rafa", 0.0, None, True)])
check("MOST at most", len(bars.rows([follow("Vex", rank, 1.0, 1.0) for rank in range(6)],
                                    [{"companion": "Rafa", "after_s": 45.0}] * 6, {})) == bars.kinds.MOST)


class Service:
    def __init__(self, fails_with: Exception | None = None) -> None:
        self.published, self.fails_with, self.asked, self.stops = [], fails_with, 7, 0

    def publish(self, rows: list, shown: bool, aimed: str | None) -> None:
        if self.fails_with is not None:
            raise self.fails_with
        self.published.append((rows, shown, aimed))

    def stop(self) -> bool:
        self.stops += 1
        return True


clock = fake.Clock()
team = ns(active=lambda: follows, respawns=ns(waiting=waiting))
service = Service()
looks: list = []
# The mod's option, as Bars reads it (shown).
option = {"shown": False}
shown = bars.Bars(service, NAMES, clock, lambda: option["shown"], lambda: "pc")
shown.aimed = types.SimpleNamespace(look=lambda pc, seen, names: looks.append((pc, seen, names)) or "Vex")
shown.beat(team)
clock.now += 0.1
shown.beat(team)
check("published at once, then not before EVERY_S", len(service.published) == 1 and shown.published == 1)
check("with the option's value and the hunter aimed at, looked for among those followed", service.published[0] == (
      bars.rows(follows, waiting, NAMES), False, "Vex") and looks == [("pc", follows, NAMES)])
option["shown"] = True
clock.now += 0.15
shown.beat(team)
check("published again EVERY_S later, the mod's option read again", len(service.published) == 2
      and service.published[1][1] is True)
option["shown"] = False
looking = bars.Bars(service, NAMES, clock, lambda: False)
check("the hunter aimed at: aimed.py's, its clock the team's", isinstance(looking.aimed, bars.aimed.Aimed)
      and looking.aimed.clock is clock)
state["info"].clear()
shown.stop("stopped")
shown.stop("again")
said = notes("companion_bars_stop")
check("stopped once, said with what was published and asked, and how long the stop held the game",
      service.stops == 1 and len(said) == 1 and isinstance(said[0].pop("stop_ms"), float)
      and said == [{"event": "companion_bars_stop", "run": 0, "why": "stopped", "published": 2, "asked": 7,
                   "stopped": True}])
check("due at their next publish, never once stopped", looking.due() == looking.next_at and shown.due() == math.inf)
broken = Service(RuntimeError("no"))
failing = bars.Bars(broken, NAMES, clock, lambda: False, lambda: None)
failing.beat(team)
check("a publish that fails: the bars stopped, said", failing.done == "failed:RuntimeError:no" and broken.stops == 1
      and notes("companion_bars_stop")[-1]["why"] == "failed:RuntimeError:no")
clock.now += 1.0
failing.beat(team)
check("nothing more after", broken.stops == 1 and failing.published == 0)

CONSTANTS = (HERE / "characters" / "assets" / "companion_bars.json").read_text(encoding="utf-8")
TABLE = json.dumps({"version": 1, "names": {"fr": {"Decrepit Frame": "Châssis vétuste", "Crankus": "Crankus"},
                                            "zh-Hans": {"Crankus": "克兰库斯"}}})
FILES = {bars.CONSTANTS: CONSTANTS, bars_names.TABLE: TABLE}


class Served:
    """bars_service.CompanionBars as start() makes it: start answers OPEN."""
    OPEN = True

    def __init__(self, wire: object, constants: dict, said: object) -> None:
        self.constants, self.asked = constants, 0

    def start(self) -> bool:
        return Served.OPEN

    def port(self) -> int:
        return self.constants["port"]

    def stop(self) -> bool:
        return True


bars.bars_service = ns(CompanionBars=Served)


def culture_library(parameters: list, value: object) -> None:
    props = [ns(Name=name, Class=ns(Name=kind), PropertyFlags=0x80 | (0x400 if returned else 0))
             for name, kind, returned in parameters]
    library = ns(_find=lambda name: ns(_properties=lambda: iter(props)),
                 ClassDefaultObject=ns(GetCurrentCulture=lambda: value))
    state["classes"]["KismetInternationalizationLibrary"] = library


culture_library(bars_names.EXPECTED, "fr")
state["info"].clear()
check("neither package: nothing, said", bars.start(clock, lambda: False, FILES.get, inside) is None
      and notes("companion_bars_off")[-1]["why"] == "no_package")
Served.OPEN = False
check("the port held: nothing, said", bars.start(clock, lambda: False, FILES.get, installed_here) is None
      and notes("companion_bars_off")[-1]["why"] == "no_port")
Served.OPEN = True
check("the constants unread: nothing, said", bars.start(clock, lambda: False, {}.get, installed_here) is None
      and notes("companion_bars_off")[-1]["why"].startswith("failed:"))
started = bars.start(clock, lambda: True, FILES.get, installed_here)
check("started: the port, the language, the names and the packages said", isinstance(started, bars.Bars)
      and notes("companion_bars_start")[-1] == {"event": "companion_bars_start", "run": 0,
                                                "port": json.loads(CONSTANTS)["port"], "every_s": 0.25,
                                                "culture": "fr", "culture_read": "read", "names": "table",
                                                "bars": True, "names_pak": False}
      and started.names["Decrepit Frame"] == "Châssis vétuste" and started.names["Vex"] == "Vex"
      and started.shown() is True)
paks_here = root / "OakGame" / "Content" / "Paks"
(paks_here / PAKS["bars"]).unlink()
check("the bars' package gone: not installed", bars.installed(installed_here, read=read) is False)
(paks_here / PAKS["names"]).write_bytes(b"pak")
check("the aimed bar's package alone: started too, said", isinstance(bars.start(clock, lambda: False, FILES.get,
      installed_here), bars.Bars) and notes("companion_bars_start")[-1]["bars"] is False
      and notes("companion_bars_start")[-1]["names_pak"] is True)

check("the language read when its parameters are the expected ones", bars_names.culture() == ("fr", "read"))
culture_library([("ReturnValue", "TextProperty", True)], "fr")
check("other parameters: never called, said", bars_names.culture() == (None, "parameters_differ"))
culture_library(bars_names.EXPECTED, "../fr")
check("an answer that is no language: none", bars_names.culture() == (None, "no_culture"))
del state["classes"]["KismetInternationalizationLibrary"]
check("the library missing: none, said", bars_names.culture()[1].startswith("failed:"))

check("the language's own names, the English for one it lacks, the hunters their own", bars_names.shown(
      "fr", FILES.get)[0] == {**{kind.name: kind.name for kind in bars_names.kinds.ALL},
                              "Decrepit Frame": "Châssis vétuste"})
check("a language with its country: the one without", bars_names.shown("zh-Hans-CN", FILES.get)[1] == "table"
      and bars_names.shown("fr-FR", FILES.get)[0]["Decrepit Frame"] == "Châssis vétuste")
check("a language the table lacks: the English", bars_names.shown("xx", FILES.get)[0]["Decrepit Frame"]
      == "Decrepit Frame")
check("no language: the English, said", bars_names.shown(None, FILES.get)[1] == "english:no_culture")
check("another version of the table: the English, said", bars_names.shown("fr", {
      bars_names.TABLE: json.dumps({"version": 2, "names": {}})}.get)[1] == "english:table_version")
check("a table unread or broken: the English, said", bars_names.shown("fr", {}.get)[1] == "english:table_unread"
      and bars_names.shown("fr", {bars_names.TABLE: "{"}.get)[1] == "english:table_unread"
      and bars_names.shown("fr", {bars_names.TABLE: json.dumps({"version": 1, "names": {"fr": {
          "Crankus": 3}}})}.get)[1] == "english:table_unread")
check("the trials' table, moved into the mod, read as it is", bars_names.shown("fr", lambda name: (
      HERE / "characters" / "assets" / name).read_text(encoding="utf-8"))[0]["Brine Type M"] == "Saumure type M")
reads: list = []


def counted(name: str) -> str:
    reads.append(name)
    return FILES[name]


check("a window in French: the allies' names in French, the hunters their own",
      bars_names.in_window("FR", counted)["Decrepit Frame"] == "Châssis vétuste"
      and bars_names.in_window("FR", counted)["Vex"] == "Vex")
check("read once per language", reads == [bars_names.TABLE])
check("a window in English: the names the team knows them by, nothing read",
      bars_names.in_window("EN", counted)["Decrepit Frame"] == "Decrepit Frame" and reads == [bars_names.TABLE])
check("a language no window offers: the English, never kept", bars_names.in_window("XX", counted)["Crankus"]
      == "Crankus" and "XX" not in bars_names._in_window)


class Published:
    """Bars always due: the team asks them at each of its beats."""

    def __init__(self) -> None:
        self.beats, self.stopped = 0, None

    def due(self) -> float:
        return -math.inf

    def beat(self, team: object) -> None:
        self.beats += 1

    def stop(self, why: str) -> None:
        self.stopped = why


game = fake.Game(state)
crew = team_module.Team(clock, fake.Births(game))
crew.start(["Crankus"])
crew.bars = published = Published()
crew.beat()
crew.beat()
check("the team publishes them on its beat", published.beats == 2)
crew.stop("stopped")
check("the team stopped: the bars too, with why", published.stopped == "stopped" and crew.bars is None)

folder.cleanup()

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
