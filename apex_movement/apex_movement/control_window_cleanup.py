"""The closing session owns bounded retries until each of its resources is released."""

import unrealsdk

from .control_window_hooks import note, remove_listener

COMMAND = "movement_ui_close"
RETRY_NS = 250_000_000
MAX_ATTEMPTS = 4
STEPS = ("root", "input", "cursor", "shape", "command", "menu")


class Cleanup:
    def __init__(self, session, reason):
        self.session, self.reason = session, reason
        self.done, self.reported = set(), set()  # Bounded by STEPS plus the hook.
        self.attempts = self.next_try = 0

    def run(self, name, operation):
        try:
            return operation() is not False
        except Exception as error:
            if name not in self.reported:
                self.reported.add(name)
                note(f"cleanup_error={type(error).__name__} step={name}")
            return False

    def advance(self, now, explicit=False):
        if explicit:
            self.attempts = 0
        elif self.attempts >= MAX_ATTEMPTS or now < self.next_try:
            return False
        self.attempts += 1
        self.next_try = now + RETRY_NS
        for name in STEPS:
            operation = (lambda: self.menu(now)) if name == "menu" else getattr(self, name)
            if name not in self.done and self.run(name, operation):
                self.done.add(name)
        released = len(self.done) == len(STEPS)
        # Keep the existing callback only while it still has bounded recovery work.
        if released or self.attempts >= MAX_ATTEMPTS:
            self.run("hook", self.hook)
        complete = released and not self.session.hooked
        if complete or self.attempts == MAX_ATTEMPTS or self.attempts == 1:
            note(f"closed={self.reason} cleanup_ok={complete} attempt={self.attempts}")
        return complete

    def context(self):
        session = self.session
        if not session.input_changed:
            return None
        pc = session.pc()
        return pc if session.same_context(pc) else None

    def root(self):
        root = self.session.root()
        if root is not None:
            root.RemoveFromParent()

    def input(self):
        pc = self.context()
        if pc is None:
            return
        library = self.session.library()
        if library is None:
            raise RuntimeError("Input library unavailable")
        if self.session.frontend:
            library.SetInputMode_GameAndUIEx(
                pc, None, unrealsdk.find_enum("EMouseLockMode").DoNotLock, False, True)
        else:
            library.SetInputMode_GameOnly(pc, True)

    def cursor(self):
        pc = self.context()
        if pc is not None:
            pc.bShowMouseCursor = self.session.cursor

    def shape(self):
        pc = self.context()
        if pc is not None:
            pc.CurrentMouseCursor = self.session.cursor_shape

    def command(self):
        if self.session.commanded:
            unrealsdk.commands.remove_command(COMMAND)
            if unrealsdk.commands.has_command(COMMAND):
                raise RuntimeError("Close command still registered")
            self.session.commanded = False

    def menu(self, now):
        if not {"root", "input", "cursor", "shape"}.issubset(self.done):
            return False
        if self.reason == "button" and self.session.handoff is not None and self.context() is not None:
            if not self.session.handoff.advance(now):
                return False
            return self.session.handoff.restore()

    def hook(self):
        if self.session.hooked:
            remove_listener()
            self.session.hooked = False
