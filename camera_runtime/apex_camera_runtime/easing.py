"""The dynamic camera's one smoothing: three first-order stages in a row.

Kevin, fourth test of the speed FOV (2026-10-06): a single stage started brutally and settled with a small rebound.
Three in a row start with no jolt, never turn back abruptly when a key is hammered, and settle without a bump; they
reach 95 % of a change in 6.3 time constants, the seconds asked. The framing and the motion use it too: Kevin found
their trials (probes using this same easing) right.
"""

import math

STAGES = 3
SETTLE_CONSTANTS = 6.3
# A long frame (loading, a menu) must not jump a transition to its end.
MAX_STEP_S = 0.1


class Easing:
    def __init__(self, size: int, rest: float) -> None:
        """size: values eased together; rest: close enough to snap to the goal, instead of chasing a vanishing tail."""
        self.size, self.rest = size, rest
        self.reset()

    def reset(self) -> None:
        self.snap((0.0,) * self.size)

    def snap(self, values: tuple) -> None:
        self.stages = [list(values) for _ in range(STAGES)]

    @property
    def value(self) -> tuple:
        return tuple(self.stages[-1])

    def step(self, goal: tuple, seconds: float, step_s: float) -> tuple:
        step_s = min(max(step_s, 0.0), MAX_STEP_S)
        blend = 1.0 - math.exp(-step_s * SETTLE_CONSTANTS / seconds)
        source = goal
        for stage in self.stages:
            for axis in range(self.size):
                stage[axis] += (source[axis] - stage[axis]) * blend
            source = tuple(stage)
        if all(abs(stage[axis] - goal[axis]) < self.rest for stage in self.stages for axis in range(self.size)):
            self.snap(tuple(goal))
        return self.value
