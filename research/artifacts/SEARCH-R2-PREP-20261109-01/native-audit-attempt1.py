"""Offline native-tool audit: synthetic SSE only, no real key/provider/install."""
import copy
import argparse
import http.server
import json
import os
import pathlib
import shlex
import signal
import subprocess
import sys
import threading

sys.dont_write_bytecode = True
from model_smoke import Broker, ROOT, RUNTIME, config, profile, sha256, write, now
from environment_profile import environment_profile, REVISIONS

INVENTORY = '''import os,shutil,json,subprocess,hashlib
names=["rg","python","python3","bash","find","ls"]
paths={n:shutil.which(n) for n in names}
rg=paths["rg"]
checks={}
if rg:
    for name,args in {"files":["--files"],"search":["-n","OFFLINE_SEARCH_FIXTURE","audit.txt"]}.items():
        run=subprocess.run([rg,*args],capture_output=True,text=True)
        checks[name]={"exit_code":run.returncode,"stdout":run.stdout,"stderr":run.stderr}
    try:
        with open(rg,"r+b"): pass
        checks["rg_read_only"]=False
    except OSError:
        checks["rg_read_only"]=True
print(json.dumps({"PATH":os.environ.get("PATH"),"which":paths,"checks":checks,"rg_sha256":hashlib.sha256(open(rg,"rb").read()).hexdigest() if rg else None,"rg_version":subprocess.run([rg,"--version"],capture_output=True,text=True).stdout if rg else None}))'''
COMMAND = "python3 -B -c " + shlex.quote(INVENTORY)


