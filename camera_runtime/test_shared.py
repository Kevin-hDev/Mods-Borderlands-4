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


for name in ("_apex_camera_runtime_v1", "_apex_camera_runtime_v2", "_apex_camera_runtime_v3", "_apex_camera_runtime_v4"):
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
except RuntimeError as error:
    refused, notice = True, getattr(error, "notice", None)
else:
    refused, notice = False, None
check("a runtime without zoom is refused before registering new commands", refused)
check("the refusal names the line a settings window shows for it", notice == "camera_outdated")
sys.modules.pop("_apex_camera_runtime_v2", None)
old = types.ModuleType("_apex_camera_runtime_v3")
old.protocol, old.runtime = 3, object()
sys.modules["_apex_camera_runtime_v3"] = old
try:
    shared_module.shared(lambda item: item, lambda item: 1)
except RuntimeError:
    refused = True
else:
    refused = False
check("v3 cannot share the ADS native contract", refused)
sys.modules.pop("_apex_camera_runtime_v3", None)
old = types.ModuleType("_apex_camera_runtime_v4")
old.protocol, old.runtime = 4, object()
sys.modules["_apex_camera_runtime_v4"] = old
try:
    shared_module.shared(lambda item: item, lambda item: 1)
except RuntimeError:
    refused = True
else:
    refused = False
check("v4 cannot share the framing contract", refused and "_apex_camera_runtime_v5" not in sys.modules)
sys.modules.pop("_apex_camera_runtime_v4", None)
old = types.ModuleType("_apex_camera_runtime_v5")
old.protocol, old.runtime = 5, object()
sys.modules["_apex_camera_runtime_v5"] = old
try:
    shared_module.shared(lambda item: item, lambda item: 1)
except RuntimeError:
    refused = True
else:
    refused = False
check("v5 cannot share the per-frame collision callback", refused)
sys.modules.pop("_apex_camera_runtime_v5", None)
old = types.ModuleType("_apex_camera_runtime_v6")
old.protocol, old.runtime = 6, object()
sys.modules["_apex_camera_runtime_v6"] = old
try:
    shared_module.shared(lambda item: item, lambda item: 1)
except RuntimeError:
    refused = True
else:
    refused = False
check("v6 cannot share the build-qualified native libraries", refused)
sys.modules.pop("_apex_camera_runtime_v6", None)
runtime = shared_module.shared(lambda item: item, lambda item: 1)
state = sys.modules.get("_apex_camera_runtime_v7")
check("all names reserve the same zoom-capable runtime",
      shared_module.PROTOCOL == 7 and state is not None
      and sys.modules.get("_apex_camera_runtime_v1") is state
      and sys.modules.get("_apex_camera_runtime_v2") is state
      and sys.modules.get("_apex_camera_runtime_v3") is state
      and sys.modules.get("_apex_camera_runtime_v4") is state
      and sys.modules.get("_apex_camera_runtime_v5") is state
      and sys.modules.get("_apex_camera_runtime_v6") is state and state.runtime is runtime)
from apex_camera_runtime import ads_category, ads_paths_reader, generated_ads
check("probes consume the elected package's canonical ADS readers",
      state is not None and getattr(state, "ads_category_reader", None) is ads_category.category
      and getattr(state, "ads_object_address", None) is ads_category.address
      and getattr(state, "ads_paths_reader", None) ==
      (generated_ads.PathsConfig, generated_ads.PathsSample,
       ads_paths_reader.make_config, ads_paths_reader.object_parts))
check("old clients reject the reserved state without starting a second camera",
      getattr(sys.modules["_apex_camera_runtime_v1"], "protocol", None) != 1
      and all(getattr(sys.modules[f"_apex_camera_runtime_v{version}"], "protocol", None) != version
              for version in (2, 3, 4, 5, 6)))
shared_module.reset_for_tests()
check("cleanup removes both shared names",
      all(name not in sys.modules for name in shared_module.ALL_STATES))

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
raise SystemExit(1 if fails else 0)
