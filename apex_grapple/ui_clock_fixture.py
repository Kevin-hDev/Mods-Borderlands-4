"""Adapt existing lifecycle failure injections to an abstract timer backend."""

from types import SimpleNamespace as NS

from ui_test_loader import load


def install(sdk):
    def stop(owner):
        sdk.hooks.remove_hook("test_timer", sdk.hooks.Type.POST, owner)
        if sdk.hooks.has_hook("test_timer", sdk.hooks.Type.POST, owner):
            raise RuntimeError("Timer still registered")

    def start(owner, callback):
        sdk.hooks.add_hook("test_timer", sdk.hooks.Type.POST, owner, callback)
        return sdk.hooks.has_hook("test_timer", sdk.hooks.Type.POST, owner)

    backend = NS(claim=lambda *args: None, release=lambda *args: None, start=start, stop=stop)
    load("control_window_clock").shared = lambda: backend
    return backend
