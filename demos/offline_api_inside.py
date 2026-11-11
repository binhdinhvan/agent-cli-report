"""Harness chạy bên trong bwrap: chỉ health/auth/events/session metadata, không prompt."""

import argparse
import base64
import datetime
import hashlib
import json
import os
import pathlib
import queue
import re
import secrets
import subprocess
import threading
import time
import urllib.error
import urllib.parse
import urllib.request


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


class Server:
    def __init__(self, executable, v2, password):
        self.v2 = v2
        self.lines = {"stdout": [], "stderr": []}
        self.ready = queue.Queue()
        self.threads = []
        env = dict(os.environ)
        env["OPENCODE_PASSWORD" if v2 else "OPENCODE_SERVER_PASSWORD"] = password
        args = [executable, "serve", "--hostname", "127.0.0.1", "--port", "0"]
        if v2:
            args.append("--stdio")
        self.record = {"started_at_utc": now(), "args": args}
        self.process = subprocess.Popen(args, stdin=subprocess.PIPE if v2 else subprocess.DEVNULL,
                                        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env)
        self.record["pid_inside_namespace"] = self.process.pid
        for label in ("stdout", "stderr"):
            thread = threading.Thread(target=self.drain, args=(label,), daemon=True)
            thread.start()
            self.threads.append(thread)

    def drain(self, label):
        for line in getattr(self.process, label):
            self.lines[label].append(line.rstrip("\n"))
            if label == "stdout":
                self.ready.put(line)
        if label == "stdout":
            self.ready.put(None)

    def endpoint(self):
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            line = self.ready.get(timeout=max(0.01, deadline - time.monotonic()))
            if line is None:
                raise RuntimeError("Server exited before readiness")
            if self.v2:
                try:
                    url = json.loads(line).get("url")
                except json.JSONDecodeError:
                    continue
            else:
                match = re.search(r"opencode server listening on (http://\S+)", line)
                url = match.group(1) if match else None
            if url:
                parsed = urllib.parse.urlsplit(url)
                if parsed.scheme != "http" or parsed.hostname != "127.0.0.1" or not parsed.port:
                    raise ValueError("Server returned a non-loopback endpoint")
                self.record["endpoint"] = url
                self.record["ready_at_utc"] = now()
                return url
        raise TimeoutError("No server readiness within 30 seconds")

    def stop(self):
        if self.process.poll() is None:
            if self.v2:
                self.record["stop_requested"] = "stdin_eof"
                self.process.stdin.close()
            else:
                self.record["stop_requested"] = "SIGTERM_exact_child"
                self.process.terminate()
            try:
                self.process.wait(timeout=8)
            except subprocess.TimeoutExpired:
                self.record["termination_fallback"] = True
                self.process.terminate()
                try:
                    self.process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    self.record["kill_fallback"] = True
                    self.process.kill()
                    self.process.wait(timeout=3)
        for thread in self.threads:
            thread.join(timeout=2)
        self.record.update({"exit_code": self.process.returncode, "stopped_at_utc": now(),
                            "stdout": self.lines["stdout"], "stderr": self.lines["stderr"]})


