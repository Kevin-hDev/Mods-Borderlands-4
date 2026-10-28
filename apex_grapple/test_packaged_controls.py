"""The distributable archive carries the complete UI and imports without source-side probes."""

from pathlib import Path
import subprocess
import sys
import tempfile
import zipfile

HERE = Path(__file__).resolve().parent
package = HERE / "apex_grapple"
# Public checkout: exercise the documented zip layout without a private deployment tool.
files = sorted(package.glob("*.py")) + sorted(path for path in (package / "assets").iterdir() if path.is_file())
with tempfile.TemporaryDirectory(prefix="grapple_package_") as folder:
    archive = Path(folder) / "apex_grapple.sdkmod"
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as built:
        for path in files:
            built.write(path, path.relative_to(HERE).as_posix())
    with zipfile.ZipFile(archive) as z:
        assert "apex_grapple/control_capture.py" not in z.namelist()
        for name in ("window", "view", "form", "bindings", "console_handoff", "console_keys"):
            assert f"apex_grapple/control_{name}.py" in z.namelist()
    code = '''
import sys
import sdk_stubs
sdk_stubs.install()
sys.path.insert(0, sys.argv[1])
import apex_grapple
from apex_grapple import control_window, control_menu, control_bindings, control_form
from apex_grapple import control_console_handoff, control_console_keys, control_view
for module in (apex_grapple, control_window, control_bindings, control_form,
               control_console_handoff, control_console_keys, control_view):
    assert sys.argv[1] in module.__file__, module.__file__
calls = []
control_window.start = lambda **kwargs: calls.append(kwargs)
control_menu.MENU.on_press(control_menu.MENU)
assert calls == [{"return_to_menu": True}]
assert not control_window.active()
print("OK | complete distributable archive, zip imports, direct menu action, no source-side dependency")
'''
    run = subprocess.run([sys.executable, "-c", code, str(archive)], cwd=HERE,
                         capture_output=True, text=True, timeout=30)
    print(run.stdout, end="")
    if run.returncode:
        raise AssertionError(run.stderr)
