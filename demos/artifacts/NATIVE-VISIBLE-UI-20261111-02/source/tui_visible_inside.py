"""Forward a real native TUI PTY into xterm; capture bytes, never draw a fake terminal."""
import fcntl
import json
import os
from pathlib import Path
import pty
import re
import select
import struct
import subprocess
import sys
import termios
import time

root = Path(os.environ["HOME"]).parent
master, slave = pty.openpty()
fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack("HHHH", 42, 148, 0, 0))
env = dict(os.environ, TERM="xterm-256color", COLORTERM="truecolor")
env.pop("NO_COLOR", None)
command = [sys.argv[1], "--session", sys.argv[2]]
child = subprocess.Popen(command, stdin=slave, stdout=slave, stderr=slave, env=env)
os.close(slave)
raw = bytearray()
found = False
try:
    deadline = time.monotonic() + 50
    while time.monotonic() < deadline and child.poll() is None:
        if (root / "stop-tui").exists():
            break
        ready, _, _ = select.select([master, sys.stdin.fileno()], [], [], .15)
        for fd in ready:
            try:
                data = os.read(fd, 65536)
            except OSError:
                continue
            if not data:
                continue
            if fd == master:
                raw.extend(data)
                os.write(sys.stdout.fileno(), data)
                plain = re.sub(rb"\x1b\][^\x07]*(?:\x07|\x1b\\)|\x1b\[[0-?]*[ -/]*[@-~]", b"", raw)
                if not found and b"REPORT_SHARED_UI_MARKER" in plain:
                    found = True
                    (root / "tui-visible-ready.json").write_text(json.dumps({
                        "sessionID": sys.argv[2], "command": command,
                        "session_title_observed": True, "pid": child.pid,
                    }))
                if len(raw) > 2 * 1024 * 1024:
                    raise RuntimeError("TUI output cap")
            else:
                os.write(master, data)
finally:
    if child.poll() is None:
        child.terminate()
        try:
            child.wait(timeout=4)
        except subprocess.TimeoutExpired:
            child.kill()
            child.wait(timeout=3)
    os.close(master)
    (root / "tui-pty.ansi").write_bytes(raw)
    (root / "tui-result.json").write_text(json.dumps({
        "command": command, "sessionID": sys.argv[2], "session_title_observed": found,
        "pid": child.pid, "exit_code": child.returncode,
        "process_stopped": child.poll() is not None, "bytes": len(raw),
        "scope": "actual PTY bytes displayed by xterm on private Xvfb; no prompt",
    }, indent=2))
