"""Defer console suspension until its command returns; keep its menu stack intact."""

from . import control_console_keys as keys
from .control_reserved import MAX_CONSOLE_KEYS

COMMAND_RETURN_NS = 250_000_000
MESSAGE_DRAIN_NS = 250_000_000
MAX_MENU_DEPTH = 32


class Handoff:
    def __init__(self, native, console_key, now, redraw):
        self.native, self.console_key, self.redraw = native, console_key, redraw
        self.next_step = now + COMMAND_RETURN_NS
        self.phase = "command"
        self.restore_step = 0

    def advance(self, now):
        if self.phase == "ready":
            return True
        if now < self.next_step:
            return False
        if self.phase == "command":
            # Escape closes an empty console; its submitted command must have returned first.
            self.native.tap(keys.ESCAPE)
            self.phase = "drain"
            self.next_step = now + MESSAGE_DRAIN_NS
            return False
        self.native.check_target()
        self.phase = "ready"
        return True

    def restore(self):
        if self.restore_step == 3:
            return True
        if self.phase != "ready":
            return False
        self.native.check_target()
        if self.restore_step == 0:
            self.redraw()
            self.restore_step = 1
        # Kevin confirmed the two-press cycle: closed -> typing bar -> full menu.
        if self.restore_step == 1:
            self.native.tap(self.console_key)
            self.restore_step = 2
        if self.restore_step == 2:
            self.native.tap(self.console_key)
            self.restore_step = 3
        return True


def select_console_key(configured):
    if not 0 < len(configured) <= MAX_CONSOLE_KEYS:
        raise ValueError("Console shortcuts unavailable")
    for entry in configured:
        try:
            return keys.configured_key(str(entry.KeyName))
        except ValueError:
            # Only try configured alternatives; never invent or rewrite a console binding.
            continue
    raise ValueError("No supported console shortcut")


def create(now):
    import unrealsdk
    from console_mod_menu import screens
    if not 0 < len(screens.screen_stack) <= MAX_MENU_DEPTH:
        raise ValueError("Open this experiment from the mod menu")
    screen = screens.screen_stack[-1]

    def redraw():
        # Do not resurrect an old page if something else changed the menu meanwhile.
        if not screens.screen_stack or screens.screen_stack[-1] is not screen:
            raise RuntimeError("Menu changed while the window was open")
        screen.draw()

    configured = unrealsdk.find_class("InputSettings").ClassDefaultObject.ConsoleKeys
    key = select_console_key(configured)
    native = keys.WindowKeys()
    virtual_key, scan = native.mapping(key)
    unrealsdk.logging.info(f"[OmniUIWindow] console_key_mapping vk={virtual_key:#x} scan={scan:#x}")
    return Handoff(native, key, now, redraw)
