"""Persist protection before granting; never grant if protection is unavailable."""
import sys
import unittest
from unittest.mock import patch
from types import SimpleNamespace as NS
from vehicle_unlocks import service, batch


class Tests(unittest.TestCase):
    def setUp(self):
        service.busy = service.locked = False

    def test_promotions_require_protection_before_delivery(self):
        from vehicle_unlocks import protection_runtime, promotion_award
        events = []
        def apply(engine, targets, guard, trace):
            guard()
            events.append('award')
            return batch.Result('delivered', len(targets))
        with patch.object(service, 'context', return_value=(1, 2, 3)), \
                patch.object(service, 'engine_for', return_value=object()), \
                patch.object(service, 'trace'), \
                patch.object(protection_runtime, 'request', side_effect=lambda: events.append('request')), \
                patch.object(protection_runtime, 'check', side_effect=lambda: events.append('check')), \
                patch.object(promotion_award, 'apply', side_effect=apply), \
                patch.object(batch, 'apply') as regular:
            result = service.run('promotions', NS(is_enabled=True))
        self.assertEqual(result.kind, 'delivered')
        self.assertEqual(events, ['request', 'check', 'award'])
        regular.assert_not_called()

    def test_protection_error_never_delivers_or_reports_already_unlocked(self):
        from vehicle_unlocks import protection_runtime, promotion_award
        with patch.object(service, 'context', return_value=(1, 2, 3)), \
                patch.object(service, 'engine_for', return_value=object()), patch.object(service, 'trace'), \
                patch.object(protection_runtime, 'request', side_effect=ValueError('version mismatch')), \
                patch.object(promotion_award, 'apply') as award, patch.object(batch, 'apply') as regular:
            result = service.run('promotions', NS(is_enabled=True))
        self.assertEqual(result.kind, 'refused')
        award.assert_not_called()
        regular.assert_not_called()


if __name__ == '__main__':
    result = unittest.TextTestRunner().run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
    print('RESULTAT:', 'OK' if result.wasSuccessful() else 'ECHEC')
    sys.exit(not result.wasSuccessful())
