"""Tests the enemies the normal mode meets (normal/enemies.py), with the real pieces: dodge_rate on a real block of
memory (param_fixture.py), speed, toughness on the health fixture, teams on a fake team library, pursuit on fake zones;
only the census is set by the test. The enemies read are met nearest first: their family's file opened and their copy
brought to it, their speed, health and zone raised, one team when the player chose it; a census that changes nothing
says nothing, a speed the game put back is written again; a dead enemy let go without a call, its speed written back,
its copy left; one gone and one no longer read alive by a complete census let go, but not by a census cut short; past
MOST the rest left out; a dodge that fails said once, the enemy still met; the nearest within reach watched; the end
gives the living everything back. The census asked for the bosses; a boss met gets its health and speed only, no
dodge, chase nor team, and is never watched; the Hardcore's factor given to every enemy held alive at once, none
called on one the game says dead, and to those met next. The Hardcore's kills: the census asked who killed; the dead
the first census reads not counted; each new body counted once, the player's (his character, his vehicle, his last
hit) and never the rest's; a body read alive again counted at its next death; the bodies remembered bounded. An
enemy no longer read alive then met again, twice: its health taken back as raised, never raised again, its own team
given back with its health at the end (audit of 15 October 2026)."""

import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

import health_fixture  # noqa: E402
import param_fixture as fx  # noqa: E402
from it_follows import census, gbx_param  # noqa: E402
from it_follows.normal import dodge_rate, enemies as enemies_module, levels, pursuit  # noqa: E402
from it_follows.seen import Seen  # noqa: E402

health_fixture.install(state)
fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


class Team:
    def __init__(self, name: str) -> None:
        self.name = name

    def __str__(self) -> str:
        return f"FGameDataHandle(15, '{self.name}', None)"


team_calls: list[tuple] = []


class TeamLibrary:
    def GetTeam(self, actor: object) -> object:
        team_calls.append(("get", actor.Name))
        return actor.team

    def SetTeam(self, actor: object, team: object) -> None:
        team_calls.append(("set", actor.Name, str(team)))
        actor.team = team


state["classes"]["GbxTeamFunctionLibrary"] = types.SimpleNamespace(ClassDefaultObject=TeamLibrary())
BANDITS, BEASTS = Team("Team_Bandit"), Team("Team_Beast")
memory = fx.Memory()
HUMAN, CAT = fx.dodge_file(memory, "DodgeData_Human"), fx.dodge_file(memory, "DodgeData_Cat", chance=1.0)


def zone(path: str) -> types.SimpleNamespace:
    return types.SimpleNamespace(settings=types.SimpleNamespace(CombatTerritory=types.SimpleNamespace(Radius=4000.0)),
                                 _path_name=lambda: path, freed=False)


def enemy(name: str, metres: float, family: object, team: Team, area: types.SimpleNamespace | None) -> Seen:
    actor = fx.enemy(memory, name, metres, family)
    actor.team, actor.pools = team, [health_fixture.Pool(100.0), None, None]
    actor.CharacterMovement = types.SimpleNamespace(MaxGroundSpeedScale=types.SimpleNamespace(Value=1.0))
    where = (metres * 100.0, 0.0, 0.0)
    return Seen(actor, name, "Char_Enemy", area, area._path_name() if area is not None else "", where, 40.0, where)


def census_reads(seens: list[Seen], dead: tuple = (), stopped: str = "complete", killed: tuple = ()) -> None:
    sighting = census.Sighting(frozenset(seen.name for seen in seens), frozenset(dead), (), killed)

    def seen_around(player: object, seconds: float | None = None, bosses: bool = False, kills: bool = False,
                    pc: object = None) -> tuple:
        asked.append((bosses, kills))
        return list(seens), {"read": len(seens), "stopped": stopped}, sighting

    census.seen_around = seen_around


asked: list[tuple] = []


def scale(seen: Seen) -> float:
    return seen.actor.CharacterMovement.MaxGroundSpeedScale.Value


def chance(seen: Seen) -> float:
    return gbx_param.read(seen.actor.AIDodgeState.DodgeBullet, "Chance")[1]


