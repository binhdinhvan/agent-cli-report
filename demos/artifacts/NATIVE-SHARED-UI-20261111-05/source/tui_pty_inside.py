"""Bounded native TUI observation via private PTY; no prompt or real user terminal."""
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

root = Path(os.environ['HOME']).parent
master, slave = pty.openpty()
fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack('HHHH', 40, 140, 0, 0))
env = {**os.environ, 'TERM': 'xterm-256color', 'COLORTERM': 'truecolor'}
env.pop('NO_COLOR', None)
command = [sys.argv[1], '--session', sys.argv[2]]
process = subprocess.Popen(command, stdin=slave, stdout=slave, stderr=slave, env=env, start_new_session=True)
os.close(slave)
chunks = []
found = False
deadline = time.monotonic() + 12
try:
    while time.monotonic() < deadline and process.poll() is None:
        ready, _, _ = select.select([master], [], [], 0.25)
        if not ready: continue
        try: data = os.read(master, 65536)
        except OSError: break
        if not data: break
        chunks.append(data)
        if b'\x1b[c' in data or b'\x1b[0c' in data: os.write(master, b'\x1b[?1;2c')
        if b'\x1b[6n' in data: os.write(master, b'\x1b[1;1R')
        text = b''.join(chunks).decode('utf-8', errors='replace')
        plain = re.sub(r'\x1b\][^\x07]*(?:\x07|\x1b\\)|\x1b\[[0-?]*[ -/]*[@-~]', '', text)
        if 'REPORT_SHARED_UI_MARKER' in plain:
            found = True
            break
        if sum(map(len, chunks)) > 2 * 1024 * 1024: break
finally:
    if process.poll() is None:
        process.terminate()
        try: process.wait(timeout=4)
        except subprocess.TimeoutExpired: process.kill(); process.wait(timeout=3)
    os.close(master)
raw = b''.join(chunks)
(root / 'tui-pty.ansi').write_bytes(raw)
result = {'command': command, 'pid': process.pid, 'exit_code': process.returncode,
          'session_title_observed': found, 'bytes': len(raw), 'process_stopped': process.poll() is not None,
          'scope': 'native TUI default managed-service discovery in isolated PTY; no prompt'}
(root / 'tui-result.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result))
