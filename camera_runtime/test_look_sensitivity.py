"""The mouse's and the controller's look multipliers: scaled in third person and Orbit by the look, aim or weapon
factor, the game's value back elsewhere and at stop, a game write taken as the new base, a new multiplier followed,
one failure stopping the unit."""

import enum
import unittest
from types import SimpleNamespace as NS

from apex_camera_runtime import look_multiplier
from apex_camera_runtime.look_multiplier import FIND_NS
from apex_camera_runtime.look_sensitivity import LookSensitivity, factor

GAME = (0.07, 0.07, 0.07)


class WeaponType(enum.IntEnum):
    Pistol, SMG, Shotgun, AssaultRifle, SniperRifle, Heavy = 1, 2, 3, 4, 5, 6


def scalar(values=GAME):
    return NS(Class=NS(Name="InputModifierScalar"), Scalar=NS(X=values[0], Y=values[1], Z=values[2]))


def mapping(modifiers, action="Action_Look", key="Mouse2D"):
    return NS(Action=NS(Name=action), Key=NS(KeyName=key), Modifiers=modifiers)


class Settings:
    def __init__(self, look=0.5, aim=2.0, weapons=None):
        self.factors = (look, aim) if weapons is None else (look, aim, weapons)

    def look_sensitivity(self):
        return self.factors


