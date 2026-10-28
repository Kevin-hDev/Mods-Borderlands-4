"""One retryable anchor owned by the elected camera during native climbing."""
from .climb_anchor_bridge import ClimbAnchorBridge, NativeRefusal


class ClimbAnchorSession:
    def __init__(self, library, weak_ref, log):
        self.bridge = ClimbAnchorBridge(library, weak_ref)
        self.log = log
        self.pending = False
        self._blocked = None

    def sync(self, controller, manager, climbing):
        if not climbing:
            self.stop()
            # A failed traversal stays disarmed, but cannot poison later traversals for the whole session.
            self._blocked = None
            return
        owner = controller._lifetime.ids
        if self._blocked == owner:
            return
        try:
            if not self.pending:
                # Own a partial native installation too; cleanup must remain retryable.
                self.pending = True
                self.bridge.start(manager)
                self.log('native climb animated anchor started')
            self.bridge.refresh()
        except Exception as error:
            self._blocked = owner
            detail = f' stage={error.stage} code={error.code}' if isinstance(error, NativeRefusal) else ''
            self.log(f'native climb animated anchor unavailable: {type(error).__name__}{detail}')
            self.stop()

    def stop(self):
        if not self.pending:
            return
        self.bridge.stop()
        self.pending = False
        try:
            value = self.bridge.stats()
            self.log(f'native climb animated anchor stopped applied={value.applied} refused={value.refused}')
        except Exception as error:
            self.log(f'native climb animated anchor statistics unavailable: {type(error).__name__}')
