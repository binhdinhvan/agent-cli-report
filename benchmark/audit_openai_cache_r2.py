"""Verify saved cache-r2 offline acceptance and immutable history; no API/key access."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit(artifact):
    plan = json.loads((artifact / 'plan.json').read_text())
    result = json.loads((artifact / 'result.json').read_text())
    assert plan['generation_authorized'] is False and result['generation_authorized'] is False
    for name, expected in plan['input_sha256'].items():
        assert sha(ROOT / name) == expected, name
        assert sha(artifact / 'source' / name) == expected, name
    assert result['provider_requests'] == 0 and result['synthetic_usage'] is True
    assert len(result['runs']) == 16 and result['all_slots_executed']
    assert all(r['status'] == 'success' and r['validity'] == 'valid' for r in result['runs'])
    assert len({(r['task_id'], r['tool']) for r in result['runs']}) == 16
    exchanges = 0
    for run in result['runs']:
        assert run['grading']['pass'] and all(run['preflight_events'].values())
        assert run['supervisor_pid_absent'] and run['broker_socket_absent']
        for q in run['requests']:
            exchanges += 1
            assert q['cost']['usage']['input_tokens_details']['cache_write_tokens'] == 3109
            assert q['cost']['estimated_cost_usd'] == '0.015871'
            assert q['cost']['conservative_upper_bound'] is True
    for name in ['OPENAI48-REVIEW-20261110-01', 'CONTINUE43-REVIEW-20261110-01',
                 'GEMINI-SMOKE5-REVIEW-20261110-01', 'GOOGLE-GEMINI-SMOKE5-REVIEW-20261110-01']:
        review = json.loads((ROOT / 'research/artifacts' / name / 'validation.json').read_text())
        base = ROOT / (review.get('batch') or review['artifact'])
        assert all(sha(base / p) == expected for p, expected in review['raw_artifact_sha256'].items()), name
    state = json.loads((ROOT / 'research/experiment-state.json').read_text())
    assert (state['next_pilot_run_start'], state['next_pilot_config_start']) == (274, 375)
    assert state['openai48']['generation_authorized'] is False
    assert state['user_requested_benchmark_pause']['new_inference_or_network_probe_authorized'] is False
    frozen = subprocess.run(['python3', '-B', 'benchmark/freeze_pilot.py', '--verify'], cwd=ROOT,
                            capture_output=True, text=True, timeout=120)
    assert frozen.returncode == 0
    return {'status': 'pass', 'scope': 'offline-only;0API/key-read', 'artifact': str(artifact.relative_to(ROOT)),
        'native_synthetic_cases_passed': 16, 'synthetic_exchanges': exchanges,
        'provider_requests': 0, 'new_run_ids_reserved': 0,
        'prior_raw_retained': True, 'source_snapshots_match': True,
        'registry': ['R-0274', 'C-0375'], 'generation_authorized': False,
        'frozen_pilot': frozen.stdout,
        'raw_artifact_sha256': {str(p.relative_to(artifact)): sha(p) for p in artifact.rglob('*') if p.is_file()},
        'replay': 'research/artifacts/OPENAI-CACHE-R2-REPLAY-20261110-01/replay.json',
        'limits': 'synthetic native acceptance only; future live revision/approval/IDs/carry still required'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--artifact-dir', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.artifact_dir.resolve())
    args.output_dir.mkdir(parents=True, exist_ok=False)
    (args.output_dir / 'validation.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'raw_artifact_sha256'}, ensure_ascii=False))


if __name__ == '__main__':
    main()
