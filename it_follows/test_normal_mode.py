"""Tests the normal mode while it is on (normal/mode.py), with its game played whole (normal/play.py and its pieces):
turned on without a game it waits, its beat hooked under its own name, the reason written once however many seconds
pass; from a vehicle and in a game of several players it waits, each reason written when it changes; the character
found, it plays at the next second at its level: the damage taken raised, the camp near grown, and the second after,
the enemy the census reads given the level; the game left (the character's weak pointer emptied), it gives back what
the game still holds and waits again, the dodge files kept opened, then plays in the next game; turned on in a game,
it plays at once; turned off, its beat unhooked, the game it played in given back, then the dodge files."""

import json
import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

import census_fixture  # noqa: E402
import aim_fixture  # noqa: E402
import param_fixture as fx  # noqa: E402
from it_follows import gbx_param, report  # noqa: E402
from it_follows.normal import dodge_speed, levels, mode as mode_module, options  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def notes() -> list[dict]:
    """Every line It Follows wrote since the last call."""
    lines = [json.loads(text.split(" ", 2)[2]) for text in state["info"] if text.startswith(report.PREFIX + " {")]
    state["info"].clear()
    return lines


def events() -> list[str]:
    return [line["event"] for line in notes() if line["event"] != "call"]


def players(count: int) -> None:
    world = types.SimpleNamespace(GameState=types.SimpleNamespace(PlayerArray=[object()] * count))
    sys.modules["mods_base"].ENGINE = types.SimpleNamespace(GameViewport=types.SimpleNamespace(World=world))


def driving() -> types.SimpleNamespace:
    return types.SimpleNamespace(OakCharacter=None,
                                 Pawn=types.SimpleNamespace(Class=types.SimpleNamespace(Name="OakVehicle_C")))


def hunter() -> types.SimpleNamespace:
    return types.SimpleNamespace(freed=False, K2_GetActorLocation=lambda: sdk_stubs.vector(0.0, 0.0),
                                 DamageState=types.SimpleNamespace(DamageTakenMultiplier=types.SimpleNamespace(
                                     BaseValue=1.0, Value=1.0)))


def psycho(memory: fx.Memory, family: fx.Built) -> object:
    """An enemy the census reads, with its own copy of its family's dodge file, a speed and a zone."""
    zone = census_fixture.Zone(1000.0, "Zone_Camp", radius_cm=4000.0)
    pawn = census_fixture.enemy("Char_PsychoBasic_Male", 1000.0, census_fixture.PSYCHO, zone)
    pawn.fields["AIDodgeState"] = fx.build(memory, "AIDodgeState",
                                           {**fx.copy_of(memory, family), "CurrentDodgeData": family})
    pawn.CharacterMovement.fields["MaxGroundSpeedScale"] = types.SimpleNamespace(Value=1.0)
    # A shield of the game's already: the mode gives none (normal/shields.py, tested on its own).
    pawn.HealthState.HealthTypeStates = [types.SimpleNamespace(
        HealthType=types.SimpleNamespace(_name="HealthType_AI_Energy"))]
    pawn.zone = zone
    pawn.gun = aim_fixture.Behaviour("OakWeapon_1.UM0_PC")
    pawn.fields["ActiveWeapons"] = aim_fixture.weapons([pawn.gun])
    return pawn


