"""When a key asks for the weapon to be put away: at its press, or once it has been held long enough.

Why both, Kevin, 2026-09-25: "il faudra aussi pouvoir bind une touche avec un simple clic, ça doit pas forcément être
une touche maintenue, il faudra les deux". Held by default: the controller's Square also reloads, and the game reloads
only on a short tap (Action_Reload, InputTriggerTap, releves/apex_inputs_2026-09-16.log), so a hold leaves the reload
alone.
"""

PRESS, HOLD = "Press", "Hold"
# A mouse button pressed twice quickly comes as a double click, not a second press (audit of Apex Movement's walk key,
# 2026-09-25): both start a press.
PRESSES = ("IE_Pressed", "IE_DoubleClick")
# The hold is counted at each frame of the arms. A first frame this long after the hold time means none ran meanwhile
# (a menu, a loading screen), and the release may have gone unseen: putting the weapon away then would surprise.
LATE_S = 0.5


class KeyWatch:
    """One key's presses, told in the SDK's event names."""

    def __init__(self) -> None:
        self._down_at: float | None = None
        self._asked = False

    def event(self, name: str, now: float, mode: str) -> bool:
        """True when this event asks for the weapon to be put away now."""
        if name in PRESSES:
            # Always a fresh start: a release missed earlier must not leave the key stuck down.
            self._down_at, self._asked = now, mode == PRESS
            return mode == PRESS
        if name == "IE_Released":
            self.forget()
        return False

    def tick(self, now: float, mode: str, hold_s: float) -> bool:
        """True when the key, held, has just reached the hold time."""
        if not self.pending() or mode != HOLD:
            return False
        held = now - self._down_at
        if held > hold_s + LATE_S:
            self.forget()
            return False
        if held < hold_s:
            return False
        self._asked = True
        return True

    def pending(self) -> bool:
        return self._down_at is not None and not self._asked

    def forget(self) -> None:
        self._down_at, self._asked = None, False
