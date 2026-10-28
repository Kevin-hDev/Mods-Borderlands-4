"""Vehicle SDK mod lifecycle and settings file fixture."""
import tempfile
from pathlib import Path
from typing import Any


class FakeMod:
    """As mods_base.Mod where this mod depends on it: hooks on before on_enable, off before on_disable."""

    def __init__(self, state: dict, **kwargs: Any) -> None:
        self.state, self.kwargs, self.is_enabled = state, kwargs, False
        self._settings_directory = tempfile.TemporaryDirectory()
        self.settings_file = Path(self._settings_directory.name) / "settings.json"
        if state["settings_exists"]:
            self.settings_file.write_text("{}")

    def enable(self) -> None:
        if self.is_enabled:
            return
        self.is_enabled = True
        for hook in self.kwargs.get("hooks") or []:
            hook.enable()
        if self.kwargs.get("on_enable"):
            self.kwargs["on_enable"]()

    def disable(self) -> None:
        if not self.is_enabled:
            return
        self.is_enabled = False
        for hook in self.kwargs.get("hooks") or []:
            hook.disable()
        if self.kwargs.get("on_disable"):
            self.kwargs["on_disable"]()

    def save_settings(self) -> None:
        self.state["saves"] = self.state.get("saves", 0) + 1

    def iter_display_options(self):
        yield from self.kwargs.get("options", ())
