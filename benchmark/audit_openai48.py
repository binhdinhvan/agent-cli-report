"""Offline OpenAI cohort postcheck; no credential content or provider access."""
import argparse
from decimal import Decimal
import hashlib
import json
import os
from pathlib import Path
import re
import stat

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit(artifact):
    plan = json.loads((artifact / 'plan.json').read_text())
    summary = json.loads((artifact / 'result.json').read_text())
    assert plan['provider'] == 'https://api.openai.com/v1' and plan['model'] == 'gpt-6.1-sol'
    for name, expected in plan['input_sha256'].items():
        assert sha(artifact / 'source' / name) == expected, name
        assert sha(ROOT / name) == expected, name
    reserved = json.loads((artifact / 'reserved.json').read_text())
    assert len(reserved) == len({r['run_id'] for r in reserved}) == len({r['config_id'] for r in reserved}) == 52
    state = json.loads((ROOT / 'research/experiment-state.json').read_text())
    assert state['next_pilot_run_start'] == plan['proposed_run_start'] + 52
    assert state['next_pilot_config_start'] == plan['proposed_config_start'] + 52
    key = (ROOT / '.local/credentials/openai.key').lstat()
    assert stat.S_ISREG(key.st_mode) and key.st_uid == os.getuid() and stat.S_IMODE(key.st_mode) == 0o600
    phases = [summary['native_smoke']]
    if 'benchmark' in summary:
        assert summary['native_smoke']['native_smoke_pass']
        phases.append(summary['benchmark'])
    requests = [q for phase in phases for run in phase['runs'] for q in run['requests']]
    known = sum(Decimal(q['cost']['estimated_cost_usd']) for q in requests if q.get('cost', {}).get('estimated_cost_usd') is not None)
    unknown = sum(q.get('cost', {}).get('estimated_cost_usd') is None for q in requests)
    for phase in phases:
        assert phase['provider'] == plan['provider']
        for run in phase['runs']:
            if run.get('execution'):
                assert run['supervisor_pid_absent'] and run['broker_socket_absent']
            assert run['config_id'] in {r['config_id'] for r in reserved}
            for q in run['requests']:
                assert q['effective_settings'] == {'reasoning': {'effort': 'low'}, 'service_tier': 'default', 'store': False}
                assert q['effective_max_output_tokens'] <= 2048
    hashes = {}
    for path in artifact.rglob('*'):
        if path.is_file():
            raw = path.read_bytes()
            assert not re.search(rb'\bsk-[A-Za-z0-9_-]{24,}|Bearer\s+[A-Za-z0-9_.-]{24,}', raw), str(path)
            hashes[str(path.relative_to(artifact))] = sha(path)
    return {'status': 'pass', 'scope': 'offline postcheck only;0API/key-content-read',
        'artifact': str(artifact.relative_to(ROOT)), 'raw_artifact_sha256': hashes,
        'cohort': 'OpenAI-direct, never pooled with old provider results',
        'provider_requests': len(requests), 'known_usage_estimated_cost_usd': str(known),
        'unpriced_requests': unknown, 'measured_charge_usd': None,
        'native_smoke_pass': summary['native_smoke']['native_smoke_pass'],
        'benchmark_attempts': len(summary.get('benchmark', {}).get('runs', [])),
        'benchmark_not_run': sum(r['status'] == 'not_run' for r in summary.get('benchmark', {}).get('plan', reserved[4:])),
        'key_metadata': 'owner regular600; contents not read',
        'secret_scan': 'heuristic only; not full publication audit',
        'source_snapshots': 'match approved inputs', 'registry': '52freshIDs reserved, no reuse',
        'limitations': ['soft estimate guard, not invoicecap', 'missing usage never zero']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--artifact-dir', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    answer = audit(args.artifact_dir.resolve())
    args.output_dir.mkdir(parents=True, exist_ok=False)
    (args.output_dir / 'validation.json').write_text(json.dumps(answer, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k: v for k, v in answer.items() if k != 'raw_artifact_sha256'}, ensure_ascii=False))


if __name__ == '__main__':
    main()
