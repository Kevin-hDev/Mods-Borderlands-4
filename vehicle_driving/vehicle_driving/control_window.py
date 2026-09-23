"""Binding window lifecycle, using the mod's saved options and native selector."""

from itertools import islice
import time

from mods_base import get_pc
import unrealsdk

from . import control_console_handoff, control_window_clock
from .control_window_hooks import install_listener, note, require_signature
from .control_window_cleanup import COMMAND, Cleanup

POLL_NS = 50_000_000
MAX_INSTANCES = 32
MAX_CURSOR_LOGS = 3
_active = None


def active():
    return _active is not None and not _active.closed


def cancel():
    if _active is not None:
        _active.close("cancelled")


def cancel_for_gameplay():
    if active() and getattr(_active.form, "keep_when_disabled", False):
        try:
            if _active.same_context(_active.pc()):
                return  # The settings window survives disabling gameplay, not world changes.
        except Exception as error:
            note(f"context_error={type(error).__name__}")
    cancel()


class Session:
    def __init__(self, pc, root, library, cursor, form, bindings, character):
        self.pc, self.root, self.library = pc, root, library
        self.form, self.bindings, self.character = form, bindings, character
        pawn = getattr(pc(), "Pawn", None)
        self.pawn = unrealsdk.unreal.WeakPointer(pawn) if pawn is not None else lambda: None
        self.frontend = character() is None and self.pawn() is None
        self.selector = form.focus
        self.cursor_shape = pc().CurrentMouseCursor
        self.cursor_recoveries = 0
        self.cursor = cursor
        self.next_poll = 0
        self.closed = self.selecting = False
        self.hooked = self.commanded = self.input_changed = False
        self.handoff = None
        self.cleanup = None
        self.claimed = False

    def same_context(self, pc):
        character = self.character()
        return (pc is not None and pc == get_pc(possibly_loading=True)
                and ((self.frontend and getattr(pc, "OakCharacter", None) is None
                      and getattr(pc, "Pawn", None) is None)
                     or (character is not None and getattr(pc, "OakCharacter", None) == character)
                     or (character is None and self.pawn() is not None
                         and getattr(pc, "Pawn", None) == self.pawn())))

    def close(self, reason):
        self.closed = True
        if self.cleanup is None:
            self.cleanup = Cleanup(self, reason)
        elif _active is not self:
            return  # A completed old callback must never release a newer window's resources.
        if reason in ("cancelled", "retry", "command"):
            self.cleanup.reason = reason  # A new console request supersedes the old return page.
        self.recover(time.perf_counter_ns(), explicit=True)

    def recover(self, now, explicit=False):
        global _active
        if self.cleanup is not None and self.cleanup.advance(now, explicit) and _active is self:
            if self.claimed:
                control_window_clock.shared().release(__package__)
                self.claimed = False
            _active = None

    def poll(self, now):
        if self.closed:
            self.recover(now)
            return
        if now < self.next_poll:
            return
        self.next_poll = now + POLL_NS
        root, selector = self.root(), self.selector()
        if root is None or selector is None:
            note(f"widget_valid root={root is not None} selector={selector is not None}")
            self.close("window_gone")
            return
        pc = self.pc()
        if not self.same_context(pc):
            self.close("session_changed")
            return
        if not self.bindings.ready():
            self.close("mod_disabled")
            return
        if self.handoff is not None and not self.input_changed:
            if not self.handoff.advance(now):
                return
            self.focus()
            note("console_handoff_dispatched=true")
        if self.form.poll():
            self.close("button")
            return
        selecting = self.form.selecting()
        if selecting and not self.selecting:
            note("selecting=true")
        self.selecting = selecting
        if not self.closed and not selecting and self.input_changed and not self.pc().bShowMouseCursor:
            # A hidden cursor is not proof of lost input ownership (live click trace).
            # Only restore visibility while idle; never refocus, flush or cancel capture.
            self.pc().bShowMouseCursor = True
            self.pc().CurrentMouseCursor = unrealsdk.find_enum("EMouseCursor").Default
            if self.cursor_recoveries < MAX_CURSOR_LOGS:
                self.cursor_recoveries += 1
                note(f"cursor_visible_restored={self.cursor_recoveries}")

    def focus(self):
        pc, selector, library = self.pc(), self.selector(), self.library()
        self.input_changed = True
        pc.bShowMouseCursor = True
        pc.CurrentMouseCursor = unrealsdk.find_enum("EMouseCursor").Default
        library.SetInputMode_UIOnlyEx(pc, selector, unrealsdk.find_enum("EMouseLockMode").DoNotLock, True)
        selector.SetKeyboardFocus()

    def tick(self, _obj, _args, _ret, _func):
        try:
            self.poll(time.perf_counter_ns())
        except Exception as error:
            note(f"poll_error={type(error).__name__}")
            self.close("error")


