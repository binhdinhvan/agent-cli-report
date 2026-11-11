"""Trace body Codex bằng SSE giả lập cục bộ; không credential/provider/generation thật."""
import copy
import argparse
import http.server
import json
import os
import pathlib
import signal
import subprocess
import sys
import threading

sys.dont_write_bytecode = True
from model_smoke import Broker, MARKER, PROMPT, ROOT, RUNTIME, config, profile, sha256, write, now
from preflight import ensure_fresh_id


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact-name", required=True)
    parser.add_argument("--config-id", required=True)
    args = parser.parse_args()
    if pathlib.Path(args.artifact_name).name != args.artifact_name or not args.config_id.startswith("C-") or not args.config_id[2:].isdigit():
        parser.error("Invalid artifact/config ID")
    ensure_fresh_id(args.config_id)
    artifact = ROOT / "demos/artifacts" / args.artifact_name
    artifact.mkdir(exist_ok=False)
    spec = copy.deepcopy(next(s for s in json.loads((ROOT / "demos/artifacts/PREP-20261106-01/preparation.json").read_text())["releases"] if s["tool"] == "codex"))
    spec["config_id"] = args.config_id
    root = RUNTIME / spec["config_id"]
    root.mkdir(exist_ok=False)
    spec["runtime_root"] = str(root)
    for directory in ["home", "tmp", "project", "xdg-config", "xdg-data", "xdg-cache", "xdg-state", "managed", "agent", "sessions", "codex-home"]:
        (root / directory).mkdir()
    (root / "project/smoke-marker.txt").write_text(MARKER + "\n")
    inside = root / "inside.py"
    bridge_source = (ROOT / "demos/model_smoke_inside.py").read_text()
    anchor = '        length = int(self.headers.get("Content-Length", "0"))'
    assert bridge_source.count(anchor) == 1
    instrumentation = '''        with (pathlib.Path.cwd().parent / "client-header-trace.jsonl").open("a") as trace:
            trace.write(json.dumps({"names": sorted(self.headers.keys()), "responses_lite": self.headers.get("x-openai-internal-codex-responses-lite")}) + "\\n")
'''
    inside.write_text(bridge_source.replace(anchor, instrumentation + anchor))
    header_module = root / "proxy_headers.py"
    header_module.write_bytes((ROOT / "demos/proxy_headers.py").read_bytes())
    nonce = "offline-inert-token-not-a-provider-key"
    arguments = config(spec, root, nonce)
    captures = []
    class Capture(http.server.BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_POST(self):
            payload = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            number = len(captures) + 1
            captures.append({"index": number, "observed_at_utc": now(), "path": self.path,
                             "header_names": sorted(self.headers.keys()), "body": payload})
            write(artifact / "requests.json", captures)
            if number == 1:
                # Simulated model output: only the fixed, harmless read command.
                item = {"type": "custom_tool_call", "id": "ctc_offline_trace_01", "call_id": "call_offline_trace_01",
                        "status": "completed", "name": "exec", "input": 'const r = await tools.exec_command({cmd:"cat smoke-marker.txt",yield_time_ms:10000,max_output_tokens:2000}); text(r.output);'}
                events = [{"type": "response.created", "response": {"id": "resp_offline_trace_01", "status": "in_progress"}},
                          {"type": "response.output_item.done", "output_index": 0, "item": item},
                          {"type": "response.completed", "response": {"id": "resp_offline_trace_01", "status": "completed", "output": [item]}}]
                data = b"".join(b"data: " + json.dumps(e).encode() + b"\n\n" for e in events)
                self.send_response(200)
                self.send_header("Content-Type", "text/event-stream")
            else:
                data = b'{"error":{"message":"Intentional offline trace stop; not a provider response"}}'
                self.send_response(418)
                self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

    server = Broker(str(root / "broker.sock"), Capture)
    os.chmod(root / "broker.sock", 0o600)
    thread = threading.Thread(target=server.serve_forever)
    thread.start()
    command, binary, env = profile(spec)
    command += ["--ro-bind", str(root / "project"), str(root / "project"), "--ro-bind", str(inside), str(inside),
                "--ro-bind", str(header_module), str(header_module),
                "--setenv", "SMOKE_PROXY_TOKEN", nonce,
                "/usr/bin/python3", str(inside), str(root / "broker.sock"), json.dumps([binary, *arguments])]
    process = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               env={"PATH": "/usr/bin:/bin"}, start_new_session=True)
    try:
        try:
            stdout, stderr = process.communicate(timeout=45)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            stdout, stderr = process.communicate()
    finally:
        server.shutdown()
        server.server_close()
        thread.join()
        (root / "broker.sock").unlink(missing_ok=True)
    (artifact / "stdout.jsonl").write_bytes(stdout)
    (artifact / "stderr.txt").write_bytes(stderr)
    header_trace = (root / "client-header-trace.jsonl").read_text()
    (artifact / "client-header-trace.jsonl").write_text(header_trace)
    summary = {"scope": "Offline simulated SSE, no provider requests; not a benchmark or model smoke result", "spec": spec,
               "finished_at_utc": now(), "exit_code": process.returncode, "requests_captured": len(captures),
               "script_sha256": sha256(pathlib.Path(__file__)), "requests_sha256": sha256(artifact / "requests.json"),
               "bridge_sha256": sha256(inside), "client_headers_before_bridge": [json.loads(line) for line in header_trace.splitlines()],
               "requests": [{"index": r["index"], "path": r["path"], "header_names": r["header_names"],
                    "model": r["body"].get("model"), "store": r["body"].get("store"),
                    "previous_response_id_present": "previous_response_id" in r["body"],
                    "tools_present": "tools" in r["body"], "body_keys": sorted(r["body"]),
                    "input_types": [i.get("type") for i in r["body"].get("input", [])]} for r in captures]}
    write(artifact / "summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
