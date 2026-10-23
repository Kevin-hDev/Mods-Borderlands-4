"""Reinforcements, trial 168: the last stretch of a companion's walk, pushed to its own place beside the hunter, as Vex
Phase Clones walks its Specters (vex_phase_clones/walk.py, verified in game there: W5 to W8, M5).

Kevin, 20 October 2026, after trial 167, of the Specters' rules: « Pour le reste oui c'est ok ». The game's walk
(walk.py, AIScriptedMove) only aims at a character: every companion walked to the hunter himself, one into the
other. Vex's way: each walk aims at a place of its own on the circle where it stops, on its side of the hunter (its
bearing from him when the push begins) turned by its rank's step of the fan (catch.fan), so that companions
set off from one spot do not walk one inside the other. The push is AddMovementInput, forced, as a player's stick:
Unreal uses it for one movement update only, so it is given again at most every PUSH_S. Its parameters are the ones
Vex calls with (WorldDirection, ScaleValue, bForce). Not verified on our companions, whose brains walk them otherwise.
"""

import math
from typing import Any, Callable

import unrealsdk

# Vex's W5 to W8 pushed at most every 8 ms, and the Specter walked at its full speed.
PUSH_S = 0.008


def bearing(here: tuple, at: tuple) -> float:
    """The direction from the hunter to the companion, in degrees."""
    return math.degrees(math.atan2(at[1] - here[1], at[0] - here[0]))


def spot(here: tuple, aim: float, radius_m: float) -> tuple:
    """The place at aim degrees from the hunter, radius_m from him, at his height."""
    angle = math.radians(aim)
    return here[0] + math.cos(angle) * radius_m * 100.0, here[1] + math.sin(angle) * radius_m * 100.0, here[2]


class Push:
    """One companion's push to its place: actor is its weak pointer; note(text) says the first push of each walk
    before it is made, the others being too many for the trace."""

    def __init__(self, actor: Any, name: str, note: Callable[[str], None]) -> None:
        self.actor, self.name, self.note = actor, name, note
        self.aim: float | None = None
        self.said = False
        self.pushes = 0

    @property
    def active(self) -> bool:
        return self.aim is not None

    def begin(self, here: tuple, at: tuple, turn: float) -> None:
        self.aim, self.said = bearing(here, at) + turn, False

    def end(self) -> None:
        self.aim = None

    def step(self, here: tuple, at: tuple, radius_m: float) -> None:
        """One push toward its place, flat; none when it stands on it. A failing call raises."""
        target = spot(here, self.aim, radius_m)
        x, y = target[0] - at[0], target[1] - at[1]
        length = math.hypot(x, y)
        if length < 1.0:
            return
        if not self.said:
            self.said = True
            self.note(f"about to call AddMovementInput on {self.name}, toward its place at {round(self.aim)} degrees")
        self.pushes += 1
        self.actor().AddMovementInput(WorldDirection=unrealsdk.make_struct("Vector", X=x / length, Y=y / length,
                                                                            Z=0.0), ScaleValue=1.0, bForce=True)