def read_event(response):
    data = []
    while True:
        line = response.readline()
        if not line:
            raise EOFError("SSE ended before expected event")
        value = line.decode("utf-8").rstrip("\r\n")
        if not value:
            if data:
                return json.loads("\n".join(data))
        elif value.startswith("data:"):
            data.append(value[5:].lstrip(" "))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--executable", required=True)
    parser.add_argument("--tool", choices=["opencode-v1", "opencode-v2"], required=True)
    parser.add_argument("--demo-id", required=True)
    parser.add_argument("--host-net", required=True)
    args = parser.parse_args()
    v2 = args.tool == "opencode-v2"
    root = pathlib.Path(os.environ["HOME"]).parent
    output = root / "api-offline" / args.demo_id
    output.mkdir(parents=True, exist_ok=False)
    result = {"tool": args.tool, "demo_id": args.demo_id, "started_at_utc": now(),
              "scope": "HTTP metadata only; no model, prompt, tool execution or shared host service",
              "checks": {}, "requests": [], "events": [], "server_cycles": []}
    password = secrets.token_urlsafe(32)
    token = base64.b64encode(("opencode:" + password).encode()).decode()
    wrong_token = base64.b64encode(("opencode:" + password + "-wrong").encode()).decode()
    redactions = [token, wrong_token, password]
    base_headers = {"Accept": "application/json"}
    if not v2:
        base_headers["x-opencode-directory"] = str(pathlib.Path.cwd())
    server = None
    stream = None

    def check(name, condition):
        result["checks"][name] = bool(condition)
        if not condition:
            raise AssertionError(name)

    def request(url, method, path, payload=None, auth="correct"):
        # No code path in this harness may send a model prompt or execute a tool.
        if method not in {"GET", "POST"} or (method == "POST" and path not in {"/api/session", "/session"}):
            raise ValueError("Request outside offline acceptance protocol")
        headers = dict(base_headers)
        if auth != "missing":
            headers["Authorization"] = "Basic " + (token if auth == "correct" else wrong_token)
        body = None if payload is None else json.dumps(payload).encode()
        if body is not None:
            headers["Content-Type"] = "application/json"
        call = urllib.request.Request(url + path, data=body, headers=headers, method=method)
        started = now()
        try:
            response = urllib.request.urlopen(call, timeout=8)
        except urllib.error.HTTPError as error:
            response = error
        with response:
            raw = response.read()
            try:
                decoded = json.loads(raw)
            except json.JSONDecodeError:
                decoded = raw.decode("utf-8", errors="replace")
            item = {"started_at_utc": started, "finished_at_utc": now(), "method": method, "path": path,
                    "auth_case": auth, "status": response.code, "payload": payload, "response": decoded}
            if path in {"/doc", "/openapi.json"}:
                (output / "openapi.json").write_bytes(raw)
                item["response"] = {"sha256": hashlib.sha256(raw).hexdigest(),
                                    "size": len(raw), "openapi": decoded.get("openapi")}
            result["requests"].append(item)
            return response.code, decoded

    try:
        check("host_home_hidden", not pathlib.Path("/home/tts").exists())
        check("private_network_namespace", os.readlink("/proc/self/ns/net") != args.host_net)
        check("no_provider_credentials", not any(key.endswith("API_KEY") for key in os.environ))
        check("cwd_inside_runtime", pathlib.Path.cwd() == root / "project")
        sessions = "/api/session" if v2 else "/session"
        event_path = "/api/event" if v2 else "/event"
        health = "/api/info" if v2 else "/global/health"
        server = Server(args.executable, v2, password)
        result["server_cycles"].append(server.record)
        url = server.endpoint()
        for auth in ("missing", "wrong"):
            status, _ = request(url, "GET", sessions, auth=auth)
            check("auth_" + auth + "_rejected", status == 401)
        status, info = request(url, "GET", health)
        check("health_authorized", status == 200)
        check("health_version", info["version"] == ("2.2.5" if v2 else "1.19.5"))
        if v2:
            check("health_pid_matches_child", info["pid"] == server.process.pid)
        status, schema = request(url, "GET", "/openapi.json" if v2 else "/doc")
        check("openapi_contract", status == 200 and "post" in schema["paths"][sessions])
        headers = {**base_headers, "Accept": "text/event-stream", "Authorization": "Basic " + token}
        stream = urllib.request.urlopen(urllib.request.Request(url + event_path, headers=headers), timeout=8)
        connected = read_event(stream)
        result["events"].append(connected)
        check("sse_ready_before_create", connected["type"] == "server.connected")
        result["subscription_ready_at_utc"] = now()
        payload = {"title": "offline-api-" + args.demo_id}
        if v2:
            payload["location"] = {"directory": str(pathlib.Path.cwd())}
        status, created = request(url, "POST", sessions, payload)
        session = created["data"] if v2 else created
        check("session_created", status == 200 and bool(session.get("id")))
        session_id = session["id"]
        result["session_id"] = session_id
        check("title_matches", session["title"] == payload["title"])
        for _ in range(30):
            event = read_event(stream)
            result["events"].append(event)
            if event.get("type") == "session.created" and session_id in json.dumps(event):
                break
        else:
            raise AssertionError("No correlated session.created in first 30 events")
        check("session_created_event", event.get("type") == "session.created" and session_id in json.dumps(event))
        stream.close()
        stream = None
        status, fetched = request(url, "GET", sessions + "/" + session_id)
        fetched = fetched["data"] if v2 else fetched
        check("session_get", status == 200 and fetched["id"] == session_id)
        status, listed = request(url, "GET", sessions + "?limit=10")
        listed = listed["data"] if v2 else listed
        check("session_list", status == 200 and any(item["id"] == session_id for item in listed))
        first_pid = server.process.pid
        server.stop()
        check("first_child_stopped", server.process.poll() is not None)
        if v2:
            check("stdio_eof_shutdown", not server.record.get("termination_fallback") and server.record["exit_code"] == 0)
        server = Server(args.executable, v2, password)
        result["server_cycles"].append(server.record)
        url = server.endpoint()
        check("new_process_on_restart", server.process.pid != first_pid)
        status, restored = request(url, "GET", sessions + "/" + session_id)
        restored = restored["data"] if v2 else restored
        check("metadata_survives_restart", status == 200 and restored["id"] == session_id and restored["title"] == payload["title"])
        check("file_database_created", pathlib.Path(os.environ["OPENCODE_DB"]).is_file())
        result["status"] = "offline_api_pass"
    except Exception as error:
        result.update({"status": "offline_api_failure", "error_type": type(error).__name__, "error": str(error)})
    finally:
        if stream is not None:
            stream.close()
        if server is not None:
            server.stop()
        result["finished_at_utc"] = now()
        encoded = json.dumps(result, ensure_ascii=False, indent=2)
        for secret in redactions:
            encoded = encoded.replace(secret, "[REDACTED]")
        (output / "result.json").write_text(encoded + "\n")
        print(encoded)
    return 0 if result["status"] == "offline_api_pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
