"""Offline suite48 writer/grader sandbox. No native CLI/model/provider or credential access."""
import difflib
import hashlib
import json
import os
import pathlib
import signal
import stat
import subprocess
import tempfile
import time

ROOT = pathlib.Path(__file__).resolve().parents[1]
SUITE = ROOT / "benchmark/suite48"
ENTRY = ROOT / "benchmark/suite48_entry.py"
LIMIT = 1024 * 1024


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def task_spec(task_id):
    manifest = json.loads((SUITE / "manifest.json").read_text())
    return next(task for task in manifest["tasks"] if task["id"] == task_id)


def sandbox(workspace, task_id, mode, writer=None, timeout=15):
    if mode not in ("execute", "public", "hidden") or (mode == "execute") != (writer is not None):
        raise ValueError("Invalid offline sandbox mode/writer")
    workspace = pathlib.Path(workspace).resolve()
    baseline = SUITE / task_id / "fixture"
    allowed = set(task_spec(task_id)["allowed_changes"])
    immutable = sorted(str(p.relative_to(baseline)) for p in baseline.rglob("*")
                       if p.is_file() and str(p.relative_to(baseline)) not in allowed)
    with tempfile.TemporaryDirectory(dir="/tmp/opencode", prefix="suite48-controller-") as temporary:
        controller = pathlib.Path(temporary)
        (controller / "immutable.json").write_text(json.dumps(immutable))
        command = ["/usr/bin/bwrap", "--unshare-user", "--unshare-pid", "--unshare-net", "--unshare-ipc", "--unshare-uts",
            "--die-with-parent", "--new-session", "--cap-drop", "ALL", "--ro-bind", "/usr", "/usr",
            "--ro-bind", "/lib", "/lib", "--ro-bind", "/lib64", "/lib64", "--symlink", "usr/bin", "/bin",
            "--proc", "/proc", "--dev", "/dev", "--tmpfs", "/tmp", "--dir", "/etc",
            "--bind" if mode == "execute" else "--ro-bind", str(workspace), "/workspace",
            "--chdir", "/workspace", "--clearenv", "--setenv", "PATH", "/usr/bin:/bin",
            "--setenv", "LANG", "C.UTF-8", "--setenv", "HOME", "/tmp",
            "--setenv", "PYTHONPATH", "/workspace:/grader" if mode == "hidden" else "/workspace",
            "--ro-bind", str(ENTRY), "/controller/entry.py"]
        if mode == "execute":
            for name in immutable:
                command += ["--ro-bind", str(workspace / name), "/workspace/" + name]
            command += ["--ro-bind", str(pathlib.Path(writer).resolve()), "/controller/apply.py",
                "--ro-bind", str(controller / "immutable.json"), "/controller/immutable.json"]
        elif mode == "hidden":
            command += ["--ro-bind", str(SUITE / task_id / "hidden"), "/grader"]
        command += ["/usr/bin/python3", "-B", "/controller/entry.py", mode]
        start = time.monotonic()
        # Regular files + RLIMIT_FSIZE bound output without unbounded communicate buffers.
        with (controller / "stdout").open("w+b") as out, (controller / "stderr").open("w+b") as err:
            process = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=out, stderr=err,
                env={"PATH": "/usr/bin:/bin"}, start_new_session=True)
            timed_out = False
            try:
                process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                timed_out = True
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
            out.seek(0)
            err.seek(0)
            stdout, stderr = out.read(LIMIT + 1), err.read(LIMIT + 1)
        overflow = len(stdout) + len(stderr) > LIMIT
        result = {"exit_code": process.returncode, "timed_out": timed_out, "output_limit_exceeded": overflow,
            "duration_ms": round((time.monotonic() - start) * 1000),
            "stdout": stdout[:LIMIT].decode(errors="replace"), "stderr": stderr[:LIMIT].decode(errors="replace")}
        if mode == "execute":
            markers = [line[len("WITNESS_JSON="):] for line in result["stdout"].splitlines() if line.startswith("WITNESS_JSON=")]
            result["witness"] = json.loads(markers[0]) if markers else None
            result["host_net_namespace"] = os.readlink("/proc/self/ns/net")
        return result


def passed(outcome):
    return outcome["exit_code"] == 0 and not outcome["timed_out"] and not outcome["output_limit_exceeded"]


def grade(project, task_id, target):
    """Snapshot only a stopped writer. Files never imported/executed in the host interpreter."""
    target = pathlib.Path(target)
    target.mkdir(exist_ok=False)
    snapshot = target / "snapshot"
    snapshot.mkdir()
    invalid, file_count, byte_count, dir_count = [], 0, 0, 0
    for directory, dirs, files in os.walk(project, followlinks=False):
        dir_count += 1
        if dir_count > 64:
            invalid.append("directory_limit")
            break
        for name in list(dirs):
            path = pathlib.Path(directory) / name
            if path.is_symlink():
                invalid.append(str(path.relative_to(project)))
                dirs.remove(name)
            elif name == "__pycache__":
                dirs.remove(name)
        for name in files:
            path = pathlib.Path(directory) / name
            relative = str(path.relative_to(project))
            file_count += 1
            if file_count > 64:
                invalid.append("file_limit")
                break
            try:
                descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
                with os.fdopen(descriptor, "rb") as handle:
                    info = os.fstat(handle.fileno())
                    if not stat.S_ISREG(info.st_mode) or info.st_size > LIMIT:
                        invalid.append(relative)
                        continue
                    data = handle.read(LIMIT + 1)
            except OSError:
                invalid.append(relative)
                continue
            byte_count += len(data)
            if len(data) > LIMIT or byte_count > 8 * LIMIT:
                invalid.append(relative)
                continue
            destination = snapshot / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(data)
    fixture = SUITE / task_id / "fixture"
    baseline = {str(p.relative_to(fixture)): p.read_bytes() for p in fixture.rglob("*") if p.is_file()}
    actual = {str(p.relative_to(snapshot)): p.read_bytes() for p in snapshot.rglob("*") if p.is_file()}
    changed = sorted(name for name in set(baseline) | set(actual) if baseline.get(name) != actual.get(name))
    # Allowed additions are explicit, but deleting an existing file is never allowed.
    scope_ok = not invalid and set(baseline) <= set(actual) and set(changed) <= set(task_spec(task_id)["allowed_changes"])
    patches = []
    for name in changed:
        patches.extend(difflib.unified_diff(baseline.get(name, b"").decode(errors="replace").splitlines(True),
            actual.get(name, b"").decode(errors="replace").splitlines(True), fromfile="before/" + name, tofile="after/" + name))
    (target / "patch.diff").write_text("".join(patches))
    start = time.monotonic()
    outcomes = {mode: sandbox(snapshot, task_id, mode) for mode in ("public", "hidden")} if scope_ok else {}
    rubric = None
    if task_id == "B-01" and outcomes:
        for line in outcomes["hidden"]["stdout"].splitlines():
            if line.startswith("RUBRIC_JSON="):
                rubric = json.loads(line[len("RUBRIC_JSON="):])
    result = {"task_id": task_id, "scope_ok": scope_ok, "changed_files": changed, "invalid_paths": invalid,
        "snapshot_sha256": {str(p.relative_to(snapshot)): digest(p) for p in snapshot.rglob("*") if p.is_file()},
        "suites": outcomes, "rubric": rubric, "grader_duration_ms": round((time.monotonic() - start) * 1000),
        "pass": scope_ok and bool(outcomes) and all(passed(value) for value in outcomes.values())}
    (target / "grading.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    return result
