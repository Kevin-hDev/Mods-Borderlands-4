"""Only a loaded local character at foot may receive a batch."""
import sys
import unittest
from types import SimpleNamespace as NS
from unittest.mock import patch
from vehicle_unlocks import service


class Tests(unittest.TestCase):
    def ask(self, pc, own=True, enabled=True):
        sdk = NS(find_class=lambda _: NS(ClassDefaultObject=NS(IsServer=lambda _: own)))
        with patch.dict(sys.modules, {'mods_base': NS(get_pc=lambda: pc), 'unrealsdk': sdk}):
            return service.context(NS(is_enabled=enabled))

    def test_loaded_character_and_manager_are_identity_guard(self):
        pawn, manager = object(), object()
        pc = NS(Pawn=pawn, OakCharacter=pawn, RewardsManager=manager)
        self.assertEqual(self.ask(pc), (pc, pawn, manager))

    def test_menu_disabled_vehicle_guest_and_unknown_host_refuse(self):
        pawn = object()
        pc = NS(Pawn=pawn, OakCharacter=pawn, RewardsManager=object())
        for target, own, enabled, reason in (
                (None, True, True, 'no_game'), (NS(Pawn=None), True, True, 'no_game'),
                (pc, True, False, 'disabled'), (pc, False, True, 'guest'), (pc, None, True, 'unreadable'),
                (NS(Pawn=object(), OakCharacter=None), True, True, 'vehicle'),
                (NS(Pawn=object(), OakCharacter=pawn), True, True, 'vehicle')):
            with self.subTest(reason=reason), self.assertRaises(service.Refused) as error:
                self.ask(target, own, enabled)
            self.assertEqual(error.exception.reason, reason)

    def test_missing_reward_manager_refuses(self):
        pawn = object()
        with self.assertRaises(service.Refused) as error:
            self.ask(NS(Pawn=pawn, OakCharacter=pawn))
        self.assertEqual(error.exception.reason, 'unreadable')


if __name__ == '__main__':
    result = unittest.TextTestRunner().run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
    print('RESULTAT:', 'OK' if result.wasSuccessful() else 'ECHEC')
    sys.exit(not result.wasSuccessful())
