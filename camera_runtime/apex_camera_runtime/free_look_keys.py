"""Free Look's key, one per device, free of the game for its tests.

Kevin, 2026-10-06: a key in COMMANDS with two ways, hold or press. Held, Free Look starts once the key has been
down for the hold time (0.20 s by default, adjustable), so a short press stays the game's (L3 sprints); it lasts
while the key stays down. Pressed, each press turns it on or off at once. Aiming ends it (Kevin, 2026-10-07); it
then waits for every key to be up, or a key still held would start it again at once.
"""


class Device:
    def __init__(self) -> None:
        self.down_s = 0.0
        self.was_down = False
        self.on = False

    def step(self, down: bool, hold: bool, hold_s: float, step_s: float) -> bool:
        pressed = down and not self.was_down
        self.was_down = down
        if hold:
            self.down_s = self.down_s + step_s if down else 0.0
            self.on = down and self.down_s >= hold_s
        elif pressed:
            self.on = not self.on
        return self.on

    def clear(self) -> None:
        self.down_s, self.on = 0.0, False


class Trigger:
    """Whether Free Look is wanted this frame, from the keyboard and the controller."""

    def __init__(self) -> None:
        self.devices = (Device(), Device())
        self.waiting = False

    def step(self, downs: tuple, holds: tuple, hold_s: float, step_s: float) -> bool:
        wanted = [device.step(down, hold, hold_s, step_s) for device, down, hold in zip(self.devices, downs, holds)]
        if self.waiting:
            if any(downs):
                self.clear_devices()
                return False
            self.waiting = False
        return any(wanted)

    def cancel(self) -> None:
        self.clear_devices()
        self.waiting = True

    def clear_devices(self) -> None:
        for device in self.devices:
            device.clear()
