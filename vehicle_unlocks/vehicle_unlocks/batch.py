"""Bounded explicit batches, validating every native transition before continuing."""
from collections import Counter
from dataclasses import dataclass

from . import config as cfg


@dataclass(frozen=True)
class Result:
    kind: str
    changed: int = 0
    skipped: int = 0
    reason: str | None = None


class Uncertain(RuntimeError):
    def __init__(self, changed, skipped):
        self.changed, self.skipped = changed, skipped
        super().__init__('Reward outcome uncertain')


def counter(names):
    return Counter(label.casefold() for label in names)


def checked_give(engine, target, before):
    engine.give(target)
    after = engine.snapshot()
    old_u, old_p = map(counter, before)
    new_u, new_p = map(counter, after)
    one = Counter((target.reward.casefold(),))
    if (new_u not in (old_u, old_u + one) or new_p not in (old_p, old_p + one)
            or (new_u == old_u and new_p == old_p)):
        raise ValueError('Reward attribution not verified')
    return after


def checked_open(engine, target, before):
    engine.open(target)
    after = engine.snapshot()
    old_u, old_p = map(counter, before)
    new_u, new_p = map(counter, after)
    one = Counter((target.reward.casefold(),))
    if new_p != old_p - one or new_u not in (old_u, old_u + one) or not new_u[target.reward.casefold()]:
        raise ValueError('Reward package opening not verified')
    return after


def apply(engine, targets, guard, trace):
    if not 1 <= len(targets) <= cfg.MAX_TARGETS or len({t.reward for t in targets}) != len(targets):
        raise ValueError('Invalid reward batch')
    guard()
    expected = engine.snapshot()
    pending = counter(expected[1])
    for target in targets:
        if pending[target.reward.casefold()] > 1:
            raise ValueError('Ambiguous pending reward')
        if pending[target.reward.casefold()]:
            engine.validate(target)
    changed, skipped, attempted = 0, 0, False
    try:
        for target in targets:
            guard()
            if engine.snapshot() != expected:
                raise ValueError('Reward state changed')
            unique, pending = map(counter, expected)
            key = target.reward.casefold()
            if unique[key] and not pending[key]:
                skipped += 1
                trace(f'reward={target.reward} already_received=1')
                continue
            if not pending[key]:
                trace(f'reward={target.reward} stage=give')
                attempted = True  # Never retry after a call whose outcome could be ambiguous.
                expected = checked_give(engine, target, expected)
            if counter(expected[1])[key]:
                engine.validate(target)
                guard()
                if engine.snapshot() != expected:
                    raise ValueError('Reward state changed before opening')
                trace(f'reward={target.reward} stage=open_package')
                attempted = True
                expected = checked_open(engine, target, expected)
            changed += 1
            trace(f'reward={target.reward} recorded=1 other_rewards_unchanged=1')
    except Exception as error:
        if attempted:
            raise Uncertain(changed, skipped) from error
        raise
    return Result('changed' if changed else 'unchanged', changed, skipped)
