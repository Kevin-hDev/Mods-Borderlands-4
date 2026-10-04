"""One shared operation owner for both mods, gated on a local character at foot."""
from . import batch, config as cfg

locked = False
busy = False


class Refused(ValueError):
    def __init__(self, reason):
        self.reason = reason
        super().__init__(reason)


def context(mod):
    from mods_base import get_pc
    import unrealsdk
    if not mod.is_enabled:
        raise Refused('disabled')
    pc = get_pc()
    if pc is None or pc.Pawn is None:
        raise Refused('no_game')
    character = getattr(pc, 'OakCharacter', None)
    if character is None or pc.Pawn != character:
        raise Refused('vehicle')
    library = unrealsdk.find_class(cfg.HOST_LIBRARY)
    if library is None:
        raise Refused('unreadable')
    own = library.ClassDefaultObject.IsServer(pc)
    if type(own) is not bool:
        raise Refused('unreadable')
    if not own:
        raise Refused('guest')
    manager = getattr(pc, 'RewardsManager', None)
    if manager is None:
        raise Refused('unreadable')
    return pc, character, manager


def engine_for(target):
    from .engine import Engine
    pc, _, manager = target
    return Engine(pc, manager)


def trace(message):
    from unrealsdk import logging
    logging.info(f'{cfg.PREFIX} {message}')


def available(mod):
    if locked:
        return 'restart'
    if busy:
        return 'busy'
    try:
        engine_for(context(mod))
        return None
    except Refused as error:
        return error.reason
    except Exception:
        return 'unreadable'


def run(action, mod):
    global locked, busy
    reason = ('unreadable' if type(action) is not str or action not in cfg.ACTIONS else 'disabled' if not mod.is_enabled
              else 'restart' if locked else 'busy' if busy else None)
    if reason is not None:
        return batch.Result('refused', reason=reason)
    busy = True
    try:
        target = context(mod)
        engine = engine_for(target)
        from . import protection_runtime, promotion_award
        promotional = action == 'promotions'
        if promotional:
            protection_runtime.request()
        def guard():
            if context(mod) != target:
                raise Refused('unreadable')
            if promotional:
                protection_runtime.check()
        operation = promotion_award.apply if promotional else batch.apply
        result = operation(engine, cfg.ACTIONS[action], guard, trace)
    except batch.Uncertain as error:
        locked = True
        result = batch.Result('uncertain', error.changed, error.skipped, 'restart')
    except Refused as error:
        result = batch.Result('refused', reason=error.reason)
    except Exception as error:
        trace(f'action={action} failure_type={type(error).__name__}')
        result = batch.Result('refused', reason='unreadable')
    finally:
        busy = False
    trace(f'action={action} result={result.kind} changed={result.changed} skipped={result.skipped} '
          f'reason={result.reason or "none"}')
    return result
