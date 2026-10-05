"""Distinguish logical Orbit revocation from physical recovery in the elected camera."""


def cancel(runtime, owner, *, restore=True):
    if type(restore) is not bool:
        return False
    client = runtime.arbiter.active() if restore else runtime._active_client or runtime.arbiter.active()
    if client is None or client.owner != owner or runtime.third_person is None:
        return False
    if not restore:
        # Context loss revokes persistence only: no query or write against the previous world.
        runtime.third_person.foot_mode.clear_pending()
        runtime.third_person.foot_mode.rollback_failed = True
        return True
    try:
        return bool(runtime.third_person.cancel_orbit(client.settings, runtime.third_person.clock()))
    except Exception:
        client.settings.note("orbit setting: cancellation was refused")
        return False