def start(return_to_menu=False):
    global _active
    session = None
    stage = "preflight"
    claimed = False
    try:
        if _active is not None and _active.closed:
            _active.close("retry")
            if _active is not None:
                note("cleanup_pending=true")
                return
        if active() or unrealsdk.commands.has_command(COMMAND):
            note("already_open=true use_vehicle_ui_close=true")
            return
        pc = get_pc(possibly_loading=True)
        if pc is None or (pc.bShowMouseCursor and not return_to_menu):
            note("not_ready=true")
            return
        handoff = None
        if return_to_menu:
            handoff = control_console_handoff.create(time.perf_counter_ns())
        from . import panel_factory
        bindings = panel_factory.PanelBindings()
        if not bindings.prepare():
            note("mod_not_ready=true")
            return
        viewport_class = unrealsdk.find_class("GameViewportSubsystem")
        # BL4's reflected parameter is lowercase 'slot' (measured in the live SDK).
        require_signature(viewport_class, "AddWidget", ("Widget", "slot", "ReturnValue"))
        viewport = next((x for x in islice(unrealsdk.find_all(viewport_class), MAX_INSTANCES)
                         if not str(x.Name).startswith("Default__")), None)
        if viewport is None:
            raise ValueError("Viewport unavailable")
        library = unrealsdk.find_class("WidgetBlueprintLibrary").ClassDefaultObject
        # Preflight both acquisition and release before changing input ownership.
        require_signature(library.Class, "SetInputMode_UIOnlyEx",
                          ("PlayerController", "InWidgetToFocus", "InMouseLockMode", "bFlushInput"))
        require_signature(library.Class, "SetInputMode_GameOnly", ("PlayerController", "bFlushInput"))
        if getattr(pc, "OakCharacter", None) is None and getattr(pc, "Pawn", None) is None:
            require_signature(library.Class, "SetInputMode_GameAndUIEx",
                              ("PlayerController", "InWidgetToFocus", "InMouseLockMode", "bHideCursorDuringCapture", "bFlushInput"))
        stage = "window_ownership"
        control_window_clock.shared().claim(__package__, cancel)
        claimed = True
        stage = "construct_selector"
        weak = unrealsdk.unreal.WeakPointer
        root, form = panel_factory.build(pc, bindings, return_to_menu)
        character = getattr(pc, "OakCharacter", None)
        character_ref = weak(character) if character is not None else lambda: None
        session = Session(weak(pc), weak(root), weak(library), pc.bShowMouseCursor, form, bindings, character_ref)
        session.handoff = handoff
        session.claimed = True
        _active = session
        stage = "layout"
        slot = panel_factory.panel_view.viewport_slot()
        stage = "add_to_viewport"
        if not viewport.AddWidget(root, slot):
            raise RuntimeError("Viewport rejected widget")
        stage = "cleanup_registration"
        session.hooked = install_listener(session.tick)
        if not session.hooked:
            raise RuntimeError("Cannot schedule cleanup")
        session.commanded = unrealsdk.commands.add_command(COMMAND, lambda *_: session.close("command"))
        if not session.commanded:
            raise RuntimeError("Cannot register close command")
        stage = "focus"
        if handoff is None:
            session.focus()
        note("opened=true persistent_bindings=true close=button")
    except Exception as error:
        note(f"open_error={type(error).__name__} stage={stage}")
        if session is not None:
            session.close("open_failed")
        elif claimed:
            control_window_clock.shared().release(__package__)
