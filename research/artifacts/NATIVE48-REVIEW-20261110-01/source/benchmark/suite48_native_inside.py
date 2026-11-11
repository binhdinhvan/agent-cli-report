"""Suite48 native CLI witness/bridge; executes only the pinned command in the sandbox."""
import json
import os
import pathlib
import subprocess
import time

root = pathlib.Path.cwd().parent
immutable = json.loads((root / "immutable.json").read_text())
readonly = {}
for name in immutable:
    try:
        with pathlib.Path(name).open("r+"):
            readonly[name] = False
    except OSError as error:
        readonly[name] = error.errno in (13, 30)
probe = pathlib.Path(".suite48-writable-witness")
probe.write_text("offline native preflight\n")
probe.unlink()
witness = {"project_writable": True, "immutable_readonly": readonly,
    "hidden_absent": not pathlib.Path("/grader").exists(),
    "home_hidden": not pathlib.Path("/home/tts").exists(),
    "net_namespace": os.readlink("/proc/self/ns/net"),
    "provider_key_env_absent": not any(name in os.environ for name in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY"))}
(root / "native-witness.json").write_text(json.dumps(witness))
if not all(readonly.values()) or not all(witness[k] for k in ("project_writable", "hidden_absent", "home_hidden", "provider_key_env_absent")):
    raise SystemExit(97)

# Preserve the existing bridge, while recording exact native subprocess boundaries
# separately from outer launcher/bridge startup and teardown.
original_call = subprocess.call


def measured_call(*args, **kwargs):
    start = time.monotonic()
    clock = {"started_monotonic": start}
    (root / "native-clock.json").write_text(json.dumps(clock))
    try:
        return original_call(*args, **kwargs)
    finally:
        clock["finished_monotonic"] = time.monotonic()
        clock["duration_ms"] = round((clock["finished_monotonic"] - start) * 1000)
        (root / "native-clock.json").write_text(json.dumps(clock))


subprocess.call = measured_call
import inside
inside.main()
