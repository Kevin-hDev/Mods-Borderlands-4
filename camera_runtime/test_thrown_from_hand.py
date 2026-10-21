"""The watcher sends the hunter's new knife or grenade from his hand in third person; first person, a client's copy,
another's grenade and a weapon are left alone; a first throw that exists before it flies is watched until launched,
WAIT_S at most, dropped if destroyed; nothing is read again while nothing is thrown; a failure stops the unit and
stop takes it off."""

import math
import pathlib
import sys
import unittest
from types import SimpleNamespace as NS

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from camera_test_fixtures import Hooks  # noqa: E402
from apex_camera_runtime.thrown_from_hand import (FRAME, IDENTIFIER, MAX_DETAIL_LINES, MAX_SEEN,  # noqa: E402
                                                  MAX_WAITING, WAIT_S, ThrownFromHand)

# Measured on 2026-10-21 (rayons-3.txt, third person), the camera at the origin facing X: the knife born 178 cm
# ahead, 8 cm left and 26 cm up; the body's left hand 257 cm ahead, 66 cm right and 21 cm down; a wall at 1249 cm.
SPAWN, HAND, POINT = (178.0, -8.0, 26.0), (257.0, 66.0, -21.0), (1249.0, 0.0, 0.0)
ORIGIN = (0.0, 0.0, 0.0)


def unit(vector):
    length = math.sqrt(sum(part * part for part in vector))
    return tuple(part / length for part in vector)


def vec(point):
    return NS(X=point[0], Y=point[1], Z=point[2])


class Kind:
    def __init__(self, name):
        self.Name = name

    def _inherits(self, other):
        return other is self


GRENADE, WEAPON = Kind("ModularGrenade"), Kind("OakWeapon")


class Thrown:
    count = 0

    def __init__(self, owner, at=SPAWN, launched=True, authority=True, kind=GRENADE):
        Thrown.count += 1
        self.address, self.name_reads = 0x1000 + Thrown.count, 0
        self.label, self.Class, self.Instigator = f"jakobs_grenade_{Thrown.count}", kind, owner
        self.authority, self.destroyed = authority, False
        self.at, self.velocity = ORIGIN, ORIGIN
        if launched:
            self.launch(at)
        self.MovementComponent = NS(Velocity=None)
        self.placed = []

    def launch(self, at=SPAWN):
        """What the game does to a first throw some time after it exists: place it and give it its speed."""
        self.at = at
        self.velocity = tuple(4000.0 * part for part in unit([p - a for p, a in zip(POINT, at)]))

    @property
    def Name(self):
        self.name_reads += 1
        return self.label

    def _get_address(self):
        return self.address

    def K2_GetActorLocation(self):
        return vec(self.at)

    def GetVelocity(self):
        return vec(self.velocity)

    def HasAuthority(self):
        return self.authority

    def K2_SetActorLocation(self, where, sweep, _hit, teleport):
        self.placed.append(((where.X, where.Y, where.Z), sweep, teleport))
        return True, NS()


class Pawn:
    def __init__(self):
        self.Children = []
        self.Mesh = NS(DoesSocketExist=lambda name: name == "FX_L_Hand", GetSocketLocation=lambda _name: vec(HAND))


def weak(item):
    """The game's weak pointer: empty once the object is destroyed."""
    return lambda: None if getattr(item, "destroyed", False) else item


