"""Offline reasoning-r3 acceptance audit; never reads credentials or calls providers."""
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
    assert result['provider_requests'] == 0 and result['synthetic_usage'] is True
    assert len(result['runs']) == 16 and result['all_slots_executed']
    for name, expected in plan['input_sha256'].items():
        assert sha(ROOT / name) == expected, name
        assert sha(artifact / 'source' / name) == expected, name
    exchanges, lite = 0, 0
    for run in result['runs']:
        assert run['status'] == 'success' and run['validity'] == 'valid'
        assert run['grading']['pass'] and all(run['preflight_events'].values())
        assert run['supervisor_pid_absent'] and run['broker_socket_absent']
        captures = json.loads((artifact / run['slot'] / 'synthetic-payloads.json').read_text())
        assert len(captures) == len(run['requests'])
        for q, payload in zip(run['requests'], captures):
            exchanges += 1
            reasoning = q['effective_settings']['reasoning']
            native = q['native_requested_settings']['reasoning'] or {}
            assert reasoning == {**native, 'effort': 'low'} == payload['reasoning']
            assert q['reasoning_normalizer_revision'] == 'preserve-native-fields-r3'
            assert q['cost']['estimated_cost_usd'] == '0.015871'
            if q.get('responses_lite') == 'true':
                lite += 1
                assert native['context'] == reasoning['context'] == 'all_turns'
    assert lite >= 4
    for name in ['OPENAI48-R2-REVIEW-20261110-01', 'OPENAI48-REVIEW-20261110-01',
                 'CONTINUE43-REVIEW-20261110-01', 'GEMINI-SMOKE5-REVIEW-20261110-01',
                 'GOOGLE-GEMINI-SMOKE5-REVIEW-20261110-01']:
        review = json.loads((ROOT / 'research/artifacts' / name / 'validation.json').read_text())
        base = ROOT / (review.get('batch') or review['artifact'])
        assert all(sha(base / p) == h for p, h in review['raw_artifact_sha256'].items()), name
    state = json.loads((ROOT / 'research/experiment-state.json').read_text())
    assert (state['next_pilot_run_start'], state['next_pilot_config_start']) == (326, 427)
    assert state['user_requested_benchmark_pause']['new_inference_or_network_probe_authorized'] is False
    frozen = subprocess.run(['python3', '-B', 'benchmark/freeze_pilot.py', '--verify'], cwd=ROOT,
                            capture_output=True, text=True, timeout=120)
    assert frozen.returncode == 0
    return {'status': 'pass', 'scope': 'offline-only;0API/keyread/reservedIDs',
        'artifact': str(artifact.relative_to(ROOT)), 'native_synthetic_cases_passed': 16,
        'synthetic_exchanges': exchanges, 'responses_lite_context_preserved_exchanges': lite,
        'source_snapshots_match': True, 'prior_raw_retained': True, 'frozen_pilot': frozen.stdout,
        'registry': ['R-0326', 'C-0427'], 'generation_authorized': False,
        'replay': 'research/artifacts/OPENAI-REASONING-R3-REPLAY-20261110-01/replay.json',
        'raw_artifact_sha256': {str(p.relative_to(artifact)): sha(p) for p in artifact.rglob('*') if p.is_file()},
        'limitations': 'synthetic native acceptance, not provider acceptance after fix; no live retry authorization'}


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
