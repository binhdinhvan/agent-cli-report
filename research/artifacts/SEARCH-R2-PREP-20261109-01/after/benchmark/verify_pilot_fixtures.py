"""Tự kiểm tra/seal fixture pilot offline trong bwrap; không model, key hoặc repo tool."""
import argparse
import datetime
import hashlib
import json
import os
import pathlib
import shutil
import signal
import subprocess
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
TASKS = ROOT / "benchmark/tasks"

# Oracles chỉ ở supervisor, không đưa vào fixture agent hoặc coi là output của model.
INTERVAL_REFERENCE = '''def merge_intervals(intervals):
    prepared = []
    for pair in intervals:
        try:
            values = tuple(pair)
        except (TypeError, ValueError) as error:
            raise ValueError("invalid interval") from error
        if len(values) != 2 or not all(isinstance(n, int) for n in values) or values[0] >= values[1]:
            raise ValueError("invalid interval")
        prepared.append(values)
    merged = []
    for start, end in sorted(prepared):
        if merged and start < merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))
    return merged
'''
SCHEDULER_REFERENCE = '''def task_names(jobs):
    return sorted(jobs)

def execution_order(jobs):
    dependencies = {name: set(values) for name, values in jobs.items()}
    if any(value not in dependencies for values in dependencies.values() for value in values):
        raise ValueError("unknown prerequisite")
    order = []
    remaining = set(dependencies)
    while remaining:
        available = sorted(name for name in remaining if not (dependencies[name] & remaining))
        if not available:
            raise ValueError("cycle")
        name = available[0]
        remaining.remove(name)
        order.append(name)
    return order
'''


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sandbox(workspace, acceptance, suite):
    command = ["/usr/bin/bwrap", "--unshare-user", "--unshare-pid", "--unshare-net", "--unshare-ipc", "--unshare-uts",
               "--die-with-parent", "--new-session", "--cap-drop", "ALL", "--ro-bind", "/usr", "/usr",
               "--ro-bind", "/lib", "/lib", "--ro-bind", "/lib64", "/lib64", "--symlink", "usr/bin", "/bin",
               "--proc", "/proc", "--dev", "/dev", "--tmpfs", "/tmp", "--dir", "/etc",
               "--ro-bind", str(workspace), "/workspace", "--chdir", "/workspace", "--clearenv",
               "--setenv", "PATH", "/usr/bin:/bin", "--setenv", "LANG", "C.UTF-8", "--setenv", "PYTHONPATH", "/workspace"]
    if suite == "hidden":
        command += ["--ro-bind", str(acceptance), "/grader/acceptance.py", "/usr/bin/python3", "-B", "/grader/acceptance.py", "-v"]
    else:
        command += ["/usr/bin/python3", "-B", "-m", "unittest", "-v", "test_public"]
    process = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               env={"PATH": "/usr/bin:/bin"}, start_new_session=True)
    try:
        stdout, stderr = process.communicate(timeout=15)
        timed_out = False
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGKILL)
        stdout, stderr = process.communicate()
        timed_out = True
    if len(stdout) + len(stderr) > 1024 * 1024:
        raise RuntimeError("Fixture self-test output limit exceeded")
    return {"exit_code": process.returncode, "timed_out": timed_out,
            "stdout": stdout.decode(errors="replace"), "stderr": stderr.decode(errors="replace")}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact-dir", type=pathlib.Path, required=True)
    args = parser.parse_args()
    artifact = args.artifact_dir.resolve()
    if not artifact.is_relative_to(ROOT / "benchmark/artifacts"):
        parser.error("Artifact must be under benchmark/artifacts")
    artifact.mkdir(parents=True, exist_ok=False)
    result = {"created_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
              "scope": "Offline fixture self-test with supervisor-authored reference/mutants; no agent/model benchmark runs",
              "script_sha256": digest(pathlib.Path(__file__)), "tasks": [], "status": "pending"}
    references = {"P-01": ("intervals.py", INTERVAL_REFERENCE), "P-02": ("scheduler.py", SCHEDULER_REFERENCE)}
    for task_id, (module, reference) in references.items():
        task = TASKS / task_id
        record = {"task_id": task_id, "fixture_version": json.loads((task / "task.json").read_text())["fixture_version"], "files": {str(p.relative_to(task)): digest(p) for p in sorted(task.rglob("*")) if p.is_file()}, "checks": []}
        mutants = ({"touching_overlap": reference.replace("start < merged[-1][1]", "start <= merged[-1][1]"),
                    "input_mutation": reference.replace("    prepared = []", "    if isinstance(intervals, list):\n        intervals.sort()\n    prepared = []")}
                   if task_id == "P-01" else
                   {"wrong_tie_break": reference.replace("name = available[0]", "name = available[-1]"),
                    "silent_cycle": reference.replace('raise ValueError("cycle")', "return order")})
        with tempfile.TemporaryDirectory(dir="/tmp/opencode", prefix="pilot-fixture-selftest-") as temporary:
            workspace = pathlib.Path(temporary) / "project"
            shutil.copytree(task / "fixture", workspace)
            variants = {"baseline": None, "reference": reference, **mutants}
            for label, code in variants.items():
                if code is not None:
                    (workspace / module).write_text(code)
                for suite in ["public", "hidden"]:
                    outcome = sandbox(workspace, task / "acceptance.py", suite)
                    should_pass = suite == "public" or label == "reference"
                    # A failing unittest suite has exit 1 and a FAILED summary; do not confuse sandbox/import errors with detected bugs.
                    expected = (not outcome["timed_out"] and outcome["exit_code"] == 0 if should_pass else
                                not outcome["timed_out"] and outcome["exit_code"] == 1 and "FAILED (" in outcome["stderr"] and "Ran " in outcome["stderr"])
                    record["checks"].append({"variant": label, "suite": suite, "expected_pass": should_pass,
                                             "expectation_met": expected, **outcome})
        record["status"] = "pass" if all(c["expectation_met"] for c in record["checks"]) else "failure"
        result["tasks"].append(record)
    result["status"] = "pass" if all(t["status"] == "pass" for t in result["tasks"]) else "failure"
    (artifact / "preparation.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"status": result["status"], "tasks": [{"id": t["task_id"], "status": t["status"], "checks": len(t["checks"])} for t in result["tasks"]],
                      "artifact": str(artifact.relative_to(ROOT) / "preparation.json")}, indent=2))
    if result["status"] != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
