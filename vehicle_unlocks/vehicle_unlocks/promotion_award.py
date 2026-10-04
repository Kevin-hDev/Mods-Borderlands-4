"""Explicit repair of vehicle-only receipts; never called on startup or a timer."""
from . import batch, config as cfg


def restore(engine, original, target):
    current = engine.snapshot()[0]
    key = target.reward.casefold()
    count = batch.counter(current)[key]
    if count > 1:
        raise RuntimeError('Duplicate receipt after delivery')
    if count == 0 and batch.counter(original)[key]:
        index = min(next(i for i, value in enumerate(original) if value.casefold() == key), len(current))
        value = next(value for value in original if value.casefold() == key)
        engine.write_unique(current[:index] + (value,) + current[index:])


def apply(engine, targets, guard, trace):
    if (not 1 <= len(targets) <= len(cfg.ACTIONS['promotions'])
            or any(target not in cfg.ACTIONS['promotions'] for target in targets)
            or len(set(targets)) != len(targets)):
        raise ValueError('Invalid promotional request')
    guard()
    expected = engine.snapshot()
    for target in targets:
        unique, pending = map(batch.counter, expected)
        if unique[target.reward.casefold()] > 1 or pending[target.reward.casefold()] > 1:
            raise ValueError('Ambiguous promotion state')
    completed, attempted = 0, False
    try:
        for target in targets:
            guard()
            if engine.snapshot() != expected:
                raise ValueError('Reward state changed')
            before = expected
            key = target.reward.casefold()
            try:
                if not batch.counter(before[1])[key]:
                    if batch.counter(before[0])[key]:
                        attempted = True
                        engine.write_unique(tuple(value for value in before[0] if value.casefold() != key))
                    guard()
                    reduced = engine.snapshot()
                    if reduced != (tuple(v for v in before[0] if v.casefold() != key), before[1]):
                        raise ValueError('Receipt removal not verified')
                    attempted = True
                    expected = batch.checked_give(engine, target, reduced)
                    if batch.counter(expected[1])[key] != 1:
                        raise ValueError('Target package not delivered')
                engine.validate(target)
                guard()
                if engine.snapshot() != expected:
                    raise ValueError('Reward state changed before opening')
                attempted = True
                expected = batch.checked_open(engine, target, expected)
            finally:
                restore(engine, before[0], target)
            final = engine.snapshot()
            wanted_unique = batch.counter(before[0])
            wanted_unique[key] = 1
            if (batch.counter(final[0]) != wanted_unique
                    or batch.counter(final[1]) != batch.counter(before[1]) - batch.counter((target.reward,))):
                raise ValueError('Promotion final state differs')
            expected = final
            completed += 1
            trace(f'reward={target.reward} delivered=1 other_rewards_unchanged=1')
    except Exception as error:
        if attempted:
            raise batch.Uncertain(completed, 0) from error
        raise
    return batch.Result('delivered', completed)
