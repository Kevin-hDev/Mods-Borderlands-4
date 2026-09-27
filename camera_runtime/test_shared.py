"""Zoom's protocol reserves legacy runtime names and refuses an already-loaded old owner."""

import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from apex_camera_runtime import shared as shared_module  # noqa: E402

fails = []


def check(label, condition):
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


for name in ("_apex_camera_runtime_v1", "_apex_camera_runtime_v2", "_apex_camera_runtime_v3"):
    sys.modules.pop(name, None)

legacy = types.ModuleType("_apex_camera_runtime_v1")
legacy.protocol = 1
legacy.runtime = object()
sys.modules["_apex_camera_runtime_v1"] = legacy
try:
    shared_module.shared(lambda item: item, lambda item: 1)
except RuntimeError:
    refused = True
else:
    refused = False
check("v1 already loaded makes v2 refuse without creating an authority",
      refused and "_apex_camera_runtime_v2" not in sys.modules)
sys.modules.pop("_apex_camera_runtime_v1", None)

old = types.ModuleType("_apex_camera_runtime_v2")
old.protocol, old.runtime = 2, object()
sys.modules["_apex_camera_runtime_v2"] = old
try:
    shared_module.shared(lambda item: item, lambda item: 1)
except RuntimeError:
    refused = True
else:
    refused = False
check("a runtime without zoom is refused before registering new commands", refused)
sys.modules.pop("_apex_camera_runtime_v2", None)
runtime = shared_module.shared(lambda item: item, lambda item: 1)
state = sys.modules.get("_apex_camera_runtime_v3")
check("all names reserve the same zoom-capable runtime",
      shared_module.PROTOCOL == 3 and state is not None
      and sys.modules.get("_apex_camera_runtime_v1") is state
      and sys.modules.get("_apex_camera_runtime_v2") is state and state.runtime is runtime)
check("old clients reject the reserved state without starting a second camera",
      getattr(sys.modules["_apex_camera_runtime_v1"], "protocol", None) != 1
      and getattr(sys.modules["_apex_camera_runtime_v2"], "protocol", None) != 2)
shared_module.reset_for_tests()
check("cleanup removes both shared names",
      all(name not in sys.modules for name in
          ("_apex_camera_runtime_v1", "_apex_camera_runtime_v2", "_apex_camera_runtime_v3")))

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
raise SystemExit(1 if fails else 0)
