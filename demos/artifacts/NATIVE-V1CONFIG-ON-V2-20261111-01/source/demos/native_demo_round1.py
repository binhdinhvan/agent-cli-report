"""Isolated native plugin and permission demos; memory-only provider, no credentials."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shlex
import socket
import sys
import threading
import time
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'benchmark'))
import batch48 as batch

native = batch.native
MARKER = 'REPORT_DEMO_DONE'
WITNESS = 'report-permission-witness.txt'


def cases():
    result = [dict(id='PL01-v1', tool='opencode-v1', plugin='v1'),
              dict(id='PL02-v1-on-v2', tool='opencode-v2', plugin='v1'),
              dict(id='PL03-v2-port', tool='opencode-v2', plugin='v2')]
    for tool in ('opencode-v1', 'opencode-v2'):
        for permission in ('allow', 'deny', 'overlap-allow', 'overlap-deny', 'ask'):
            result.append(dict(id='PM-' + tool + '-' + permission, tool=tool, permission=permission))
    return result


class Provider:
    def __init__(self, case):
        self.case = case; self.captures = []; self.injected = False

    def open(self, request, timeout):
        payload = json.loads(request.data); self.captures.append(payload)
        names = [t.get('name') for t in payload.get('tools', [])]
        target = 'report_marker' if 'plugin' in self.case else ('bash' if self.case['tool'] == 'opencode-v1' else 'shell')
        # Inject denied tools as well: catalog visibility alone is not execution enforcement.
        ready = target in names or ('permission' in self.case and bool(names))
        if ready and not self.injected:
            command = 'python3 -c ' + shlex.quote('from pathlib import Path; Path("' + WITNESS + '").write_text("REPORT_PERMISSION_EXECUTED"); print("REPORT_PERMISSION_EXECUTED")')
            args = {} if 'plugin' in self.case else {'command': command}
            items = [{'type': 'function_call', 'id': 'fc_report_demo', 'call_id': 'call_report_demo',
                'name': target, 'status': 'completed', 'arguments': json.dumps(args)}]
            self.injected = True
        else:
            items = [{'type': 'message', 'id': 'msg_report_demo_' + str(len(self.captures)), 'role': 'assistant',
                'status': 'completed', 'content': [{'type': 'output_text', 'text': MARKER, 'annotations': []}]}]
        return native.Response(native.sse(items, len(self.captures)))


def configure(root, case):
    path = root / 'xdg-config/opencode/opencode.json'; cfg = json.loads(path.read_text())
    if 'plugin' in case:
        plugin = root / 'plugins/marker'; plugin.mkdir(parents=True)
        source = ROOT / ('demos/fixtures/plugin_' + case['plugin'] + '.js')
        (plugin / 'index.js').write_bytes(source.read_bytes())
        (plugin / 'package.json').write_text('{"name":"report-marker-local","type":"module","exports":"./index.js"}\n')
        if case['tool'] == 'opencode-v1':
            cfg['plugin'] = [(plugin / 'index.js').as_uri()]
            cfg['permission']['report_marker'] = 'allow'
        else:
            cfg['plugins'] = [str(plugin)]
            cfg['permissions'].append({'action': 'report_marker', 'resource': '*', 'effect': 'allow'})
    else:
        permission = case['permission']
        effects = {'allow': ['allow'], 'deny': ['deny'], 'overlap-allow': ['deny', 'allow'],
                   'overlap-deny': ['allow', 'deny'], 'ask': ['ask']}[permission]
        if case['tool'] == 'opencode-v1' or case.get('legacy_v1_config'):
            if case.get('legacy_v1_config'):
                cfg.pop('permissions', None)
                cfg['permission'] = {'*': 'deny'}
            if len(effects) == 1:
                cfg['permission']['bash'] = effects[0]
            else:
                cfg['permission']['bash'] = {'*': effects[0], 'python3 *': effects[1]}
        else:
            cfg['permissions'] = [{'action': '*', 'resource': '*', 'effect': 'deny'},
                *[{'action': 'shell', 'resource': '*' if i == 0 else 'python3 *', 'effect': effect} for i, effect in enumerate(effects)]]
    native.write(path, cfg)
    return cfg


def run(case, artifact, specs):
    dest = artifact / case['id']; dest.mkdir()
    config_id = 'BP48-DM-' + hashlib.sha256((artifact.name + '|' + case['id']).encode()).hexdigest()[:20]
    spec, root, nonce, command, cli = batch.prepare(specs[case['tool']], config_id, 'B-02')
    config = configure(root, case)
    cli[-1] = 'Execute the requested marker tool once, then reply REPORT_DEMO_DONE.'
    command[-1] = json.dumps(cli)
    provider = Provider(case); ledger = []
    rates = json.loads((ROOT / 'research/provider-pricing.json').read_text())
    handler = native.handler('OFFLINE-INERT-NOT-A-CREDENTIAL', nonce, ledger, threading.Lock(), rates,
                             time.monotonic() + 120, request_limit=6, output_limit=512)
    server = native.Broker(str(root / 'broker.sock'), handler); os.chmod(root / 'broker.sock', 0o600)
    thread = threading.Thread(target=server.serve_forever); thread.start()
    try:
        with patch.object(native.model_smoke.urllib.request, 'build_opener', return_value=provider), \
                patch.object(socket, 'create_connection', side_effect=AssertionError('Demo host forbids TCP/provider egress')):
            execution = native.execute(command, root, timeout=120)
    finally:
        server.shutdown(); server.server_close(); thread.join(); (root / 'broker.sock').unlink(missing_ok=True)
    stdout, stderr = execution.pop('stdout'), execution.pop('stderr')
    (dest / 'stdout.jsonl').write_text(stdout.replace(nonce, '[LOCAL-TOKEN]'))
    (dest / 'stderr.txt').write_text(stderr.replace(nonce, '[LOCAL-TOKEN]'))
    server_log = root / 'xdg-data/opencode/log/opencode.log'
    if server_log.is_file():
        (dest / 'isolated-server.log').write_text(server_log.read_text().replace(nonce, '[LOCAL-TOKEN]'))
    marker_tool_completed = False; tool_errors = []
    for line in stdout.splitlines():
        try: e = json.loads(line)
        except ValueError: continue
        if e.get('type') == 'tool_use':
            part = e.get('part', {}); state = part.get('state', {})
            if part.get('tool') == 'report_marker' and state.get('status') == 'completed' and 'REPORT_PLUGIN_MARKER' in state.get('output', ''):
                marker_tool_completed = True
            if state.get('status') == 'error':tool_errors.append(state)
    witness = (root / 'project' / WITNESS).is_file()
    result = {'case': case, 'spec': spec, 'config': config, 'cli': cli, 'execution': execution,
        'synthetic_transport': True, 'provider_requests': 0, 'synthetic_exchanges': len(ledger),
        'synthetic_ledger_not_real_cost': ledger, 'payloads': provider.captures,
        'marker_tool_completed': marker_tool_completed, 'shell_witness_created': witness, 'tool_errors': tool_errors,
        'isolation_pass': native.isolated(execution), 'supervisor_pid_absent': not Path('/proc', str(execution['supervisor_host_pid'])).exists(),
        'broker_socket_absent': not (root / 'broker.sock').exists(),
        'status': 'observed_pending_review'}
    # Never persist even the inert random proxy token in shared artifacts.
    text = json.dumps(result, ensure_ascii=False, indent=2).replace(nonce, '[LOCAL-TOKEN]')
    (dest / 'result.json').write_text(text + '\n')
    print(json.dumps({'case': case['id'], 'exit_code': execution['exit_code'], 'timeout': execution['timed_out'],
        'plugin_tool_completed': marker_tool_completed, 'shell_witness': witness, 'synthetic_exchanges': len(ledger)}), flush=True)
    return json.loads(text)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--artifact-dir', type=Path, required=True)
    parser.add_argument('--case', action='append')
    parser.add_argument('--legacy-v1-config', action='store_true')
    args = parser.parse_args(); artifact = args.artifact_dir.resolve()
    if not artifact.is_relative_to(ROOT / 'demos/artifacts'):
        parser.error('Fresh demos artifact directory required')
    selected = [c for c in cases() if not args.case or c['id'] in args.case]
    if args.legacy_v1_config:
        if any(c['tool'] != 'opencode-v2' or 'permission' not in c for c in selected):
            parser.error('Legacy config scope requires explicit v2 permission cases')
        selected = [{**c, 'legacy_v1_config': True} for c in selected]
    if not selected:parser.error('No matching case')
    artifact.mkdir(parents=True, exist_ok=False)
    inputs = [Path(__file__), ROOT / 'demos/NATIVE_DEMO_ROUND1.md', ROOT / 'demos/fixtures/plugin_v1.js', ROOT / 'demos/fixtures/plugin_v2.js']
    for p in inputs:
        dest = artifact / 'source' / p.relative_to(ROOT); dest.parent.mkdir(parents=True, exist_ok=True); dest.write_bytes(p.read_bytes())
    specs = {s['tool']: s for s in json.loads((ROOT / 'demos/artifacts/PREP-20261106-01/preparation.json').read_text())['releases']}
    summary = {'scope': 'native plugin/permission with in-memory scripted transport, not provider/model quality',
        'provider_requests': 0, 'credential_reads': 0, 'input_sha256': {str(p.relative_to(ROOT)): batch.digest(p) for p in inputs}, 'cases': []}
    for case in selected:
        summary['cases'].append(run(case, artifact, specs)); native.write(artifact / 'summary.json', summary)


if __name__ == '__main__':
    main()
