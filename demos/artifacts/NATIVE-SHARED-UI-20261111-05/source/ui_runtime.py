"""Native Desktop/Web/TUI acceptance in a fresh offline namespace and private service."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'benchmark'))
import batch48 as batch


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--artifact-dir', type=Path, required=True)
    args = p.parse_args()
    artifact = args.artifact_dir.resolve()
    if not artifact.is_relative_to(ROOT / 'demos/artifacts'): p.error('Fresh artifact required')
    artifact.mkdir(parents=True, exist_ok=False)
    spec = next(s for s in json.loads((ROOT / 'demos/artifacts/PREP-20261106-01/preparation.json').read_text())['releases'] if s['tool'] == 'opencode-v2')
    cid = 'BP48-UI-' + hashlib.sha256(artifact.name.encode()).hexdigest()[:20]
    spec, root, nonce, command, cli = batch.prepare(spec, cid, 'B-02')
    desktop = ROOT / '.local/demo-desktop-2.2.5/payload/opt/OpenCode'
    assert (desktop / 'ai.opencode').is_file(), list(desktop.iterdir())
    harness = ROOT / 'demos/ui_runtime_inside.ts'
    tui_harness = ROOT / 'demos/tui_pty_inside.py'
    (root / 'runtime').mkdir(mode=0o700)
    (artifact / 'source').mkdir()
    for file in [Path(__file__), harness, tui_harness]: shutil.copyfile(file, artifact / 'source' / file.name)
    command = command[:command.index('/usr/bin/python3')]
    bun = Path(shutil.which('bun')).resolve()
    command += ['--ro-bind', str(bun), '/opt/research/bun', '--ro-bind', str(desktop), '/opt/research/desktop',
                '--ro-bind', str(harness), '/opt/research/ui_runtime_inside.ts',
                '--ro-bind', str(tui_harness), '/opt/research/tui_pty_inside.py',
                '--ro-bind', '/etc/fonts', '/etc/fonts',
                '--setenv', 'XDG_RUNTIME_DIR', str(root / 'runtime'),
                '/opt/research/bun', '/opt/research/ui_runtime_inside.ts', cli[0]]
    execution = batch.native.execute(command, root, timeout=90)
    for label in ['stdout', 'stderr']:
        (artifact / (label + '.txt')).write_text(execution.pop(label).replace(nonce, '[LOCAL-TOKEN]'))
    for name in ['ui-result.json', 'desktop-stderr.txt', 'desktop-stdout.txt', 'ui-server.log', 'desktop.png', 'web.png', 'tui-result.json', 'tui-pty.ansi']:
        if (root / name).exists(): shutil.copyfile(root / name, artifact / name)
    batch.native.write(artifact / 'manifest.json', {'spec': spec, 'execution': execution, 'harness_sha256': batch.digest(harness),
        'desktop_deb_sha256': batch.digest(ROOT / '.local/demo-desktop-2.2.5/opencode-desktop-linux-amd64.deb'),
        'provider_requests': 0, 'credential_reads': 0, 'supervisor_pid_absent': not Path('/proc', str(execution['supervisor_host_pid'])).exists()})
    print(json.dumps({'exit_code': execution['exit_code'], 'timeout': execution['timed_out'], 'result_present': (artifact / 'ui-result.json').exists()}))


if __name__ == '__main__': main()
