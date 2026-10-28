"""Loaded by the elected shared runtime; native access is lazy and fails closed."""
from . import protection_config as cfg, protection_store, service
from .protection import Controller
from .protection_startup import Waiter
from time import perf_counter_ns


def factory():
    import unrealsdk
    from .protection_memory import Memory
    from .protection_catalogue import Catalogue, validate_layout
    from .protection_links import Links
    from .protection_write import Writer
    trace = (lambda _: None) if controller.pending else service.trace
    trace('protection prepare stage=memory')
    memory = Memory()
    trace('protection prepare stage=layout')
    validate_layout(unrealsdk.find_object('ScriptStruct', cfg.DLC_STRUCT))
    trace('protection prepare stage=reward_type')
    reward = unrealsdk.find_object('ScriptStruct', service.cfg.REWARD_STRUCT)
    if reward is None:
        raise ValueError('Reward type unavailable')
    trace('protection prepare stage=native_contract')
    catalogue = Catalogue(memory, reward._get_address(), service.trace)
    trace('protection prepare stage=catalogue')
    _, targets = catalogue.capture()
    trace('protection prepare stage=originals')
    catalogue.validate_originals(targets)
    trace('protection prepare stage=writers')
    writers = {address: Writer(memory, address) for address, _ in targets.values()}
    def write(address, expected, value):
        writers[address](address, expected, value)
    result = Links(catalogue.capture, write)
    # Recheck original reward identities after the second capture, before any write.
    catalogue.validate_originals(result.original)
    service.trace('protection prepare stage=ready writes=0')
    return result


controller = Controller(protection_store.load, protection_store.save, factory, service.trace)


def install(callback):
    from unrealsdk import hooks
    if hooks.add_hook(cfg.STARTUP_HOOK, hooks.Type.PRE, cfg.STARTUP_HOOK_ID, callback) is False:
        raise RuntimeError('Startup hook unavailable')


def remove():
    from unrealsdk import hooks
    if hooks.remove_hook(cfg.STARTUP_HOOK, hooks.Type.PRE, cfg.STARTUP_HOOK_ID) is False:
        raise RuntimeError('Startup hook unavailable')


# Elected with the runtime, so independently bundled mods share one startup hook.
waiter = Waiter(controller, perf_counter_ns, install, remove)


def start(owner):
    result = controller.start(owner)
    waiter.sync()
    return result and not controller.failed


def stop(owner):
    result = controller.stop(owner)
    waiter.sync()
    return result


def request():
    controller.request(tuple(cfg.DLC))


def check():
    controller.check()
