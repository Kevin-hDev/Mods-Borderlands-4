"""The canonical cleanup releases input despite logging failure, only for its controller."""
from types import SimpleNamespace as NS
from unittest.mock import patch

import test_window_cleanup_recovery as fixture
from ui_test_loader import load

cleanup = load("control_window_cleanup")
sdk, events = fixture.f.sdk, fixture.f.events


def main():
    item, root, registered = fixture.setup()
    item.same_context = fixture.fail
    with patch.object(sdk.logging, "info", fixture.fail):
        item.close("error")
    assert fixture.f.window._active is None
    assert "game_input" in events and not any(registered.values())

    for same_address in (True, False):
        item, root, registered = fixture.setup()
        current = NS(_get_address=lambda: item.controller_address if same_address else -1)
        item.same_context = fixture.fail
        with patch.object(cleanup, "get_pc", lambda **kwargs: current):
            item.close("error")
        assert ("game_input" in events) is same_address
        assert not any(registered.values())
    print("RESULTAT: OK (canonical cleanup tolerates failed logging and checks controller addresses)")


if __name__ == "__main__":
    main()
