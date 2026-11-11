"""Host DNS/TCP/TLS/HTTP read-only diagnostics; no key, auth, redirects or generation."""
import argparse
import datetime
import hashlib
import json
import os
import pathlib
import socket
import ssl
import subprocess
import sys
import time
import urllib.error
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
HOST = "api.shopaikey.com"


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def stage(kind, target):
    started = time.monotonic()
    try:
        if kind == "dns":
            addresses = []
            for family, _, _, _, address in socket.getaddrinfo(HOST, 443, type=socket.SOCK_STREAM):
                item = {"family": "IPv6" if family == socket.AF_INET6 else "IPv4", "ip": address[0]}
                if item not in addresses:
                    addresses.append(item)
            result = {"ok": True, "addresses": addresses}
        elif kind == "tcp-tls":
            with socket.create_connection((target, 443), timeout=8) as connection:
                tcp_ms = round((time.monotonic() - started) * 1000)
                with ssl.create_default_context().wrap_socket(connection, server_hostname=HOST) as secured:
                    cert = secured.getpeercert()
                    result = {"ok": True, "ip": target, "tcp_connect_ms": tcp_ms,
                              "tls_version": secured.version(), "certificate_verified": True,
                              "certificate_issuer": cert.get("issuer"), "certificate_expiry": cert.get("notAfter")}
        else:
            if target not in ["/v1/models", "/"]:
                raise ValueError("Only unauthenticated read-only paths allowed")
            opener = urllib.request.build_opener(urllib.request.ProxyHandler({}),
                urllib.request.HTTPSHandler(context=ssl.create_default_context()), NoRedirect())
            request = urllib.request.Request("https://" + HOST + target, method="GET",
                headers={"User-Agent": "agent-cli-report-network-check", "Accept": "application/json"})
            try:
                response = opener.open(request, timeout=12)
            except urllib.error.HTTPError as error:
                response = error  # 401/403 proves HTTP reached an auth gate, not a connection failure.
            with response:
                result = {"ok": True, "http_status": response.code, "path": target,
                          "response_headers": {k: response.headers.get(k) for k in ["Content-Type", "Server", "Content-Length"]},
                          "body_read": False, "authorization_sent": False, "redirect_followed": False}
    except Exception as error:
        result = {"ok": False, "error_type": type(error).__name__, "error": str(error)}
    return {"stage": kind, "target": target, **result, "duration_ms": round((time.monotonic() - started) * 1000)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact-dir", type=pathlib.Path)
    parser.add_argument("--stage", choices=["dns", "tcp-tls", "http"])
    parser.add_argument("--target", default=HOST)
    args = parser.parse_args()
    if args.stage:
        print(json.dumps(stage(args.stage, args.target)))
        return
    if args.artifact_dir is None:
        parser.error("--artifact-dir required")
    artifact = args.artifact_dir.resolve()
    if not artifact.is_relative_to(ROOT / "demos/artifacts"):
        parser.error("Artifact must be under demos/artifacts")
    artifact.mkdir(exist_ok=False)
    result = {"scope": "Host network only, direct egress like broker; no key/auth/generation",
              "host": HOST, "started_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
              "proxy_environment_variable_presence_only": {name: name in os.environ for name in
                  ["HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "NO_PROXY", "http_proxy", "https_proxy", "all_proxy", "no_proxy"]},
              "environment_proxies_used": False, "inference_requests": 0, "credential_reads": 0,
              "script_sha256": hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(), "checks": []}

    def check(kind, target):
        try:
            completed = subprocess.run([sys.executable, "-B", __file__, "--stage", kind, "--target", target],
                capture_output=True, text=True, timeout=20)
            value = json.loads(completed.stdout) if completed.returncode == 0 else {"stage": kind, "target": target, "ok": False, "error_type": "DiagnosticProcessError"}
        except subprocess.TimeoutExpired:
            value = {"stage": kind, "target": target, "ok": False, "error_type": "DiagnosticWallTimeout", "timeout_seconds": 20}
        result["checks"].append(value)
        print(json.dumps(value), flush=True)
        (artifact / "result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
        return value

    dns = check("dns", HOST)
    if dns["ok"]:
        for address in dns["addresses"][:2]:
            check("tcp-tls", address["ip"])
    check("http", "/v1/models")
    check("http", "/")
    result["finished_at_utc"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    (artifact / "result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    main()
