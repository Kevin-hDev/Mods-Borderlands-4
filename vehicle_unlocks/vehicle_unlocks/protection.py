"""One bounded set of requests and two owners; startup never distributes rewards."""
from . import protection_config as cfg
from .protection_catalogue import CataloguePending


def keys(value):
    if (type(value) is not tuple or len(value) > len(cfg.DLC)
            or any(type(key) is not str or key not in cfg.DLC for key in value)
            or len(set(value)) != len(value)):
        raise ValueError('Invalid promotional selection')
    return tuple(key for key in cfg.DLC if key in value)


class Controller:
    def __init__(self, load, save, factory, trace):
        self.load, self.save, self.factory, self.trace = load, save, factory, trace
        self.owners = set()
        self.selected = ()
        self.backend = None
        self.failed = False
        self.failure_code = None
        self.pending = False

    def set(self, selected):
        if self.backend is None:
            if not selected:
                return
            self.backend = self.factory()
        self.backend.set(selected)

    def start(self, owner):
        if owner not in cfg.OWNERS:
            raise ValueError('Unknown vehicle owner')
        if owner in self.owners:
            return not self.failed and not self.pending
        self.owners.add(owner)
        try:
            if self.failed:
                raise RuntimeError('Protection requires restart')
            if len(self.owners) == 1:
                self.selected = keys(self.load())
                self.set(self.selected)
            elif self.backend is not None:
                self.backend.check()
            if self.pending:
                return False
            self.trace(f'protection owner={owner} enabled=1 selected={len(self.selected)} awards=0')
            return True
        except CataloguePending as error:
            if self.backend is not None:
                self.fail(error)
                return False
            self.pending = True
            self.trace('protection waiting=catalogue awards=0')
            return False
        except Exception as error:
            self.fail(error)
            return False

    def fail(self, error):
        self.failed, self.pending = True, False
        if self.failure_code is None:
            self.failure_code = cfg.FAILURE_CODES.get(str(error), 'unknown')
        self.trace(f'protection startup_failed={type(error).__name__} code={self.failure_code} awards=0')

    def resume(self):
        if self.failed or not self.owners:
            return False
        if not self.pending:
            return True
        try:
            self.set(self.selected)
            self.pending = False
            self.trace(f'protection startup_ready selected={len(self.selected)} awards=0')
            return True
        except CataloguePending as error:
            if self.backend is not None:
                self.fail(error)
            return False
        except Exception as error:
            self.fail(error)
            return False

    def stop(self, owner):
        if owner not in cfg.OWNERS:
            raise ValueError('Unknown vehicle owner')
        if owner not in self.owners:
            return True
        try:
            if len(self.owners) == 1:
                self.set(())
            self.owners.remove(owner)
            if not self.owners:
                self.pending = False
                # Released links may resolve or move; the next activation must revalidate them.
                self.backend = None
            self.trace(f'protection owner={owner} enabled=0 remaining={len(self.owners)}')
            return True
        except Exception as error:
            self.failed = True
            self.trace(f'protection restore_failed={type(error).__name__} restart_required=1')
            return False

    def request(self, requested):
        requested = keys(requested)
        if self.failed or self.pending or not self.owners:
            raise RuntimeError('Protection unavailable')
        wanted = keys(tuple(key for key in cfg.DLC if key in self.selected or key in requested))
        previous = self.selected
        try:
            self.set(wanted)
            self.save(wanted)
        except Exception:
            try:
                self.set(previous)
            except Exception:
                self.failed = True
                raise
            raise
        self.selected = wanted
        self.trace(f'protection selected={len(wanted)} saved=1 awards=0')

    def check(self):
        if self.failed or not self.owners or self.backend is None:
            raise RuntimeError('Protection inactive')
        try:
            self.backend.check()
        except Exception:
            self.failed = True
            raise
