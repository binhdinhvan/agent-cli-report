"""Tải/kiểm tra/extract release đã pin; không installer, build hoặc chạy binary tool."""

import argparse
import concurrent.futures
import datetime
import hashlib
import json
import pathlib
import platform
import shutil
import tarfile
import urllib.request


ROOT = pathlib.Path(__file__).resolve().parents[1]
RUNTIME = pathlib.Path("/tmp/opencode/agent-cli-report/smoke")


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def digest(path):
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def request(url):
    return urllib.request.urlopen(
        urllib.request.Request(url, headers={"User-Agent": "agent-cli-report-preparation"}), timeout=90,
    )


def prepare(spec):
    directory = ROOT / ".local/binaries" / f"{spec['tool']}-{spec['version']}"
    runtime = RUNTIME / spec["config_id"]
    result = {**spec, "started_at_utc": now(), "status": "pending"}
    try:
        if directory.exists() or runtime.exists():
            raise FileExistsError("Target already exists; inspect previous attempt, do not overwrite")
        api = f"https://api.github.com/repos/{spec['repository']}/releases/tags/{spec['tag']}"
        with request(api) as response:
            release = json.load(response)
        if release["tag_name"] != spec["tag"] or release["draft"] or release["prerelease"]:
            raise ValueError("Release metadata does not match stable pin")
        asset = next(item for item in release["assets"] if item["name"] == spec["asset"])
        if asset["size"] != spec["size"] or asset["digest"] != "sha256:" + spec["sha256"]:
            raise ValueError("Asset metadata changed from approved pin")
        url = f"https://github.com/{spec['repository']}/releases/download/{spec['tag']}/{spec['asset']}"
        if asset["browser_download_url"] != url:
            raise ValueError("Unexpected asset URL")
        result.update({"release_api": api, "release_url": release["html_url"], "asset_url": url})
        directory.mkdir(parents=True)
        archive = directory / spec["asset"]
        partial = archive.with_suffix(archive.suffix + ".part")
        with request(url) as response, partial.open("xb") as output:
            shutil.copyfileobj(response, output, length=1024 * 1024)
        actual = digest(partial)
        if partial.stat().st_size != spec["size"] or actual != spec["sha256"]:
            raise ValueError("Downloaded archive checksum/size mismatch; retained .part, not extracted")
        partial.rename(archive)
        result["archive_sha256_verified"] = actual
        payload = directory / "payload"
        payload.mkdir()
        with tarfile.open(archive, "r:gz") as source:
            members = source.getmembers()
            result["archive_members"] = [
                {"name": member.name, "size": member.size,
                 "type": member.type.decode("ascii", errors="replace"), "linkname": member.linkname}
                for member in members
            ]
            # data filter rejects traversal, unsafe links and device files; never run an archive installer.
            source.extractall(payload, filter="data")
        candidates = []
        for path in payload.rglob("*"):
            if path.name not in spec["binary_names"] or not path.is_file():
                continue
            if not path.resolve().is_relative_to(payload.resolve()):
                raise ValueError("Executable resolves outside extracted payload")
            with path.open("rb") as handle:
                elf_header = handle.read(20)
            if elf_header[:4] == b"\x7fELF" and elf_header[18:20] == b"\x3e\x00":
                candidates.append(path)
        if len(candidates) != 1:
            raise ValueError(f"Expected one x86_64 ELF CLI, found {len(candidates)}")
        binary = candidates[0]
        binary.chmod(0o755)
        runtime.mkdir(parents=True)
        for name in ("home", "xdg-config/opencode", "xdg-data/opencode", "xdg-cache", "xdg-state",
                     "tmp", "managed", "agent", "codex-home", "sessions", "project"):
            (runtime / name).mkdir(parents=True)
        (runtime / "codex-home/config.toml").write_text('cli_auth_credentials_store = "file"\n')
        result.update({
            "status": "prepared_not_executed", "binary": str(binary), "binary_sha256": digest(binary),
            "payload": str(payload), "runtime_root": str(runtime),
        })
    except Exception as error:
        result.update({"status": "preparation_error", "error_type": type(error).__name__, "error": str(error)})
    result["finished_at_utc"] = now()
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact-dir", type=pathlib.Path, required=True)
    args = parser.parse_args()
    artifact = args.artifact_dir.resolve()
    if not artifact.is_relative_to(ROOT / "demos/artifacts"):
        parser.error("Artifact must be under demos/artifacts")
    if platform.system() != "Linux" or platform.machine() != "x86_64":
        parser.error("Only the pinned Linux x86_64 profile is supported")
    if not hasattr(tarfile, "data_filter"):
        parser.error("Python with tarfile data_filter is required")
    manifest = ROOT / "demos/releases.json"
    specs = json.loads(manifest.read_text())["releases"]
    if shutil.disk_usage(ROOT).free < 4 * 1024**3:
        parser.error("Require at least 4 GiB free before preparation")
    artifact.mkdir(parents=True, exist_ok=False)
    result = {"started_at_utc": now(), "manifest_sha256": digest(manifest), "releases": []}
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        for item in pool.map(prepare, specs):
            result["releases"].append(item)
            print(f"{item['tool']}: {item['status']}", flush=True)
            (artifact / "preparation.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    result["finished_at_utc"] = now()
    (artifact / "preparation.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    if any(item["status"] != "prepared_not_executed" for item in result["releases"]):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
