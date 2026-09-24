"""The shared runtime receives one native third-person controller."""

import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from apex_camera_runtime.bootstrap import attach  # noqa: E402


class Runtime:
    third_person = None

    def set_third_person(self, controller):
        self.third_person = controller


class Function:
    def __call__(self, *_args):
        return 0


library = types.SimpleNamespace(view_start=Function(), view_stop=Function(),
                                view_set_suspended=Function(), view_stats=Function())
hooks = types.SimpleNamespace(Type=types.SimpleNamespace(PRE="PRE"))
kismet = object()
sdk = types.SimpleNamespace(make_struct=lambda *_args, **kwargs: types.SimpleNamespace(**kwargs))
runtime = Runtime()
first = attach(runtime, library, hooks, sdk, lambda item: lambda: item, kismet, lambda _line: None)
second = attach(runtime, library, hooks, sdk, lambda item: lambda: item, kismet, lambda _line: None)
ok = first is second is runtime.third_person
print("RESULTAT:", "TOUS LES TESTS PASSENT" if ok else "1 ECHEC(S)")
sys.exit(0 if ok else 1)
