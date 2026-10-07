"""Omni Sprint's way to the shared memory helper: one copy for the camera mods (apex_camera_runtime/process_memory.py)."""

try:
    from .apex_camera_runtime.process_memory import read, read_float, write, write_float
except ModuleNotFoundError as error:
    # Source tests use the canonical sibling source; packaged builds carry it below the mod's only SDK root.
    if error.name != f"{__package__}.apex_camera_runtime":
        raise
    from apex_camera_runtime.process_memory import read, read_float, write, write_float

__all__ = ("read", "read_float", "write", "write_float")