class ThrownFromHandTests(unittest.TestCase):
    def setUp(self):
        self.hooks, self.lines, self.details, self.now = Hooks(), [], [], [100.0]
        self.mode, self.camera = ["ThirdPerson"], [ORIGIN]
        self.pawn = Pawn()
        manager = NS(GetActorCameraMode=lambda _pawn: self.mode[0], GetCameraLocation=lambda: vec(self.camera[0]),
                     GetCameraRotation=lambda: NS(Pitch=0.0, Yaw=0.0))
        self.pc = NS(Pawn=self.pawn, PlayerCameraManager=manager)
        self.classes = {"ModularGrenade": GRENADE}
        sdk = NS(find_class=lambda name: self.classes.get(name),
                 make_struct=lambda name, **fields: NS(kind=name, **fields))
        kismet = NS(SphereTraceSingle=lambda *_args: (True, NS(Distance=1249.0)))
        self.unit = ThrownFromHand(self.hooks, sdk, kismet, weak, self.lines.append, self.details.append,
                                   clock=lambda: self.now[0])

    def frame(self, seconds=0.016):
        self.now[0] += seconds
        self.hooks.items[(FRAME, "POST", IDENTIFIER)](None, None, None, None)

    def throw(self, **fields):
        thrown = Thrown(self.pawn, **fields)
        self.pawn.Children.append(thrown)
        self.frame()
        return thrown

    def test_a_knife_already_there_is_only_remembered(self):
        # Thrown an instant before the camera started: where a new throw is born, yet not one to send.
        stuck = Thrown(self.pawn)
        self.pawn.Children.append(stuck)
        self.unit.start(self.pc)
        self.assertEqual(set(self.hooks.items), {(FRAME, "POST", IDENTIFIER)})
        self.frame()
        self.assertEqual((stuck.placed, self.details), ([], []))

    def test_the_hunters_new_knife_leaves_his_hand(self):
        self.unit.start(self.pc)
        knife = self.throw()
        self.assertEqual(knife.placed, [(HAND, False, True)])
        self.assertIsNotNone(knife.MovementComponent.Velocity)
        self.assertRegex(self.details[0], r"^throw from the hand object=jakobs_grenade_\d+ hand_cm=118 "
                                          r"turn_deg=\d+\.\d crosshair_cm=1249$")

    def test_a_first_throw_is_watched_until_the_game_launches_it(self):
        self.unit.start(self.pc)
        first = self.throw(launched=False)
        self.assertEqual((first.placed, self.details), ([], []))
        self.frame()
        first.launch()
        # The hunter's actors do not change when the game launches it: the waiting list is read anyway.
        self.frame()
        self.assertEqual(first.placed, [(HAND, False, True)])
        self.assertRegex(self.details[-1], r"turn_deg=\d+\.\d crosshair_cm=1249 waited_ms=\d+$")
        self.frame()
        self.assertEqual(len(first.placed), 1)

    def test_a_first_throw_destroyed_or_never_launched_is_dropped(self):
        self.unit.start(self.pc)
        gone = self.throw(launched=False)
        gone.destroyed = True
        self.frame()
        self.assertTrue(self.details[-1].endswith("reason=gone_before_launch"))
        stuck = self.throw(launched=False)
        self.frame(WAIT_S / 2)
        self.assertEqual(self.unit.left, 1)
        self.frame(WAIT_S)
        self.assertTrue(self.details[-1].endswith(f"object={stuck.label} reason=never_launched"))
        stuck.launch()
        self.frame()
        self.assertEqual((stuck.placed, self.unit.waiting), ([], []))

    def test_a_first_throw_launched_in_first_person_is_left_alone(self):
        self.unit.start(self.pc)
        first = self.throw(launched=False)
        self.mode[0] = "Default"
        first.launch()
        self.frame()
        self.assertEqual((first.placed, self.details, self.unit.waiting), ([], [], []))

    def test_the_objects_waited_for_are_bounded(self):
        self.unit.start(self.pc)
        for _ in range(MAX_WAITING + 1):
            self.throw(launched=False)
        self.assertEqual(len(self.unit.waiting), MAX_WAITING)
        self.assertTrue(self.details[-1].endswith("reason=too_many_waiting"))

    def test_first_person_is_left_alone_and_not_counted(self):
        self.mode[0] = "Default"
        self.unit.start(self.pc)
        knife = self.throw()
        self.assertEqual((knife.placed, self.details), ([], []))

    def test_a_clients_copy_is_left_as_thrown(self):
        self.unit.start(self.pc)
        client = self.throw(authority=False)
        self.assertEqual(client.placed, [])
        self.assertTrue(self.details[-1].endswith("reason=client"))

    def test_another_hunters_grenade_and_a_weapon_are_never_touched(self):
        self.unit.start(self.pc)
        other = Thrown(NS(Name="Bandit"))
        weapon = Thrown(self.pawn, kind=WEAPON)
        self.pawn.Children += [other, weapon]
        self.frame()
        self.assertEqual((other.placed, weapon.placed, self.details), ([], [], []))

    def test_nothing_is_read_again_while_nothing_is_thrown(self):
        self.unit.start(self.pc)
        knife = self.throw()
        reads = knife.name_reads
        for _ in range(5):
            self.frame()
        self.assertEqual(knife.name_reads, reads)

    def test_a_failure_stops_the_unit_until_the_next_start(self):
        self.unit.start(self.pc)
        self.camera[0] = (float("nan"), 0.0, 0.0)
        self.throw()
        self.assertEqual(self.lines, ["throws from the hand stopped: ValueError"])
        self.camera[0] = ORIGIN
        self.assertEqual(self.throw().placed, [])
        self.unit.start(self.pc)
        self.assertEqual(len(self.throw().placed), 1)

    def test_stop_takes_the_hook_off_and_sums_up(self):
        self.unit.start(self.pc)
        self.throw()
        self.throw(authority=False)
        self.throw(launched=False)
        self.unit.stop()
        self.assertEqual(self.hooks.items, {})
        self.assertEqual(self.details[-1], "throws from the hand sent=1 left=1")
        self.assertEqual(self.unit.waiting, [])
        self.unit.stop()
        self.assertEqual(self.details[-1], "throws from the hand sent=1 left=1")

    def test_a_game_without_the_thrown_class_refuses_to_start(self):
        self.classes.clear()
        with self.assertRaises(LookupError):
            self.unit.start(self.pc)
        self.assertEqual(self.hooks.items, {})

    def test_detail_lines_and_remembered_objects_are_bounded(self):
        self.unit.start(self.pc)
        for _ in range(MAX_SEEN + 10):
            self.throw()
        self.assertEqual(len(self.details), MAX_DETAIL_LINES)
        self.assertLessEqual(len(self.unit.seen), MAX_SEEN)
        self.assertEqual(self.unit.sent, MAX_SEEN + 10)


if __name__ == "__main__":
    result = unittest.main(exit=False).result
    print("RESULTAT:", "OK" if result.wasSuccessful() else "ECHEC")
    raise SystemExit(not result.wasSuccessful())
