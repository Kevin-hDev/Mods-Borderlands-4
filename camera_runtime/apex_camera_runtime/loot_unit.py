"""Own pickup hook and live container fields, including bounded cleanup after disable."""
import time
from pathlib import Path
from .cleanup_retry import CleanupRetry
from .frame_hooks import front
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

    def start(self, distance, world):
        if self.pending:
            raise RuntimeError('Loot cleanup required')
        self.retry.reset()
        self.native_pending = True
        self.bridge.start(distance)
        self.fields.apply(distance, world)
        self.distance = distance
        self.log(f'loot range enabled: distance={distance:g}')

    def refresh(self, distance, world):
        self.bridge.refresh(distance)
        self.fields.apply(distance, world)
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


def containers(sdk, world):
    """The containers of the world in play. In game, 0.2 to 0.4 ms where find_all, which goes through every object
    the game holds, took 8 to 12 ms; both gave the same containers within 50 m of the player, find_all adding only
    those of cells being unloaded, 158 m and more away (docs/performance/enquetes/2026-10-24-butin-deux-listes.md)."""
    statics = sdk.find_class('GameplayStatics').ClassDefaultObject
    _void, found = statics.GetAllActorsOfClass(WorldContextObject=world, ActorClass=sdk.find_class(CLASS_NAME),
                                               OutActors=[])
    return found


def create_unit():
    import unrealsdk
    from unrealsdk import hooks, logging
    from unrealsdk.unreal import WeakPointer
    from mods_base import MODS_DIR
    log = lambda message: logging.info(f'[Loot Range] {message}')
    fields = LootFields(lambda world: containers(unrealsdk, world), ProcessMemory(), WeakPointer)
    retry = CleanupRetry(front(hooks), 'apex_camera_runtime:loot', time.perf_counter_ns, log,
                         label='loot range')
    return LootUnit(LootBridge(Path(MODS_DIR) / RUNTIME_FOLDER), fields, retry,
                    time.perf_counter_ns, log)