class SensitivityTests(unittest.TestCase):
    def setUp(self):
        self.modifier = scalar()
        self.gone = set()
        self.mappings = [mapping([NS(Class=NS(Name="InputModifierNegate"))], key="Gamepad_Right2D"),
                         mapping([NS(Class=NS(Name="InputModifierNegate")), self.modifier])]
        self.mode = "ThirdPerson"
        self.weapon = NS(_get_address=lambda: 0x7FF600001000)
        self.animation = NS(CurrentWeapon=self.weapon, WeaponType=WeaponType.Pistol)
        self.actor = NS(ZoomState=NS(bWantsToZoom=False), ActiveWeapons=NS(Slots=[NS(Weapon=self.weapon)]),
                        Mesh=NS(GetAnimInstance=lambda: self.animation))
        manager = NS(GetActorCameraMode=lambda _actor: self.mode)
        self.pc = NS(PlayerInput=NS(EnhancedActionMappings=self.mappings), OakCharacter=self.actor,
                     PlayerCameraManager=manager)
        self.lines = []
        self.unit = LookSensitivity(lambda item: (lambda: None if id(item) in self.gone else item), id,
                                    self.lines.append)
        self.settings = Settings()
        self.now = 0

    def tick(self, settings=None):
        self.now += 16_000_000
        self.unit.sync(settings or self.settings, self.pc, self.now)

    def value(self, modifier=None):
        return look_multiplier.read(modifier or self.modifier)

    def assertValue(self, expected, modifier=None):
        for got, wanted in zip(self.value(modifier), expected):
            self.assertAlmostEqual(got, wanted, places=6)

    def test_the_factor_follows_the_mode_and_the_aim(self):
        weapons = {"pistol": 1.5}
        self.assertEqual(factor((0.5, 2.0, weapons), "ThirdPerson", True, "pistol"), 1.5)
        self.assertEqual(factor((0.5, 2.0, weapons), "ThirdPerson", True, "smg"), 2.0)
        self.assertEqual(factor((0.5, 2.0, weapons), "ThirdPerson", False, "pistol"), 0.5)
        self.assertEqual(factor((0.5, 2.0, weapons), "FirstPerson", True, "pistol"), 1.0)
        self.assertEqual(factor((0.5, 2.0), "ThirdPerson", False), 0.5)
        self.assertEqual(factor((0.5, 2.0), "Orbit", True), 2.0)
        self.assertEqual(factor((0.5, 2.0), "FirstPerson", True), 1.0)

    def test_third_person_scales_and_first_person_gives_the_game_value_back(self):
        self.tick()
        self.assertValue((0.035, 0.035, 0.035))
        self.actor.ZoomState.bWantsToZoom = True
        self.tick()
        self.assertValue((0.14, 0.14, 0.14))
        self.mode = "FirstPerson"
        self.tick()
        self.assertValue(GAME)
        self.assertIsNone(self.unit.multipliers[0].written)

    def test_the_factor_never_compounds_over_frames(self):
        for _ in range(100):
            self.tick()
        self.assertValue((0.035, 0.035, 0.035))

    def test_a_game_write_becomes_the_new_base(self):
        self.tick()
        look_multiplier.write(self.modifier, (0.1, 0.1, 0.1))
        self.tick()
        self.assertValue((0.05, 0.05, 0.05))
        self.unit.stop()
        self.assertValue((0.1, 0.1, 0.1))

    def test_stop_gives_the_game_value_back(self):
        self.tick()
        self.unit.stop()
        self.assertValue(GAME)

    def test_a_mod_without_the_setting_changes_nothing(self):
        self.unit.sync(NS(), self.pc, 1)
        self.assertValue(GAME)

    def test_100_percent_writes_nothing(self):
        self.tick(Settings(1.0, 1.0))
        self.assertValue(GAME)
        self.assertIsNone(self.unit.multipliers[0].written)

    def test_a_new_multiplier_is_followed_and_the_old_one_left_alone(self):
        self.tick()
        fresh = scalar()
        self.mappings[1] = mapping([fresh])
        self.gone.add(id(self.modifier))
        self.now += FIND_NS
        self.tick()
        self.assertValue((0.035, 0.035, 0.035), fresh)

    def test_the_controller_scales_its_last_multiplier_only(self):
        first, last = scalar((0.8, 0.5, 0.0)), scalar((60.0, 60.0, 0.0))
        self.mappings[0] = mapping([NS(Class=NS(Name="GbxInputModifier_Acceleration")), first,
                                    NS(Class=NS(Name="InputModifierScaleByDeltaTime")), last],
                                   key="Gamepad_Right2D")
        self.tick()
        self.assertValue((0.8, 0.5, 0.0), first)
        self.assertValue((30.0, 30.0, 0.0), last)
        self.assertValue((0.035, 0.035, 0.035))
        self.unit.stop()
        self.assertValue((60.0, 60.0, 0.0), last)

    def test_the_held_weapon_type_replaces_the_aim_value_while_aiming(self):
        settings = Settings(weapons={"pistol": 1.5})
        self.actor.ZoomState.bWantsToZoom = True
        self.tick(settings)
        self.assertValue((0.105, 0.105, 0.105))
        self.animation.WeaponType = WeaponType.SniperRifle
        self.tick(settings)
        self.assertValue((0.14, 0.14, 0.14))
        # A weapon type without a value in the file (one from before its row): the aim value stays.
        self.animation.WeaponType = WeaponType.Heavy
        self.tick(settings)
        self.assertValue((0.14, 0.14, 0.14))
        self.tick(Settings(weapons={"heavy": 0.5}))
        self.assertValue((0.035, 0.035, 0.035))
        self.actor.ZoomState.bWantsToZoom = False
        self.tick(settings)
        self.assertValue((0.035, 0.035, 0.035))

    def test_an_optic_zoom_uses_its_zoom_value_with_every_weapon_else_the_weapons_own(self):
        settings = Settings(weapons={"sniper": 0.5, "sniper_x2": 1.5})
        self.actor.ZoomState.bWantsToZoom = True
        self.animation.WeaponType = WeaponType.SniperRifle
        self.now += 16_000_000
        self.unit.sync(settings, self.pc, self.now, 2)
        self.assertValue((0.105, 0.105, 0.105))
        # No row for x6 (per-optic switch off, or only some zooms read): the weapon's own value.
        self.now += 16_000_000
        self.unit.sync(settings, self.pc, self.now, 6)
        self.assertValue((0.035, 0.035, 0.035))
        # A settings file from before the sniper row: the aim value.
        self.now += 16_000_000
        self.unit.sync(Settings(weapons={"pistol": 1.5}), self.pc, self.now, 3)
        self.assertValue((0.14, 0.14, 0.14))
        # No zoom (x1): the weapon's own value.
        self.tick(settings)
        self.assertValue((0.035, 0.035, 0.035))
        self.now += 16_000_000
        self.unit.sync(Settings(), self.pc, self.now, 6)
        self.assertValue((0.14, 0.14, 0.14))
        # The zoom rows count for every weapon (Kevin, 2026-10-09).
        self.animation.WeaponType = WeaponType.Pistol
        self.now += 16_000_000
        self.unit.sync(Settings(weapons={"pistol": 0.5, "sniper_x2": 1.5}), self.pc, self.now, 2)
        self.assertValue((0.105, 0.105, 0.105))
        self.now += 16_000_000
        self.unit.sync(Settings(weapons={"pistol": 0.5, "sniper_x2": 1.5}), self.pc, self.now, 3)
        self.assertValue((0.035, 0.035, 0.035))

    def test_zoom_rows_without_the_weapon_rows_fall_back_on_the_aim_value(self):
        """The per-optic and per-weapon switches are independent (Kevin, 2026-10-10)."""
        settings = Settings(weapons={"sniper_x2": 1.5})
        self.actor.ZoomState.bWantsToZoom = True
        self.animation.WeaponType = WeaponType.Pistol
        self.now += 16_000_000
        self.unit.sync(settings, self.pc, self.now, 2)
        self.assertValue((0.105, 0.105, 0.105))
        self.now += 16_000_000
        self.unit.sync(settings, self.pc, self.now, 3)
        self.assertValue((0.14, 0.14, 0.14))
        self.tick(settings)
        self.assertValue((0.14, 0.14, 0.14))

    def test_a_weapon_not_yet_in_the_animation_keeps_the_aim_value(self):
        self.actor.ZoomState.bWantsToZoom = True
        self.animation.CurrentWeapon = NS(_get_address=lambda: 0x7FF600002000)
        self.tick(Settings(weapons={"pistol": 1.5}))
        self.assertValue((0.14, 0.14, 0.14))
        self.animation.CurrentWeapon, self.animation.WeaponType = self.weapon, 3
        self.tick(Settings(weapons={"pistol": 1.5}))
        self.assertValue((0.14, 0.14, 0.14))
        self.assertFalse(self.unit.failed)

    def test_no_player_input_does_nothing(self):
        self.unit.sync(self.settings, None, 1)
        self.assertTrue(all(multiplier.written is None for multiplier in self.unit.multipliers))

    def test_a_failure_gives_the_game_value_back_and_stops(self):
        self.tick()
        self.pc.PlayerCameraManager = NS(GetActorCameraMode=lambda _actor: 1 / 0)
        self.tick()
        self.assertValue(GAME)
        self.assertTrue(self.unit.failed)
        self.assertEqual(self.lines, ["third-person sensitivity stopped: ZeroDivisionError"])
        self.pc.PlayerCameraManager = NS(GetActorCameraMode=lambda _actor: "ThirdPerson")
        self.tick()
        self.assertValue(GAME)


if __name__ == "__main__":
    result = unittest.main(exit=False).result
    print("RESULTAT:", "OK" if result.wasSuccessful() else "ECHEC")
    raise SystemExit(not result.wasSuccessful())
