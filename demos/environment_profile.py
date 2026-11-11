"""Pinned, read-only experiment dependencies; never install or download on lookup."""
import hashlib
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
REVISIONS = ("legacy", "search-r2")


def environment_profile(revision):
    if revision == "legacy":
        return {"id": "legacy", "manifest_sha256": None, "mounts": [], "path": "/usr/bin:/bin"}
    if revision != "search-r2":
        raise ValueError("Unknown experiment environment revision")
    manifest = ROOT / "research/environment-profiles/search-r2.json"
    data = json.loads(manifest.read_text())
    if (data["id"] != revision or data["common_bin"] != ".local/environments/search-r2/bin"
            or data["sandbox_bin"] != "/opt/agent-cli-report-deps/search-r2/bin"):
        raise ValueError("Unexpected dependency manifest paths")
    directory = ROOT / data["common_bin"]
    for name, spec in data["executables"].items():
        if name != "rg":
            raise ValueError("Unreviewed environment executable")
        executable = directory / name
        if executable.is_symlink() or not executable.is_file() or not executable.stat().st_mode & 0o111:
            raise ValueError("Missing/non-executable dependency")
        if hashlib.sha256(executable.read_bytes()).hexdigest() != spec["sha256"]:
            raise ValueError("Dependency checksum mismatch")
    if set(data["executables"]) != {"rg"} or {p.name for p in directory.iterdir()} != {"rg"}:
        raise ValueError("Unexpected dependency directory contents")
    return {**data, "manifest_sha256": hashlib.sha256(manifest.read_bytes()).hexdigest(),
            "mounts": ["--ro-bind", str(directory), data["sandbox_bin"]],
            "path": data["sandbox_bin"] + ":/usr/bin:/bin"}
