"""Checked SDK signatures and ownership of the binding window's update hook."""

from itertools import islice

import unrealsdk

PREFIX = "[GrappleUIWindow]"
HOOK = "/Script/Engine.AnimInstance:BlueprintUpdateAnimation"
IDENTIFIER = "grapple_ui_window:tick"
MAX_PARAMS = 16


def note(message):
    unrealsdk.logging.info(f"{PREFIX} {message}")


def require_signature(cls, method, expected):
    fields = tuple(islice(cls._find(method)._properties(), MAX_PARAMS + 1))
    names = tuple(str(field.Name) for field in fields)
    note(f"signature={method} params={','.join(names)}")
    if names != expected:
        raise ValueError("Unsupported interface signature")


def install_listener(callback):
    hooks, kind = unrealsdk.hooks, unrealsdk.hooks.Type.POST
    # Replace only our own listener; a failed opening may have left it inert.
    if hooks.has_hook(HOOK, kind, IDENTIFIER):
        hooks.remove_hook(HOOK, kind, IDENTIFIER)
    if hooks.has_hook(HOOK, kind, IDENTIFIER):
        raise RuntimeError("Cannot replace probe callback")
    result = hooks.add_hook(HOOK, kind, IDENTIFIER, callback)
    installed = hooks.has_hook(HOOK, kind, IDENTIFIER)
    note(f"hook_return={result} hook_present={installed}")
    return installed
