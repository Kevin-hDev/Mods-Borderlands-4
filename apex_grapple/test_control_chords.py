"""Chord intent is independent of press order, repeats and the other input device."""

import sdk_stubs
sdk_stubs.install()
from apex_grapple.control_chords import Chords


def test():
    chords = Chords((("LeftControl", "ThumbMouseButton2"), ("Gamepad_RightThumbstick",)))
    assert chords.feed("LeftControl", "IE_Pressed") == (False, False)
    assert chords.feed("ThumbMouseButton2", "IE_Pressed") == (True, False)
    assert chords.feed("ThumbMouseButton2", "IE_Repeat") == (False, False)
    assert chords.feed("Gamepad_RightThumbstick", "IE_Released") == (False, False)
    assert chords.feed("LeftControl", "IE_Released") == (False, True)
    assert chords.feed("ThumbMouseButton2", "IE_Released") == (False, False)
    assert chords.feed("ThumbMouseButton2", "IE_Pressed") == (False, False)
    assert chords.feed("LeftControl", "IE_Pressed") == (True, False)
    assert chords.feed("LeftControl", "IE_Pressed") == (False, False)
    chords.clear()
    assert chords.feed("LeftControl", "IE_Pressed") == (False, False)
    for _ in range(1000):
        chords.feed("Unregistered", "IE_Pressed")
    assert len(chords.down) == 1
    print("OK | order, repeat, release ownership, reset and bounded state")


if __name__ == "__main__":
    test()
