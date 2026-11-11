"""Fresh offline v1 native permission API and background-subagent acceptance."""
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
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--artifact-dir', type=Path, required=True)
    parser.add_argument('--mode', choices=['permission', 'subagent'], required=True)
    args = parser.parse_args()
    artifact = args.artifact_dir.resolve()
    if not artifact.is_relative_to(ROOT / 'demos/artifacts'): parser.error('Fresh demo artifact required')
    artifact.mkdir(parents=True, exist_ok=False)
    spec = next(s for s in json.loads((ROOT / 'demos/artifacts/PREP-20261106-01/preparation.json').read_text())['releases'] if s['tool'] == 'opencode-v1')
    cid = 'BP48-V1-' + hashlib.sha256(artifact.name.encode()).hexdigest()[:20]
    spec, root, nonce, command, cli = batch.prepare(spec, cid, 'B-02')
    config_path = root / 'xdg-config/opencode/opencode.json'
    cfg = json.loads(config_path.read_text())
    cfg['permission'] = {'*': 'deny', 'bash': 'ask', 'task': 'allow'}
    cfg['agent'] = {'report_child': {'mode': 'subagent', 'description': 'Bounded research child',
                                   'prompt': 'REPORT_V1_CHILD_SYSTEM: return fixed child marker without tools.',
                                   'permission': {'*': 'deny'}}}
    batch.native.write(config_path, cfg)
    marker = {'type': 'message', 'id': 'msg_v1_fixture', 'role': 'assistant', 'status': 'completed',
              'content': [{'type': 'output_text', 'text': 'REPORT_V1_PARENT_MARKER', 'annotations': []}]}
    (root / 'final.sse').write_bytes(batch.native.sse([marker], 1))
    marker['content'][0]['text'] = 'REPORT_V1_CHILD_MARKER'
    (root / 'child.sse').write_bytes(batch.native.sse([marker], 2))
    for index in range(7):
        cmd = f'printf REPORT_PERMISSION_EXECUTED > v1-witness-{index}.txt'
        if index == 5: cmd = 'python3 -c "from pathlib import Path; Path(\'v1-witness-5.txt\').write_text(\'REPORT_PERMISSION_EXECUTED\')"'
        item = {'type': 'function_call', 'id': f'fc_v1_{index}', 'call_id': f'call_v1_{index}',
                'name': 'bash', 'status': 'completed', 'arguments': json.dumps({'command': cmd, 'description': 'Bounded research witness'})}
        (root / f'call-{index}.sse').write_bytes(batch.native.sse([item], 3 + index))
    item.update(name='task', arguments=json.dumps({'description': 'Research child marker', 'prompt': 'REPORT_V1_CHILD_SEED',
                                                  'subagent_type': 'report_child', 'background': True}))
    (root / 'task.sse').write_bytes(batch.native.sse([item], 11))
    command = command[:command.index('/usr/bin/python3')]
    bun = Path(shutil.which('bun')).resolve()
    harness = ROOT / 'demos/v1_runtime_inside.ts'
    (artifact / 'source').mkdir()
    for path in [Path(__file__), harness]: shutil.copyfile(path, artifact / 'source' / path.name)
    command += ['--ro-bind', str(bun), '/opt/research/bun', '--ro-bind', str(harness), '/opt/research/v1_runtime_inside.ts',
                '/opt/research/bun', '/opt/research/v1_runtime_inside.ts', cli[0], args.mode]
    execution = batch.native.execute(command, root, timeout=90)
    for label in ['stdout', 'stderr']:
        (artifact / (label + '.txt')).write_text(execution.pop(label).replace(nonce, '[LOCAL-TOKEN]'))
    for name in ['v1-result.json', 'v1-server.log']:
        if (root / name).exists(): shutil.copyfile(root / name, artifact / name)
    batch.native.write(artifact / 'manifest.json', {'spec': spec, 'mode': args.mode, 'execution': execution,
        'harness_sha256': batch.digest(harness), 'provider_requests': 0, 'credential_reads': 0,
        'supervisor_pid_absent': not Path('/proc', str(execution['supervisor_host_pid'])).exists()})
    print(json.dumps({'exit_code': execution['exit_code'], 'timeout': execution['timed_out'], 'result_present': (artifact / 'v1-result.json').exists()}))


if __name__ == '__main__': main()
