"""Capture real windows in an isolated virtual display, without model calls or real user data."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "benchmark"))
import batch48 as batch


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--artifact-dir", type=Path, required=True)
    args = p.parse_args()
    artifact = args.artifact_dir.resolve()
    if not artifact.is_relative_to(ROOT / "demos/artifacts"):
        p.error("Fresh demos artifact path required")
    artifact.mkdir(parents=True, exist_ok=False)
    spec = next(s for s in json.loads((ROOT / "demos/artifacts/PREP-20261106-01/preparation.json").read_text())["releases"] if s["tool"] == "opencode-v2")
    cid = "BP48-VIS-" + hashlib.sha256(artifact.name.encode()).hexdigest()[:20]
    spec, root, nonce, command, cli = batch.prepare(spec, cid, "B-02")
    desktop = ROOT / ".local/demo-desktop-2.2.5/payload/opt/OpenCode"
    tools = ROOT / ".local/ui-capture-tools-20261111/payload"
    assert (desktop / "ai.opencode").is_file() and (tools / "usr/bin/Xvfb").is_file()
    (root / "runtime").mkdir(mode=0o700)
    (artifact / "source").mkdir()
    for name in ["ui_recapture.py", "ui_visible_inside.ts", "tui_visible_inside.py", "x_window_inside.py"]:
        shutil.copyfile(ROOT / "demos" / name, artifact / "source" / name)
    shutil.copyfile(ROOT / ".local/ui-capture-tools-20261111/manifest.json", artifact / "tools-manifest.json")
    command = command[:command.index("/usr/bin/python3")]
    command += ["--ro-bind", str(Path(shutil.which("bun")).resolve()), "/opt/research/bun",
        "--ro-bind", str(desktop), "/opt/research/desktop", "--ro-bind", str(tools), "/opt/research/ui-tools",
        "--ro-bind", "/opt/google/chrome", "/opt/google/chrome",
        "--ro-bind", str(ROOT / "demos/ui_visible_inside.ts"), "/opt/research/ui_visible_inside.ts",
        "--ro-bind", str(ROOT / "demos/tui_visible_inside.py"), "/opt/research/tui_visible_inside.py",
        "--ro-bind", str(ROOT / "demos/x_window_inside.py"), "/opt/research/x_window_inside.py",
        "--ro-bind", "/etc/fonts", "/etc/fonts",
        "--setenv", "XDG_RUNTIME_DIR", str(root / "runtime"),
        "--setenv", "DISPLAY", ":91", "--setenv", "LD_LIBRARY_PATH", "/opt/research/ui-tools/usr/lib/x86_64-linux-gnu",
        "--setenv", "NO_AT_BRIDGE", "1", "--setenv", "GTK_IM_MODULE", "xim",
        "/usr/bin/dbus-run-session", "--", "/opt/research/bun", "/opt/research/ui_visible_inside.ts", cli[0]]
    execution = batch.native.execute(command, root, timeout=150)
    for label in ["stdout", "stderr"]:
        (artifact / (label + ".txt")).write_text(execution.pop(label).replace(nonce, "[LOCAL-TOKEN]"))
    names = ["ui-visible-result.json", "desktop-window.png", "web-browser.png", "tui-terminal.png", "desktop-boot-diagnostic.png", "failure-screen.png", "tui-pty.ansi", "tui-result.json"]
    for label in ["xvfb", "twm", "service", "desktop", "chrome", "terminal"]:
        names += [label + "-stdout.txt", label + "-stderr.txt"]
    for name in names:
        if (root / name).exists():
            shutil.copyfile(root / name, artifact / name)
    batch.native.write(artifact / "manifest.json", {
        "scope": "authorized fresh UI recapture; no provider or real user display",
        "spec": spec, "execution": execution, "command": command,
        "desktop_deb_sha256": batch.digest(ROOT / ".local/demo-desktop-2.2.5/opencode-desktop-linux-amd64.deb"),
        "provider_requests": 0, "credential_reads": 0,
        "supervisor_pid_absent": not Path("/proc", str(execution["supervisor_host_pid"])).exists(),
        "source_sha256": {f.name: batch.digest(f) for f in (artifact / "source").iterdir()},
        "artifact_sha256": {f.name: batch.digest(f) for f in artifact.iterdir() if f.is_file()},
    })
    print(json.dumps({"artifact": str(artifact.relative_to(ROOT)), "exit": execution["exit_code"], "timeout": execution["timed_out"], "result_present": (artifact / "ui-visible-result.json").exists()}))


if __name__ == "__main__":
    main()
