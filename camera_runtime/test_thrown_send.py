"""One thrown object is moved into the hunter's left hand and sent from there to the crosshair's point at its speed;
a grenade's payload, a point too close, a hand missing or a move the game refuses leave it as the game made it, and
a value the game should never give stops it."""

import math
import pathlib
import sys
import unittest
from types import SimpleNamespace as NS

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from apex_camera_runtime import thrown_aim  # noqa: E402
from apex_camera_runtime.thrown_send import ThrowSender  # noqa: E402

# Measured on 2026-10-21 (rayons-3.txt, third person), the camera at the origin facing X: the knife born 178 cm
# ahead, 8 cm left and 26 cm up; the body's left hand 257 cm ahead, 66 cm right and 21 cm down; a wall at 1249 cm.
SPAWN, HAND, WALL = (178.0, -8.0, 26.0), (257.0, 66.0, -21.0), 1249.0
POINT = (WALL, 0.0, 0.0)


def unit(vector):
    length = math.sqrt(sum(part * part for part in vector))
    return tuple(part / length for part in vector)


def vec(point):
    return NS(X=point[0], Y=point[1], Z=point[2])


class Thrown:
    def __init__(self, at=SPAWN, speed=4000.0, aim=POINT, accept=True):
        # The game aims the throw at its own crosshair point.
        self.at, self.accept, self.Name = at, accept, "jakobs_grenade_1"
        self.velocity = tuple(speed * part for part in unit([p - a for p, a in zip(aim, at)]))
        self.MovementComponent = NS(Velocity=None)
        self.placed = []

    def K2_GetActorLocation(self):
        return vec(self.at)

    def GetVelocity(self):
        return vec(self.velocity)

    def K2_SetActorLocation(self, where, sweep, _hit, teleport):
        self.placed.append(((where.X, where.Y, where.Z), sweep, teleport))
        return self.accept, NS()


class ThrowSenderTests(unittest.TestCase):
    def setUp(self):
        self.camera, self.hit = [(0.0, 0.0, 0.0)], [(True, NS(Distance=WALL))]
        self.sockets = {"FX_L_Hand": HAND, "L_Hand": (250.0, 69.0, -19.0)}
        mesh = NS(DoesSocketExist=lambda name: name in self.sockets,
                  GetSocketLocation=lambda name: vec(self.sockets[name]))
        self.pawn = NS(Mesh=mesh)
        manager = NS(GetCameraLocation=lambda: vec(self.camera[0]), GetCameraRotation=lambda: NS(Pitch=0.0, Yaw=0.0))
        self.pc = NS(PlayerCameraManager=manager)
        sdk = NS(make_struct=lambda name, **fields: NS(kind=name, **fields))
        self.sender = ThrowSender(sdk, NS(SphereTraceSingle=lambda *_args: self.hit[0]))

    def send(self, thrown):
        return self.sender.send(self.pc, self.pawn, thrown)

    def test_the_knife_leaves_the_left_hand_for_the_crosshair_at_its_speed(self):
        knife = Thrown()
        sent, detail = self.send(knife)
        self.assertTrue(sent)
        self.assertEqual(knife.placed, [(HAND, False, True)])
        velocity = knife.MovementComponent.Velocity
        expected = tuple(4000.0 * part for part in unit([p - h for p, h in zip(POINT, HAND)]))
        self.assertEqual(velocity.kind, "Vector")
        for got, wanted in zip((velocity.X, velocity.Y, velocity.Z), expected):
            self.assertAlmostEqual(got, wanted, places=6)
        self.assertRegex(detail, r"^hand_cm=118 turn_deg=\d+\.\d crosshair_cm=1249$")

    def test_with_nothing_under_the_crosshair_it_flies_far_along_its_line(self):
        self.hit[0] = (False, NS())
        far = (thrown_aim.NOTHING_CM, 0.0, 0.0)
        knife = Thrown(aim=far)
        sent, detail = self.send(knife)
        velocity = knife.MovementComponent.Velocity
        direction = unit((velocity.X, velocity.Y, velocity.Z))
        wanted = unit([f - h for f, h in zip(far, HAND)])
        self.assertTrue(sent and detail.endswith("crosshair_cm=none"))
        self.assertAlmostEqual(sum(a * b for a, b in zip(direction, wanted)), 1.0, places=9)

    def test_the_hand_falls_back_on_the_bone_without_the_effect_socket(self):
        del self.sockets["FX_L_Hand"]
        knife = Thrown()
        self.send(knife)
        self.assertEqual(knife.placed[0][0], (250.0, 69.0, -19.0))

    def test_what_cannot_be_sent_is_left_as_the_game_made_it(self):
        cases = (("not_a_throw", Thrown(at=(2000.0, 0.0, 0.0))), ("not_a_throw", Thrown(at=(150.0, 60.0, -180.0))),
                 ("move_refused", Thrown(accept=False)))
        for reason, thrown in cases:
            self.assertEqual(self.send(thrown), (False, reason))
            self.assertIsNone(thrown.MovementComponent.Velocity)
        self.hit[0] = (True, NS(Distance=300.0))
        close = Thrown()
        self.assertEqual(self.send(close), (False, "too_close"))
        self.assertEqual(close.placed, [])
        self.sockets.clear()
        self.assertEqual(self.send(Thrown()), (False, "no_hand"))

    def test_a_value_the_game_should_never_give_raises(self):
        self.camera[0] = (float("nan"), 0.0, 0.0)
        with self.assertRaises(ValueError):
            self.send(Thrown())
        self.camera[0] = (0.0, 0.0, 0.0)
        for broken in ((True,), ("yes", NS(Distance=1.0)), (True, NS(Distance=-5.0)),
                       (True, NS(Distance=float("inf")))):
            self.hit[0] = broken
            with self.assertRaises(ValueError):
                self.send(Thrown())


if __name__ == "__main__":
    result = unittest.main(exit=False).result
    print("RESULTAT:", "OK" if result.wasSuccessful() else "ECHEC")
    raise SystemExit(not result.wasSuccessful())
