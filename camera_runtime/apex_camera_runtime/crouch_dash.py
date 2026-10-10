"""Crouching on the ground while the sprint is open: the game's own dash, or the slide the player chose.

Trial 9 (2026-10-09, sdk-essai-9.log): the game only dashes on the ground for a run beyond MaxSprintAngle seen from the
camera, the sprint limit itself. Opened at 180, no run is beyond it: crouching while walking only crouches, and while
sprinting slides. With the game's limit put back for LOWER_NS from the crouch key's own callback, before the game reads
the press, the dash came back walking and sprinting (ten dashes; the presses without one followed two dashes, the
game's reserve). So the crouch keys are bound, where the action keys are read each frame (body_actions.py): a frame is
too late. No press is ever blocked.

Kevin, 2026-10-09: walking, the dash whatever the choice (there is no slide while walking); sprinting, the dash or the
slide as chosen on the OMNI DIRECTION page.
"""

from typing import Any, Callable

from .body_actions import KEYS_CHECK_NS, action_keys
from .body_facing import MIN_SPEED, heading, signed_gap
from .movement_definition import GAME_LIMIT

CROUCH_ACTIONS = ("Action_Crouch_Hold", "Action_Crouch", "Action_CrouchOrDash")
WALKING = 1
# Trial 9's time, long enough for the game's dash (0.33 s) and Apex Movement's (0.53 s) to start and end.
LOWER_NS = 700_000_000


def run_gap(x: float, y: float, view: float) -> float | None:
    """The run seen from the camera, -180 to 180; None when too slow to read."""
    if (x * x + y * y) ** 0.5 < MIN_SPEED:
        return None
    return signed_gap(heading(x, y), view)


def wants_dash(mode: int, sprinting: bool, gap: float | None, dash_chosen: bool) -> bool:
    """Whether a press on the ground gets the game's limit back: beyond it, walking, or sprinting with dash chosen."""
    if mode != WALKING or gap is None or abs(gap) <= GAME_LIMIT:
        return False
    return dash_chosen or not sprinting


class CrouchDash:
    def __init__(self, bind: Callable[[str, str, Callable[[Any], None]], Any], keeper: Any,
                 get_pc: Callable[[], Any], clock: Callable[[], int], log: Callable[[str], None],
                 identifier: str) -> None:
        self.bind, self.keeper, self.get_pc, self.clock, self.log = bind, keeper, get_pc, clock, log
        self.identifier = identifier
        self.bound: dict[str, Any] = {}
        self.next_keys_ns = 0
        self.dash_chosen = True
        self.said_error = False

    def update(self, pc: Any, open_wanted: bool, dash_chosen: bool, now_ns: int) -> None:
        """Each frame: the limit open again when due, and the crouch keys bound while the sprint is asked open."""
        self.dash_chosen = dash_chosen
        self.keeper.reopen_if_due(now_ns)
        if not open_wanted:
            self.unbind()
            return
        if pc is None or now_ns < self.next_keys_ns:
            return
        self.next_keys_ns = now_ns + KEYS_CHECK_NS
        try:
            names = action_keys(pc.PlayerInput.EnhancedActionMappings, CROUCH_ACTIONS)
        except AttributeError:
            # No input list yet (a loading controller): read again a second later, the rest of the unit goes on.
            return
        if tuple(sorted(self.bound)) == names:
            return
        self.unbind()
        for name in names:
            self.bound[name] = self.bind(f"{self.identifier}:crouch:{name}", name, self.press)
        self.log("crouch keys " + (" ".join(names) if names else "none: no dash on the sides with the open sprint"))

    def press(self, event: Any) -> None:
        if getattr(event, "name", str(event)) != "IE_Pressed":
            return
        try:
            character = self.get_pc().OakCharacter
            movement = character.CharacterMovement
            velocity = movement.Velocity
            gap = run_gap(float(velocity.X), float(velocity.Y), float(character.Controller.GetControlRotation().Yaw))
            sprinting = bool(movement.bIsSprinting)
            if (wants_dash(int(movement.MovementMode), sprinting, gap, self.dash_chosen)
                    and self.keeper.lower(self.clock(), LOWER_NS)):
                self.log(f"crouch {'sprinting' if sprinting else 'walking'} at {gap:+.0f}: "
                         "game sprint limit back for the dash")
        except Exception as error:
            # The press goes to the game as it is; said once, the next ones are tried all the same.
            if not self.said_error:
                self.said_error = True
                self.log(f"crouch press not read, left to the game: {type(error).__name__}")

    def unbind(self) -> None:
        for bound in self.bound.values():
            bound.disable()
        self.bound.clear()
        self.next_keys_ns = 0

    def stop(self) -> None:
        self.unbind()