def sse(items, number):
    response = {"id": f"resp_offline_{number}", "model": "gpt-6.1-sol", "status": "in_progress"}
    events = [{"type": "response.created", "response": response}]
    for index, item in enumerate(items):
        added = {**item, "status": "in_progress"}
        if item["type"] == "function_call":
            added["arguments"] = ""
        events.append({"type": "response.output_item.added", "output_index": index, "item": added})
        if item["type"] == "function_call":
            events.append({"type": "response.function_call_arguments.delta", "item_id": item["id"], "output_index": index, "delta": item["arguments"]})
            events.append({"type": "response.function_call_arguments.done", "item_id": item["id"], "output_index": index, "arguments": item["arguments"]})
        events.append({"type": "response.output_item.done", "output_index": index, "item": item})
    events.append({"type": "response.completed", "response": {**response, "status": "completed", "output": items}})
    return b"".join(b"data: " + json.dumps(e).encode() + b"\n\n" for e in events)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact-dir", type=pathlib.Path, required=True)
    parser.add_argument("--config-start", type=int, required=True)
    parser.add_argument("--rg-control", type=pathlib.Path)
    parser.add_argument("--environment-profile", choices=REVISIONS, default="legacy")
    parser.add_argument("--pilot-settings", action="store_true")
    options = parser.parse_args()
    artifact = options.artifact_dir.resolve()
    if not artifact.is_relative_to(ROOT / "demos/artifacts"):
        parser.error("Artifact must be under demos/artifacts")
    rg_control = options.rg_control.resolve() if options.rg_control else None
    if rg_control and options.environment_profile != "legacy":
        parser.error("Do not combine standardized profile with ad-hoc control")
    dependencies = environment_profile(options.environment_profile)
    if rg_control and (not rg_control.is_relative_to(ROOT / ".local/binaries") or not rg_control.is_file()):
        parser.error("Control must be an existing binary under .local/binaries; never download/install")
    artifact.mkdir(exist_ok=False)
    specs = json.loads((ROOT / "demos/artifacts/PREP-20261106-01/preparation.json").read_text())["releases"]
    result = {"scope": "Offline synthetic SSE/native tools; not model inference or benchmark", "provider_requests": 0,
              "environment_revision": options.environment_profile, "environment_manifest_sha256": dependencies["manifest_sha256"],
              "pilot_settings": options.pilot_settings,
              "rg_control": {"source": str(rg_control), "sha256": sha256(rg_control), "mode": "read-only mount in fresh test sandbox only"} if rg_control else None,
              "started_at_utc": now(), "script_sha256": sha256(pathlib.Path(__file__)), "runs": []}
    for index, original in enumerate(specs, options.config_start):
        spec = copy.deepcopy(original)
        spec["config_id"] = f"C-{index:04d}"
        spec["environment_revision"] = options.environment_profile
        root = RUNTIME / spec["config_id"]
        root.mkdir(parents=True, exist_ok=False)
        spec["runtime_root"] = str(root)
        for name in ["home", "tmp", "project", "xdg-config", "xdg-data", "xdg-cache", "xdg-state", "managed", "agent", "sessions", "codex-home"]:
            (root / name).mkdir()
        (root / "project/audit.txt").write_text("OFFLINE_SEARCH_FIXTURE\n")
        for name in ["model_smoke_inside.py", "proxy_headers.py"]:
            (root / ("inside.py" if name.startswith("model_smoke") else name)).write_bytes((ROOT / "demos" / name).read_bytes())
        if options.pilot_settings:
            sys.path.insert(0, str(ROOT / "benchmark"))
            from pilot import pilot_config
            args = pilot_config(spec, root, "offline-inert-token", "Offline read-only tool audit")
        else:
            args = config(spec, root, "offline-inert-token")
        if spec["tool"] == "pi" and not options.pilot_settings:
            args[args.index("--tools") + 1] = "read,bash"
        args[-1] = "Offline synthetic tool audit. Only inspect files/environment, do not modify files."
        captures = []
        injected = []
        tool = spec["tool"]

        class Capture(http.server.BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_POST(self):
                payload = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                if injected or len(captures) >= 6:
                    self.send_error(400, "Intentional offline audit stop; no model/provider request")
                    return
                captures.append(payload)
                names = [t.get("name") for t in payload.get("tools", [])]
                # Codex Lite tools live in additional_tools, not the root tools array.
                ready = "glob" in names or "bash" in names or (tool == "codex" and "additional_tools" in json.dumps(payload))
                items = []
                if ready and not injected:
                    if tool == "codex":
                        items = [{"type": "custom_tool_call", "id": "ctc_offline", "call_id": "call_offline", "status": "completed", "name": "exec",
                                  "input": 'const r = await tools.exec_command({cmd:' + json.dumps(COMMAND) + ',yield_time_ms:10000,max_output_tokens:2000}); text(r.output);'}]
                    else:
                        calls = [("bash" if tool in ["pi", "opencode-v1"] else "shell", {"command": COMMAND})]
                        if tool.startswith("opencode"):
                            calls.insert(0, ("glob", {"pattern": "**/*", "path": str(root / "project")}))
                            calls.insert(1, ("grep", {"pattern": "OFFLINE_SEARCH_FIXTURE", "path": str(root / "project")}))
                        items = [{"type": "function_call", "id": f"fc_offline_{n}", "call_id": f"call_offline_{n}", "status": "completed", "name": name,
                                  "arguments": json.dumps(parameters)} for n, (name, parameters) in enumerate(calls)]
                    injected.extend(items)
                else:
                    items = [{"type": "message", "id": f"msg_offline_{len(captures)}", "role": "assistant", "status": "completed",
                              "content": [{"type": "output_text", "text": "OFFLINE_AUDIT_DONE", "annotations": []}]}]
                data = sse(items, len(captures))
                self.send_response(200)
                self.send_header("Content-Type", "text/event-stream")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

        server = Broker(str(root / "broker.sock"), Capture)
        thread = threading.Thread(target=server.serve_forever)
        thread.start()
        command, binary, env = profile(spec)
        if rg_control:
            command += ["--ro-bind", str(rg_control), "/opt/audit-bin/rg", "--setenv", "PATH", "/opt/audit-bin:/usr/bin:/bin"]
        command += ["--ro-bind", str(root / "project"), str(root / "project"),
                    "--setenv", "SMOKE_PROXY_TOKEN", "offline-inert-token", "/usr/bin/python3", "-B", str(root / "inside.py"),
                    str(root / "broker.sock"), json.dumps([binary, *args])]
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.DEVNULL,
                                   env={"PATH": "/usr/bin:/bin"}, start_new_session=True)
        timed_out = False
        try:
            try:
                stdout, stderr = process.communicate(timeout=60)
            except subprocess.TimeoutExpired:
                timed_out = True
                os.killpg(process.pid, signal.SIGKILL)
                stdout, stderr = process.communicate()
        finally:
            server.shutdown()
            server.server_close()
            thread.join()
            (root / "broker.sock").unlink(missing_ok=True)
        dest = artifact / spec["config_id"]
        dest.mkdir()
        (dest / "stdout.jsonl").write_bytes(stdout)
        (dest / "stderr.txt").write_bytes(stderr)
        write(dest / "mock-requests.json", captures)
        run = {"tool": tool, "config_id": spec["config_id"], "spec": spec, "mock_requests": len(captures), "injected_items": injected,
               "exit_code": process.returncode, "timed_out": timed_out, "supervisor_host_pid": process.pid,
               "witness": json.loads((root / "witness.json").read_text()) if (root / "witness.json").exists() else None,
               "fixture_unchanged": (root / "project/audit.txt").read_text() == "OFFLINE_SEARCH_FIXTURE\n"}
        result["runs"].append(run)
        write(artifact / "result.json", result)
        print(json.dumps({k: run[k] for k in ["tool", "config_id", "mock_requests", "timed_out", "exit_code"]}), flush=True)
    result["finished_at_utc"] = now()
    write(artifact / "result.json", result)


if __name__ == "__main__":
    main()
