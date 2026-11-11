"""Chỉ chạy witness, --version và --help trong bwrap không mạng; không gửi prompt."""

import argparse
import datetime
import hashlib
import json
import os
import pathlib
import signal
import subprocess
import time
from environment_profile import environment_profile


ROOT = pathlib.Path(__file__).resolve().parents[1]
RUNTIME = pathlib.Path("/tmp/opencode/agent-cli-report/smoke")


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def sha256(path):
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def profile(spec):
    root = pathlib.Path(spec["runtime_root"]).resolve()
    if root != RUNTIME / spec["config_id"] or not root.is_dir():
        raise ValueError("Unexpected runtime root")
    payload = pathlib.Path(spec["payload"]).resolve()
    expected = ROOT / ".local/binaries" / f"{spec['tool']}-{spec['version']}" / "payload"
    if payload != expected.resolve():
        raise ValueError("Unexpected binary payload")
    binary = pathlib.Path(spec["binary"]).resolve()
    if not binary.is_relative_to(payload) or sha256(binary) != spec["binary_sha256"]:
        raise ValueError("Executable hash/path changed")
    dependencies = environment_profile(spec.get("environment_revision", "legacy"))
    env = {
        "HOME": str(root / "home"), "PATH": dependencies["path"], "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8", "TZ": "UTC", "TERM": "dumb", "NO_COLOR": "1",
        "USER": "research", "LOGNAME": "research", "SHELL": "/bin/sh",
        "TMPDIR": str(root / "tmp"),
        **{f"XDG_{kind.upper()}_HOME": str(root / f"xdg-{kind}") for kind in ("config", "data", "cache", "state")},
    }
    if spec["tool"].startswith("opencode"):
        env.update({
            "OPENCODE_TEST_HOME": env["HOME"], "OPENCODE_CONFIG_DIR": str(root / "xdg-config/opencode"),
            "OPENCODE_DB": str(root / "xdg-data/opencode/smoke.db"),
            "OPENCODE_DISABLE_AUTOUPDATE": "1", "OPENCODE_DISABLE_MODELS_FETCH": "1",
        })
        if spec["tool"] == "opencode-v1":
            env.update({"OPENCODE_DISABLE_PROJECT_CONFIG": "1", "OPENCODE_TEST_MANAGED_CONFIG_DIR": str(root / "managed")})
        else:
            env.update({"OPENCODE_CONFIG_PROJECT_DISABLE": "1", "OPENCODE_DISABLE_CLAUDE_CODE": "1"})
    elif spec["tool"] == "pi":
        env.update({"PI_CODING_AGENT_DIR": str(root / "agent"), "PI_CODING_AGENT_SESSION_DIR": str(root / "sessions")})
    else:
        env["CODEX_HOME"] = str(root / "codex-home")
    inside = pathlib.Path("/opt/agent-cli-report") / spec["config_id"]
    command = [
        "/usr/bin/bwrap", "--unshare-user", "--unshare-pid", "--unshare-net", "--unshare-ipc", "--unshare-uts",
        "--die-with-parent", "--new-session", "--cap-drop", "ALL",
        "--ro-bind", "/usr", "/usr", "--ro-bind", "/lib", "/lib", "--ro-bind", "/lib64", "/lib64",
        "--symlink", "usr/bin", "/bin", "--symlink", "usr/sbin", "/sbin",
        "--proc", "/proc", "--dev", "/dev", "--tmpfs", "/tmp", "--dir", "/etc",
        "--bind", str(root), str(root), "--ro-bind", str(payload), str(inside),
        "--chdir", str(root / "project"), "--clearenv",
    ]
    command += dependencies["mounts"]
    for key, value in sorted(env.items()):
        command.extend(["--setenv", key, value])
    return command, str(inside / binary.relative_to(payload)), env