try:
    lines: list[tuple[str, dict]] = []
    level = levels.LEVELS["Bandit"]
    note = lambda event, **f: lines.append((event, f))  # noqa: E731
    announce = lambda call, log=True, **f: None  # noqa: E731
    dodges = dodge_rate.Dodges(level, note, announce)
    chase = pursuit.Pursuit(announce, level.chase_m)
    met = enemies_module.Enemies(level, True, dodges, chase, note, announce)
    camp = zone("/Game/Zone_Camp")
    near = enemy("Char_GunToter", 10.0, HUMAN, BANDITS, camp)
    mate = enemy("Char_Psycho", 30.0, HUMAN, BANDITS, camp)
    cat = enemy("Char_CatAdult", 80.0, CAT, BEASTS, None)
    player = types.SimpleNamespace(K2_GetActorLocation=lambda: fx.at(0.0))
    census_reads([cat, mate, near])
    looked = met.look(player, 10.0)
    check("the census asked for the bosses and who killed", asked == [(True, True)])
    check("three met: health, speed, one team", looked == {"met": 3, "lost": {}, "held": 3, "left_out": 0, "read": 3,
                                                          "stopped": "complete", "health": 3, "boosted": 3,
                                                          "team": "Team_Bandit"})
    check("nearest first: the dodge files opened in that order", list(dodges.files) == ["DodgeData_Human",
                                                                                         "DodgeData_Cat"])
    check("each copy brought to its file, speed x1.2, health x1.45, the zone widened, the cat in the bandits' team",
          chance(near) == 0.35 and chance(cat) == 0.35 and scale(near) == 1.2
          and near.actor.pools[0].base == 145.0 and camp.settings.CombatTerritory.Radius == 35000.0
          and cat.actor.team is BANDITS and ("set", "Char_CatAdult", str(BANDITS)) in team_calls)
    check("the nearest within 60 m watched", list(met.nearest((0.0, 0.0, 0.0))) == ["Char_GunToter", "Char_Psycho"])
    near.actor.CharacterMovement.MaxGroundSpeedScale.Value = 1.0
    check("a census that changes nothing says nothing; a speed the game put back written again",
          met.look(player, 15.0) == {} and scale(near) == 1.2)

    team_calls.clear()
    mate.actor.HealthState.bCurrentlyDead = True
    census_reads([cat, near], dead=("Char_Psycho",))
    looked = met.look(player, 20.0)
    check("a dead enemy let go without a call: its speed written back, its copy left",
          looked["lost"] == {"dead": 1} and scale(mate) == 1.0 and team_calls == [] and chance(mate) == 0.35
          and "Char_Psycho" not in met.met)
    census_reads([near], stopped="time_limit")
    check("a census cut short lets no one go", met.look(player, 25.0) == {} and "Char_CatAdult" in met.met)
    cat.actor.freed = True
    stray = enemy("Char_Stray", 20.0, HUMAN, BANDITS, None)
    census_reads([stray])
    looked = met.look(player, 30.0)
    check("one gone, one no longer read alive: let go; a new one met",
          looked["lost"] == {"gone": 1, "away": 1} and looked["met"] == 1 and list(met.met) == ["Char_Stray"]
          and scale(near) == 1.0 and team_calls[-1] != ("set", "Char_GunToter", str(BANDITS)))

    enemies_module.MOST = 2
    crowd = [enemy(f"Char_Crowd_{number}", 15.0 + number, HUMAN, BANDITS, None) for number in range(3)]
    broken = types.SimpleNamespace(Name="Char_Broken", freed=False, team=BANDITS, pools=[None, None, None],
                                   HealthState=types.SimpleNamespace(bCurrentlyDead=False),
                                   K2_GetActorLocation=lambda: fx.at(5.0),
                                   CharacterMovement=types.SimpleNamespace(
                                       MaxGroundSpeedScale=types.SimpleNamespace(Value=1.0)))
    broken_seen = Seen(broken, "Char_Broken", "Char_Enemy", None, "", (500.0, 0.0, 0.0), 40.0, (500.0, 0.0, 0.0))
    census_reads([stray, broken_seen, *crowd])
    lines.clear()
    looked = met.look(player, 35.0)
    check("past MOST the rest left out", looked["met"] == 1 and looked["left_out"] == 3 and len(met.met) == 2)
    check("a dodge that fails said once, the enemy still met", "Char_Broken" in met.met
          and [line for line in lines if line[0] != "health_raised"]
          == [("normal_enemy_failed", {"what": "dodges", "error": "AttributeError"})])

    enemies_module.MOST = 200
    boss = enemy("Char_CatBoss", 12.0, CAT, BEASTS, None)
    boss = Seen(boss.actor, boss.name, "Char_CatBoss", None, "", boss.at, 0.0, boss.at, boss=True)
    team_calls.clear()
    files = list(dodges.files)
    widened = chase.widened()
    census_reads([stray, boss])
    looked = met.look(player, 40.0)
    check("a boss met: its health and speed only, no team asked, said", looked["met"] == 1 and looked["bosses"] == 1
          and looked["health"] == 1 and looked["boosted"] == 1 and "team" not in looked and team_calls == []
          and boss.actor.pools[0].base == 145.0 and scale(boss) == 1.2)
    check("no dodge nor chase for it, and never watched", list(dodges.files) == files
          and met.met["Char_CatBoss"].family is None and chase.widened() == widened
          and "Char_CatBoss" not in met.nearest((0.0, 0.0, 0.0)))

    stray.actor.HealthState.bCurrentlyDead = True
    hardened = met.harden(1.1)
    check("the Hardcore's factor on top of the level's, given at once to every enemy held alive, none called on one "
          "the game says dead", hardened == {"not_alive": 1, "reached": 1} and stray.actor.pools[0].base == 145.0
          and abs(boss.actor.pools[0].base - 159.5) < 1e-6 and met.toughness.factor == 1.45 * 1.1)
    stray.actor.HealthState.bCurrentlyDead = False
    newcomer = enemy("Char_Newcomer", 14.0, HUMAN, BANDITS, None)
    census_reads([stray, boss, newcomer])
    met.look(player, 45.0)
    check("and to those met next", abs(newcomer.actor.pools[0].base - 159.5) < 1e-6)
    check("back to the level's", met.harden(1.0) == {"reached": 3} and boss.actor.pools[0].base == 145.0
          and newcomer.actor.pools[0].base == 145.0)
    started = enemies_module.Enemies(level, False, dodges, chase, note, announce, hard=1.05)
    check("a Hardcore's factor at the start", started.toughness.factor == 1.45 * 1.05)

    counter = enemies_module.Enemies(level, False, dodges, chase, note, announce)
    census_reads([], killed=(("Char_Old", ("none", "none")),))
    check("the dead the first census reads were there before: not counted", counter.look(player, 0.0) == {})
    census_reads([], killed=(("Char_Old", ("none", "none")), ("Char_A", ("player", "none")),
                             ("Char_B", ("vehicle", "none")), ("Char_C", ("none", "player")),
                             ("Char_D", ("other:Spectre", "other:AIController")), ("Char_E", ("none", "none"))))
    looked = counter.look(player, 10.0)
    check("each new body counted once, by what killed it: the player, his vehicle, his last hit; not a spectre",
          looked["kills"] == 3 and looked["killers"] == {"player/none": 1, "vehicle/none": 1, "none/player": 1,
                                                         "other:Spectre/other:AIController": 1, "none/none": 1})
    check("read again: not counted again", counter.look(player, 20.0) == {})
    reborn = enemy("Char_A", 20.0, HUMAN, BANDITS, None)
    census_reads([reborn])
    counter.look(player, 30.0)
    census_reads([], dead=("Char_A",), killed=(("Char_A", ("player", "none")),))
    looked = counter.look(player, 40.0)
    check("a body read alive again counted at its next death", looked["kills"] == 1 and looked["lost"] == {"dead": 1})
    enemies_module.COUNTED_MOST = 3
    census_reads([], killed=tuple((f"Char_Many_{number}", ("player", "none")) for number in range(5)))
    check("the bodies remembered bounded, the oldest forgotten first", counter.look(player, 50.0)["kills"] == 5
          and list(counter.counted) == ["Char_Many_2", "Char_Many_3", "Char_Many_4"])
    enemies_module.COUNTED_MOST = 2000

    lost = enemies_module.Enemies(level, True, dodges, pursuit.Pursuit(announce, level.chase_m), note, announce)
    keeper = enemy("Char_Keeper", 10.0, HUMAN, BANDITS, None)
    bat = enemy("Char_Bat", 20.0, HUMAN, BEASTS, None)
    census_reads([keeper, bat])
    lost.look(player, 100.0)
    census_reads([keeper])
    away = lost.look(player, 105.0)
    check("one no longer read alive: let go, nothing called on it, its health and team left as they are",
          away["lost"] == {"away": 1} and abs(bat.actor.pools[0].base - 145.0) < 1e-6 and bat.actor.team is BANDITS)
    for at in (110.0, 115.0, 120.0):
        census_reads([keeper, bat] if at != 115.0 else [keeper])
        lost.look(player, at)
    check("audit: met again twice, its health taken back as raised, never raised again (x1.45, never x2.1)",
          abs(bat.actor.pools[0].base - 145.0) < 1e-6 and "Char_Bat" in lost.met)
    lost.end()
    check("the end gives it its own health and its own team back",
          abs(bat.actor.pools[0].base - 100.0) < 1e-6 and bat.actor.team is BEASTS)

    ended = met.end()
    check("the end gives the living everything back", ended["enemies"] == 3 and ended["health"] == {"restored": 3}
          and chance(stray) == 0.15 and scale(stray) == 1.0
        and boss.actor.pools[0].base == 100.0 and scale(boss) == 1.0
        and stray.actor.pools[0].base == 100.0 and met.met == {})
except Exception as error:
    fails.append(f"exception {type(error).__name__}: {error}")
    print(f"ECHEC | exception {type(error).__name__}: {error}")

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
