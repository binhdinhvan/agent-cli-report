"""Chạy HTTP API/session-metadata acceptance tests v1/v2 trong sandbox không mạng."""

import argparse
import datetime
import hashlib
import json
import os
import pathlib
import shutil
import signal
import subprocess
import sys

sys.dont_write_bytecode = True
from preflight import profile


ROOT = pathlib.Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preparation", type=pathlib.Path, required=True)
    parser.add_argument("--artifact-dir", type=pathlib.Path, required=True)
    args = parser.parse_args()
    artifact = args.artifact_dir.resolve()
    if not artifact.is_relative_to(ROOT / "demos/artifacts"):
        parser.error("Artifact must be under demos/artifacts")
    artifact.mkdir(parents=True, exist_ok=False)
    harness = ROOT / "demos/offline_api_inside.py"
    result = {"started_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
              "script_sha256": {str(path.relative_to(ROOT)): digest(path) for path in [pathlib.Path(__file__), harness, ROOT / "demos/preflight.py"]},
              "profiles": []}
    specs = json.loads(args.preparation.read_text())["releases"]
    for spec in specs:
        if spec["tool"] not in {"opencode-v1", "opencode-v2"}:
            continue
        if spec["status"] != "prepared_not_executed":
            raise ValueError("Preparation did not complete")
        demo_id = artifact.name + "-" + spec["tool"]
        destination = artifact / spec["tool"]
        destination.mkdir()
        sandbox, executable, env = profile(spec)
        # Mount only the harness, not the report workspace or source repos.
        sandbox.extend(["--ro-bind", str(harness), "/opt/research/offline_api_inside.py"])
        command = [*sandbox, "--", "/usr/bin/python3", "/opt/research/offline_api_inside.py",
                   "--executable", executable, "--tool", spec["tool"], "--demo-id", demo_id,
                   "--host-net", os.readlink("/proc/self/ns/net")]
        process = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   env={"PATH": "/usr/bin:/bin"}, start_new_session=True)
        timed_out = False
        try:
            stdout, stderr = process.communicate(timeout=120)
        except subprocess.TimeoutExpired:
            timed_out = True
            os.killpg(process.pid, signal.SIGTERM)
            try:
                stdout, stderr = process.communicate(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                stdout, stderr = process.communicate()
        (destination / "harness.stdout.json").write_bytes(stdout)
        (destination / "harness.stderr.txt").write_bytes(stderr)
        run_output = pathlib.Path(spec["runtime_root"]) / "api-offline" / demo_id
        for name in ("result.json", "openapi.json"):
            source = run_output / name
            if source.is_file():
                shutil.copyfile(source, destination / name)
        status = "timeout" if timed_out else "harness_error"
        if (destination / "result.json").is_file():
            status = json.loads((destination / "result.json").read_text())["status"]
        result["profiles"].append({"tool": spec["tool"], "config_id": spec["config_id"], "demo_id": demo_id,
                                   "binary_sha256": spec["binary_sha256"], "sandbox_command": command,
                                   "environment_without_server_credential": env, "supervisor_host_pid": process.pid,
                                   "exit_code": process.returncode, "timed_out": timed_out, "status": status})
        (artifact / "summary.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
        print(f"{spec['tool']}: {status}", flush=True)
    result["finished_at_utc"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    (artifact / "summary.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    if len(result["profiles"]) != 2 or any(item["status"] != "offline_api_pass" for item in result["profiles"]):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