def ensure_fresh_id(config_id):
    state_path = ROOT / "research/experiment-state.json"
    if state_path.exists() and config_id in json.loads(state_path.read_text()).get("retired_config_ids", []):
        raise ValueError("Config ID retired after user-authorized result deletion; choose a fresh ID")


def run(command):
    started = now()
    clock = time.monotonic()
    process = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               env={"PATH": "/usr/bin:/bin"}, start_new_session=True)
    timed_out = False
    try:
        stdout, stderr = process.communicate(timeout=45)
    except subprocess.TimeoutExpired:
        timed_out = True
        os.killpg(process.pid, signal.SIGTERM)
        try:
            stdout, stderr = process.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            stdout, stderr = process.communicate()
    return {
        "started_at_utc": started, "finished_at_utc": now(), "duration_ms": round((time.monotonic() - clock) * 1000),
        "supervisor_host_pid": process.pid, "exit_code": process.returncode, "timed_out": timed_out,
        "command": command, "stdout": stdout.decode("utf-8", errors="replace"),
        "stderr": stderr.decode("utf-8", errors="replace"),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preparation", type=pathlib.Path, required=True)
    parser.add_argument("--artifact-dir", type=pathlib.Path, required=True)
    args = parser.parse_args()
    artifact = args.artifact_dir.resolve()
    if not artifact.is_relative_to(ROOT / "demos/artifacts"):
        parser.error("Artifact must be under demos/artifacts")
    artifact.mkdir(parents=True, exist_ok=False)
    specs = json.loads(args.preparation.read_text())["releases"]
    sentinel = RUNTIME / f"host-only-{artifact.name}.txt"
    sentinel.write_text("Harmless isolation witness; created only in experiment root.\n")
    host_net = os.readlink("/proc/self/ns/net")
    witness_code = (
        "import json,os,pathlib; "
        f"checks={{'host_home_hidden':not pathlib.Path('/home/tts').exists(),"
        f"'host_sentinel_hidden':not pathlib.Path({str(sentinel)!r}).exists(),"
        f"'private_network_namespace':os.readlink('/proc/self/ns/net')!={host_net!r},"
        "'cwd_in_private_home_tree':pathlib.Path.cwd().parent==pathlib.Path(os.environ['HOME']).parent,"
        "'no_provider_credentials':not any(k.endswith('API_KEY') or k in ['OPENCODE_PASSWORD','OPENCODE_SERVER_PASSWORD'] for k in os.environ)}; "
        "print(json.dumps(checks,sort_keys=True)); raise SystemExit(0 if all(checks.values()) else 1)"
    )
    result = {"started_at_utc": now(), "scope": "metadata_only_no_model_no_service", "profiles": []}
    for spec in specs:
        record = {"tool": spec["tool"], "config_id": spec["config_id"], "expected_version": spec["version"], "commands": []}
        result["profiles"].append(record)
        if spec["status"] != "prepared_not_executed":
            record["status"] = "blocked_preparation"
            continue
        sandbox, executable, env = profile(spec)
        record["environment"] = env  # This allowlist contains no credential values.
        record["binary_sha256"] = spec["binary_sha256"]
        witness = run([*sandbox, "--", "/usr/bin/python3", "-c", witness_code])
        record["witness"] = witness
        if witness["exit_code"] != 0:
            record["status"] = "blocked_isolation_witness"
        else:
            for flag in ("--version", "--help"):
                item = run([*sandbox, "--", executable, flag])
                item["label"] = flag
                record["commands"].append(item)
            version, help_result = record["commands"]
            matched = version["exit_code"] == 0 and spec["version"] in version["stdout"]
            record["status"] = "metadata_pass" if matched and help_result["exit_code"] == 0 else "metadata_failure"
        (artifact / "preflight.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
        print(f"{spec['tool']}: {record['status']}", flush=True)
    result["finished_at_utc"] = now()
    (artifact / "preflight.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    if any(item["status"] != "metadata_pass" for item in result["profiles"]):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
