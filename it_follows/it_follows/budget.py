"""The game's limit of enemies, lifted when It Follows first asks for its enemies in a run and given back at the stop.

The game makes the requests to a spawner wait while its population budget is full, and the world settings' SWITCH
turns that budget off (source unique: a third-party mod's comment and code, docs/spawn-boss/sources-tierces/); without
it, the domed arena saw the game hold some of its enemies back until the first ones died. The trials up to 8b lifted it
as BL4 Arena does, for each lot, given back once the lot was born: in trial 8b it stayed lifted 170 s of 181, 94 s on
end. Lifted once a run here, the same in effect, with nothing to watch the births. Only the settings of the world in
play are switched, as BL4 Arena does; settings the game already had switched off are left alone, and not given back.
BL4 Arena switches the same setting: an arena launched during a run could give it back early.
"""

from typing import Any, Callable

import mods_base
from unrealsdk.unreal import WeakPointer

SWITCH = "bDisableSpawnBudget"


class Budget:
    """One run's lift: once given back it is not lifted again. announce(call, log, **fields) notes a call before it is
    made."""

    def __init__(self, announce: Callable[..., None]) -> None:
        self.announce = announce
        # The settings It Follows switched off, held weakly, and what the lift came to.
        self.held: Any = None
        self.said = "untouched"

    def lift(self) -> str:
        """The limit lifted on the world in play's settings, the first time; what came of it. Lifted settings the game
        no longer holds, after a change of map, are lifted again."""
        if self.said != "untouched" and (self.held is None or self.held() is not None):
            return self.said
        self.held = None
        self.announce("WorldSettings", switch=SWITCH)
        try:
            settings = mods_base.ENGINE.GameViewport.World.PersistentLevel.WorldSettings
            if settings is None:
                self.said = "no_settings"
                return self.said
            if bool(getattr(settings, SWITCH)):
                self.said = "already_off"
                return self.said
            self.announce(SWITCH, value=True, on=str(settings.Name))
            setattr(settings, SWITCH, True)
        except Exception as error:
            self.said = f"call_failed:{type(error).__name__}"
            return self.said
        self.held, self.said = WeakPointer(settings), "lifted"
        return self.said

    def restore(self) -> str:
        """The limit given back where It Follows lifted it, if those settings are still loaded; what came of it."""
        settings = self.held() if self.held is not None else None
        lifted, self.held = self.said == "lifted", None
        if settings is None:
            return "settings_gone" if lifted else "nothing_lifted"
        try:
            self.announce(SWITCH, value=False, on=str(settings.Name))
            setattr(settings, SWITCH, False)
        except Exception as error:
            self.said = f"call_failed:{type(error).__name__}"
            return self.said
        self.said = "given_back"
        return self.said