try:
    failures: list[str] = []
    notes()  # the mod's own lines at its import
    memory = fx.Memory()
    family = fx.dodge_file(memory, "DodgeData_Psycho")
    enemy = psycho(memory, family)
    camp = fx.camp("OakSpawner_Bandits", 200.0, fx.camp_style(memory, 4), [])
    state["all"] = {"OakCharacter": [enemy], "Spawner": [camp]}
    settings = options.Settings(levels.LEVELS["Senior"], True)
    mode = mode_module.Mode(settings, failures.append)
    check("without a game, turned on: it waits", mode.begin(10.0) == "waiting" and not mode.playing())
    check("its beat hooked under its own name", mode_module.IDENTIFIER in state["hooks"]
          and mode_module.IDENTIFIER != "it_follows:run")
    for now in (11.0, 12.0, 13.0):
        mode.tick(now)
    lines = notes()
    check("on, then the reason it waits written once", [(line["event"], line.get("why")) for line in lines]
          == [("normal_on", None), ("normal_waiting", "no_character")])
    check("the start says the level, the allies and whether the speed is reduced",
          (lines[0]["level"], lines[0]["allies"], lines[0]["reduced"]) == ("Senior", True, False))
    state["pc"] = driving()
    mode.tick(14.0)
    player = hunter()
    state["pc"] = types.SimpleNamespace(OakCharacter=player)
    players(2)
    mode.tick(15.0)
    mode.tick(16.0)
    check("from a vehicle, then in a game of two players: each reason written as it changes",
          [line["why"] for line in notes()] == ["in_vehicle", "coop"] and not mode.playing())
    players(1)
    mode.tick(17.0)
    check("the character found: it plays at its level, the camps grown at once", mode.playing() and events()
          == ["normal_playing", "normal_taken_raised", "normal_camp_grown", "normal_camps"])
    mode.tick(18.0)
    looked = notes()
    check("the census the second after, never in the camps' second", [line["event"] for line in looked
                                                                      if line["event"] != "call"]
          == ["normal_dodges_opened", "health_raised", "normal_enemies"])
    check("the level's shields given (Senior: always); the game's own kept", [line.get("shields") for line in looked
                                                                             if line["event"] == "normal_enemies"]
          == [{"had_one": 1}])
    check("the damage taken x1.2, the camp x2, the enemy's dodges, speed and zone",
          player.DamageState.DamageTakenMultiplier.BaseValue == 1.2
          and gbx_param.read(camp.SpawnerComponent.SpawnerStyleData.InlineDef, "NumTotalActors")[1] == 8
          and gbx_param.read(enemy.AIDodgeState.DodgeBullet, "Chance")[1] == 0.45
          and enemy.CharacterMovement.MaxGroundSpeedScale.Value == 1.4
          and enemy.zone.settings.CombatTerritory.Radius == 35000.0)
    check("its aim: Senior's spread x0.88, bullets x1.08", enemy.gun.values()["aiaccuracy"] == [6.6, 6.6]
          and enemy.gun.values()["aiprojectilespeed"] == [0.486, 0.486])
    check("its dodges looked at each image", dodge_speed.IDENTIFIER in state["hooks"])
    mode.tick(19.0)
    check("a second while playing with nothing due writes nothing", notes() == [])
    player.freed = True
    mode.tick(20.0)
    check("the game left: said, given back, it waits again", not mode.playing()
          and events() == ["normal_left", "normal_given_back"] and dodge_speed.IDENTIFIER not in state["hooks"]
          and enemy.CharacterMovement.MaxGroundSpeedScale.Value == 1.0
          and gbx_param.read(enemy.AIDodgeState.DodgeBullet, "Chance")[1] == 0.15
          and enemy.gun.values()["aiaccuracy"] == [7.5, 7.5]
          and enemy.gun.values()["aiprojectilespeed"] == [0.45, 0.45])
    check("the dodge files kept opened from one game to the next", list(mode.dodges.files) == ["DodgeData_Psycho"]
          and gbx_param.read(family.DodgeBullet, "Chance")[1] == 0.45)
    state["pc"] = types.SimpleNamespace(OakCharacter=hunter())
    mode.tick(21.0)
    check("the next game: it plays again", mode.playing() and events()[0] == "normal_playing")
    mode.end("stopped")
    check("turned off: the beat unhooked, the game given back, then the dodge files",
          mode_module.IDENTIFIER not in state["hooks"] and events() == ["normal_left", "normal_given_back",
                                                                        "normal_off"]
          and gbx_param.read(family.DodgeBullet, "Chance")[1] == 0.15 and mode.dodges.files == {})
    again = mode_module.Mode(options.Settings(levels.LEVELS["Bandit"], False), failures.append)
    check("turned on in a game: it plays at once", again.begin(30.0) == "playing"
          and events()[:2] == ["normal_on", "normal_playing"])
    again.end("mod_disabled")
    check("turned off while playing", events() == ["normal_left", "normal_given_back", "normal_off"]
          and not failures)
except Exception as error:
    fails.append(f"exception {type(error).__name__}: {error}")
    print(f"ECHEC | exception {type(error).__name__}: {error}")

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
