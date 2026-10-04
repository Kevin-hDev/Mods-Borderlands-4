"""One persistent aiming choice per owner; the SDK owns its settings file."""

from mods_base import BoolOption

from .option_texts import AIM_VIEW


class AdsOptions:
    def __init__(self) -> None:
        self.option = BoolOption("third_person_ads", True, **AIM_VIEW)

    def enabled(self) -> bool:
        return self.option.value is True

    def save(self, value: bool) -> None:
        if type(value) is not bool:
            raise ValueError("invalid aim view setting")
        previous = self.option.value
        self.option.value = value
        try:
            self.option.mod.save_settings()
        except Exception:
            self.option.value = previous
            raise
