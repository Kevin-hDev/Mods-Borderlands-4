"""Each part of Apex Heirloom runs while the mod is on and its own switch is on: the heirloom, and the holster.

Why, Kevin, 2026-09-26 (docs/mokup/menu_mods/decisions.md): « un interrupteur par partie ». A player may want the
heirloom with another mod's key to put the weapon away, or our key without the heirloom; the mod's own switch still
turns both off. A part is started and stopped here, only when the mod or its switch changes it: started twice, the
heirloom would give our list to the hands twice.

A separate file runs its own part only (pack.py): the other part is left out of PARTS, so nothing ever starts it.
"""

from typing import Any, Callable

from . import heirloom_settings, holster_settings, inspect_keys, keys, lifecycle, pack, report, restriction


class Part:
    def __init__(self, switch: Any, start: Callable[[], None], stop: Callable[[], None]) -> None:
        self.switch, self._start, self._stop, self.running = switch, start, stop, False

    def follow(self, mod_on: bool, value: Any = None) -> None:
        """Runs the part or stops it as the mod and the switch want: `value` is the switch's value about to be set,
        mods_base calling before it changes. Only an explicit Off stops it: a malformed saved value keeps the part."""
        wanted = mod_on and (self.switch.value if value is None else value) is not False
        if wanted == self.running:
            return
        self.running = wanted
        (self._start if wanted else self._stop)()


def _heirloom_on() -> None:
    inspect_keys.start()
    lifecycle.turn_on()


def _holster_on() -> None:
    report.reset()
    keys.start()
    restriction.forget()


def _holster_off() -> None:
    keys.stop()
    restriction.forget()
    report.note("off")


HEIRLOOM = Part(heirloom_settings.heirloom, _heirloom_on, lifecycle.turn_off)
HOLSTER = Part(holster_settings.holster, _holster_on, _holster_off)
PARTS = tuple(part for part in (HEIRLOOM, HOLSTER) if pack.runs(part.switch.identifier))
for _part in PARTS:
    _part.switch.on_change_while_enabled = lambda _option, value, part=_part: part.follow(True, value)


def mod_on() -> None:
    for part in PARTS:
        part.follow(True)


def mod_off() -> None:
    for part in PARTS:
        part.follow(False)
