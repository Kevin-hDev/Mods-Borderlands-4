"""Own pickup hook and live container fields, including bounded cleanup after disable."""
import time
from pathlib import Path
from .cleanup_retry import CleanupRetry
from .generated_limits import RUNTIME_FOLDER
from .loot_bridge import LootBridge
from .loot_constants import CLASS_NAME
from .loot_fields import LootFields
from .loot_memory import ProcessMemory


class LootUnit:
    def __init__(self, bridge, fields, retry, clock, log):
        self.bridge, self.fields, self.retry = bridge, fields, retry
        self.clock, self.log = clock, log
        self.native_pending = False
        self.distance = 0

    @property
    def pending(self):
        return self.native_pending or self.fields.pending

    @property
    def cleanup_pending(self):
        return self.pending

    def start(self, distance):
        if self.pending:
            raise RuntimeError('Loot cleanup required')
        self.retry.reset()
        self.native_pending = True
        self.bridge.start(distance)
        self.fields.apply(distance)
        self.distance = distance
        self.log(f'loot range enabled: distance={distance:g}')

    def refresh(self, distance):
        self.bridge.refresh(distance)
        self.fields.apply(distance)
        if distance != self.distance:
            self.distance = distance
            self.log(f'loot range changed: distance={distance:g}')

    def reset_cleanup_context(self):
        """Give a new player identity its own bounded cleanup budget."""
        self.retry.reset()

    def stop(self, stale=False, now_ns=None):
        was_pending = self.pending
        errors = []
        if self.native_pending:
            try:
                self.bridge.stop()
                self.native_pending = False
            except Exception as error:
                errors.append(error)
        if self.fields.pending:
            try:
                self.fields.restore()
            except Exception as error:
                errors.append(error)
        if errors:
            if self.pending:
                self.retry.schedule(self, self.clock() if now_ns is None else now_ns, stale)
            else:
                self.retry.cancel()
            raise RuntimeError('Loot cleanup incomplete') from errors[0]
        self.fields.saved.clear()
        self.distance = 0
        self.retry.reset()
        if was_pending:
            self.log('loot range released')


def create_unit():
    import unrealsdk
    from unrealsdk import hooks, logging
    from mods_base import MODS_DIR
    log = lambda message: logging.info(f'[Loot Range] {message}')
    # This is a class-specific refresh, never a scan of every Unreal object.
    fields = LootFields(lambda: unrealsdk.find_all(CLASS_NAME, exact=False), ProcessMemory())
    retry = CleanupRetry(hooks, 'apex_camera_runtime:loot', time.perf_counter_ns, log,
                         label='loot range')
    return LootUnit(LootBridge(Path(MODS_DIR) / RUNTIME_FOLDER), fields, retry,
                    time.perf_counter_ns, log)
