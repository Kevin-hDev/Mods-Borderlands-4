# Copyright (c) 2026 kevin-hDev
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Tests of pak_recipe.py: the page script in one scope, its config without game paths. python test_pak_recipe.py"""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pak_recipe as r

FAILURES = []


def expect(condition, label):
    if not condition:
        FAILURES.append(label)
        print(f"ECHEC: {label}")


C = r.load_constants()
script = r.page_script(C, r.read_sources())
expect(script.startswith("(function () {") and script.rstrip().endswith("})();"), "one function scope")
config = json.loads(script.split("const LC_CONFIG = ", 1)[1].split(";\n", 1)[0])
expect(config["http"]["port"] == C["http"]["port"] and config["marker"] == C["marker"], "config from the constants")
expect("pak" not in config and "log" not in config and "masking" not in config, "no build or service value sent")
expect(config["page"]["ownStylesheet"] == "coui://uiresources/logs_conflicts/css/logs_conflicts.css",
       "own stylesheet address")
expect(sorted(config["texts"]) == ["en", "fr", "zh"], "three languages")
for language, texts in config["texts"].items():
    expect(set(texts["errors"]) == set(config["texts"]["en"]["errors"]) and
           set(texts["states"]) == set(config["texts"]["en"]["states"]), f"{language}: every text present")
expect(all(name in r.SOURCES for name in [path.name for path in r.PAGE.glob("*.js")]), "every page source is built")
expect(config["page"]["maskReplacement"] == C["masking"]["replacement"], "the page names the mask as masking does")

# The built script must be valid JavaScript: node checks it here; test_page.js runs it and checks its one global.
with tempfile.TemporaryDirectory() as folder:
    path = Path(folder) / "logs_conflicts.js"
    path.write_text(script, encoding="utf-8")
    checked = subprocess.run(["node", "--check", str(path)], capture_output=True, timeout=60, check=False)
    expect(checked.returncode == 0, "built script parses: " + checked.stderr.decode("utf-8", "replace")[-200:])

print("RESULTAT: TOUS LES TESTS PASSENT" if not FAILURES else f"RESULTAT: {len(FAILURES)} ECHEC(S)")
sys.exit(1 if FAILURES else 0)
