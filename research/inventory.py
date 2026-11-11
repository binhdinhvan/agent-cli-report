"""Kiểm kê chỉ đọc; in JSON ra stdout, không chạy binary của tool hoặc fetch Git."""

import concurrent.futures
import datetime
import json
import os
import pathlib
import platform
import re
import subprocess
import urllib.parse
import urllib.request


ROOT = pathlib.Path(__file__).resolve().parents[1]
REPOS = {
    "opencode-v1": "anomalyco/opencode",
    "opencode-v2": "anomalyco/opencode",
    "pi": "earendil-works/pi",
    "codex": "openai/codex",
}


def git(folder, *args):
    result = subprocess.run(
        ["git", "--no-optional-locks", "-C", str(folder), *args],
        text=True, capture_output=True, timeout=90,
        env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
    )
    # Không đưa stderr có thể chứa credential hoặc URL riêng vào artifact.
    return {"exit_code": result.returncode, "stdout": result.stdout.strip()}


def safe_remote(url):
    if "://" in url:
        parsed = urllib.parse.urlsplit(url)
        return urllib.parse.urlunsplit((parsed.scheme, parsed.hostname or "", parsed.path, "", ""))
    return re.sub(r"^[^/@]+@", "", url)


def local(name):
    folder = ROOT.parent / name
    origin = git(folder, "config", "--get", "remote.origin.url")
    manifests = {}
    for path in ("package.json", "packages/opencode/package.json", "packages/cli/package.json",
                 "packages/coding-agent/package.json", "codex-cli/package.json"):
        if (folder / path).is_file():
            data = json.loads((folder / path).read_text())
            manifests[path] = {key: data.get(key) for key in ("name", "version", "packageManager", "engines")}
    return {
        "head": git(folder, "rev-parse", "HEAD"),
        "commit": git(folder, "show", "-s", "--format=%H%n%cI%n%s", "HEAD"),
        "branch": git(folder, "symbolic-ref", "--short", "-q", "HEAD"),
        "status": git(folder, "status", "--porcelain=v1", "--untracked-files=normal"),
        "origin": safe_remote(origin["stdout"]),
        "describe": git(folder, "describe", "--tags", "--always"),
        "exact_tags": git(folder, "tag", "--points-at", "HEAD"),
        "manifests": manifests,
        "root_agents_present": (folder / "AGENTS.md").is_file(),
    }


def api(path):
    url = "https://api.github.com/repos/" + path
    request = urllib.request.Request(url, headers={"User-Agent": "agent-cli-report-readonly-inventory", "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.load(response)


def upstream(repo):
    # Giới hạn phạm vi rõ ràng; không coi một trang API là toàn bộ lịch sử.
    releases = api(repo + "/releases?per_page=100&page=1")
    patterns = [r"v1\.(\d+)\.(\d+)", r"v2\.(\d+)\.(\d+)"] if repo == "anomalyco/opencode" else [r"v(\d+)\.(\d+)\.(\d+)" if repo.endswith("/pi") else r"rust-v(\d+)\.(\d+)\.(\d+)"]
    remote = git(ROOT, "ls-remote", "--tags", "https://github.com/" + repo + ".git")
    refs = dict(line.split("\t", 1)[::-1] for line in remote["stdout"].splitlines()) if remote["exit_code"] == 0 else {}
    selected = []
    for pattern in patterns:
        candidates = [r for r in releases if not r["draft"] and not r["prerelease"] and re.fullmatch(pattern, r["tag_name"])]
        tags = [ref.removeprefix("refs/tags/") for ref in refs if re.fullmatch(pattern, ref.removeprefix("refs/tags/"))]
        key = lambda tag: tuple(map(int, re.fullmatch(pattern, tag).groups()))
        latest_tag = max(tags, key=key) if tags else None
        release = max(candidates, key=lambda r: key(r["tag_name"])) if candidates else None
        item = {"pattern": pattern, "highest_remote_stable_shaped_tag": latest_tag}
        if release:
            tag = release["tag_name"]
            ref = "refs/tags/" + tag
            item.update({k: release.get(k) for k in ("tag_name", "published_at", "draft", "prerelease", "html_url")})
            item["commit"] = refs.get(ref + "^{}", refs.get(ref))
            item["matches_highest_remote_tag"] = tag == latest_tag
        selected.append(item)
    return {
        "release_api": "https://api.github.com/repos/" + repo + "/releases?per_page=100&page=1",
        "releases_scanned": len(releases), "remote_tags_exit_code": remote["exit_code"],
        "selected": selected,
    }


def main():
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    with concurrent.futures.ThreadPoolExecutor(max_workers=7) as pool:
        local_jobs = {name: pool.submit(local, name) for name in REPOS}
        upstream_jobs = {repo: pool.submit(upstream, repo) for repo in set(REPOS.values())}
        result = {
            "started_at_utc": started,
            "local": {name: job.result() for name, job in local_jobs.items()},
            "upstream": {},
            "environment": {"os": platform.platform(), "architecture": platform.machine(), "logical_cpus": os.cpu_count()},
        }
        for repo, job in upstream_jobs.items():
            try:
                result["upstream"][repo] = job.result()
            except Exception as error:
                result["upstream"][repo] = {"error_type": type(error).__name__, "status": "unverified"}
    result["finished_at_utc"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
