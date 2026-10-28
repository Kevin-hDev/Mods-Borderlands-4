"""The first-person arms' animation as the draw and put-away tests see it: montages played, playing and stopped, as
the SDK gives them. Shared by test_apex_draw.py and test_apex_put_away.py."""


class Arms:
    def __init__(self, error: Exception | None = None) -> None:
        self.played: list[dict] = []
        self.playing: list[object] = []
        self.stopped: list[tuple[float, object]] = []
        self.error = error

    def PlaySlotAnimationAsDynamicMontage(self, **options) -> tuple:
        if self.error is not None:
            raise self.error
        self.played.append(options)
        self.playing.append(object())
        # The SDK gives output parameters after the return value.
        return self.playing[-1], None

    def Montage_IsPlaying(self, montage: object) -> bool:
        return montage in self.playing

    def Montage_Stop(self, blend: float, montage: object) -> None:
        self.stopped.append((blend, montage))
        self.playing.remove(montage)


def pointer(thing: object):
    """The SDK's WeakPointer, for a thing that stays alive."""
    return lambda: thing
