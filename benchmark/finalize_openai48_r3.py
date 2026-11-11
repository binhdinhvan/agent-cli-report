"""Offline audit/summary of the completed48 cohort; no API or credential content access."""
import argparse
from collections import Counter
from decimal import Decimal
import datetime
import hashlib
import json
from pathlib import Path
import statistics
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def total(requests, field):
    return sum(Decimal(q['cost'][field]) for q in requests)


def summarize(artifact):
    raw = json.loads((artifact / 'result.json').read_text())
    plan = json.loads((artifact / 'plan.json').read_text())
    smoke, bench = raw['native_smoke'], raw['benchmark']
    assert raw['status'] == 'completed' and raw['benchmark_attempts'] == 48 and raw['benchmark_not_run'] == 0
    assert smoke['native_smoke_pass'] and all(r['native_smoke_pass'] for r in smoke['runs'])
    assert bench['all_slots_executed'] and len(bench['runs']) == 48
    assert len({r['slot'] for r in bench['runs']}) == 48
    counts = Counter((r['tool'], r['task_id']) for r in bench['runs'])
    assert len(counts) == 16 and set(counts.values()) == {3}
    for name, expected in plan['input_sha256'].items():
        assert sha(artifact / 'source' / name) == expected, name
        assert sha(ROOT / name) == expected, name
    by_phase = {'native_smoke': smoke, 'benchmark': bench}
    all_requests, failures = [], []
    for phase, data in by_phase.items():
        assert len(data['runs']) == (4 if phase == 'native_smoke' else 48)
        for r in data['runs']:
            assert r['validity'] == 'valid' and r['supervisor_pid_absent'] and r['broker_socket_absent']
            assert not r['execution']['timed_out'] and not r['execution']['output_limit_exceeded']
            assert r['grading']['pass'] if phase == 'benchmark' else True
            assert len(r['requests']) <= 8
            witness = r['execution']['witness']
            assert all(witness['immutable_readonly'].values())
            assert all(witness[k] for k in ('project_writable', 'hidden_absent', 'home_hidden', 'provider_key_env_absent'))
            for q in r['requests']:
                assert q['http_status'] == 200 and q['terminal_type'] == 'response.completed' and not q.get('error_type')
                assert q['response_model'] == plan['model'] and q['response_service_tier'] == 'default'
                assert q['effective_max_output_tokens'] <= 2048
                assert q['effective_settings']['reasoning']['effort'] == 'low'
                if q.get('responses_lite') == 'true':
                    assert q['effective_settings']['reasoning']['context'] == 'all_turns'
                assert q['cost']['estimated_cost_usd'] is not None
                all_requests.append(q)
            if phase == 'benchmark' and r['status'] != 'success':
                assert r['status'] == 'failure' and r['reasons'] == ['native_error_event']
                stdout = (artifact / phase / r['slot'] / 'stdout.jsonl').read_text()
                assert 'Rejected by smoke broker' in stdout
                failures.append({'run_id': r['run_id'], 'slot': r['slot'], 'tool': r['tool'], 'task_id': r['task_id'],
                    'raw_status': r['status'], 'validity': r['validity'], 'snapshot_grader_pass': r['grading']['pass'],
                    'upstream_requests': len(r['requests']), 'cli_exit_code': r['execution']['exit_code'],
                    'interpretation': 'native_error_event after8completedupstreams and local400; consistent with requestcap8, exact rejectreason not logged; not upstream400 or wrong snapshot'})
    gaps = [(datetime.datetime.fromisoformat(b['started_at_utc']) - datetime.datetime.fromisoformat(a['finished_at_utc'])).total_seconds()
            for a, b in zip(all_requests, all_requests[1:])]
    assert len(gaps) == len(all_requests) - 1 and min(gaps) >= 30
    stats = []
    for tool in ('opencode-v1', 'opencode-v2', 'pi', 'codex'):
        runs = [r for r in bench['runs'] if r['tool'] == tool]
        requests = [q for r in runs for q in r['requests']]
        durations = [r['execution']['duration_ms'] / 1000 for r in runs]
        stats.append({'tool': tool, 'runs': 12, 'success': sum(r['status'] == 'success' for r in runs),
            'failure': sum(r['status'] == 'failure' for r in runs), 'snapshot_pass': sum(r['grading']['pass'] for r in runs),
            'median_seconds_all_attempts': statistics.median(durations), 'mean_seconds_all_attempts': statistics.mean(durations),
            'min_seconds': min(durations), 'max_seconds': max(durations), 'upstream_requests': len(requests),
            'guard_estimate_usd': str(total(requests, 'estimated_cost_usd')),
            'tariff_lower_usd_reported_usage': str(total(requests, 'published_tariff_lower_usd')),
            'input_tokens': sum(q['cost']['usage']['input_tokens'] for q in requests),
            'output_tokens': sum(q['cost']['usage']['output_tokens'] for q in requests),
            'cached_tokens': sum(q['cost']['usage']['input_tokens_details']['cached_tokens'] for q in requests),
            'cache_write_tokens': sum(q['cost']['usage']['input_tokens_details']['cache_write_tokens'] for q in requests)})
    def phase_cost(phase):
        qs = [q for r in by_phase[phase]['runs'] for q in r['requests']]
        assert str(total(qs, 'estimated_cost_usd')) == by_phase[phase]['known_usage_estimate_usd']
        return {'provider_requests': len(qs), 'guard_estimate_usd': str(total(qs, 'estimated_cost_usd')),
                'tariff_lower_usd_reported_usage': str(total(qs, 'published_tariff_lower_usd')),
                'unknown_ttl_upper_bound_requests': sum(q['cost']['conservative_upper_bound'] for q in qs)}
    carried = Decimal(plan['guard_carry_usd'])
    new = total(all_requests, 'estimated_cost_usd')
    state = json.loads((ROOT / 'research/experiment-state.json').read_text())
    assert (state['next_pilot_run_start'], state['next_pilot_config_start']) == (378, 479)
    assert state['openai48_r3']['generation_authorized'] is False
    assert state['user_requested_benchmark_pause']['new_inference_or_network_probe_authorized'] is False
    for name in ('OPENAI48-R2-REVIEW-20261110-01', 'OPENAI48-REVIEW-20261110-01', 'CONTINUE43-REVIEW-20261110-01',
                 'GEMINI-SMOKE5-REVIEW-20261110-01', 'GOOGLE-GEMINI-SMOKE5-REVIEW-20261110-01'):
        review = json.loads((ROOT / 'research/artifacts' / name / 'validation.json').read_text())
        base = ROOT / (review.get('batch') or review['artifact'])
        assert all(sha(base / p) == h for p, h in review['raw_artifact_sha256'].items()), name
    frozen = subprocess.run(['python3', '-B', 'benchmark/freeze_pilot.py', '--verify'], cwd=ROOT,
                            capture_output=True, text=True, timeout=120)
    assert frozen.returncode == 0
    elapsed = (datetime.datetime.fromisoformat(bench['finished_at_utc']) - datetime.datetime.fromisoformat(bench['started_at_utc'])).total_seconds()
    return {'status': 'pass', 'artifact': str(artifact.relative_to(ROOT)), 'scope': 'offline postcheck;0API/keyread',
        'benchmark_status': dict(Counter(r['status'] for r in bench['runs'])), 'valid_attempts': 48, 'benchmark_not_run': 0,
        'snapshot_grader_passes': 48, 'benchmark_wall_seconds': elapsed,
        'started_at_utc': bench['started_at_utc'], 'finished_at_utc': bench['finished_at_utc'],
        'native_smoke_passes': 4, 'tools': stats, 'failures': failures,
        'native_smoke_cost': phase_cost('native_smoke'), 'benchmark_cost': phase_cost('benchmark'),
        'new_guard_estimate_usd': str(new), 'carried_guard_usd': str(carried),
        'cumulative_guard_estimate_usd': str(carried + new), 'remaining_guard_usd': str(Decimal('16') - carried - new),
        'historical_unpriced_requests_retained': 6, 'new_unpriced_requests': 0, 'measured_charge_usd': None,
        'minimum_request_gap_seconds': min(gaps), 'request_gaps_checked': len(gaps),
        'registry': ['R-0378', 'C-0479'], 'source_snapshots_match': True, 'cleanup': '52supervisors/sockets absent at run completion',
        'prior_raw_retained': True, 'frozen_pilot': frozen.stdout,
        'raw_artifact_sha256': {str(p.relative_to(artifact)): sha(p) for p in artifact.rglob('*') if p.is_file()}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--artifact-dir', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    result = summarize(args.artifact_dir.resolve())
    args.output_dir.mkdir(parents=True, exist_ok=False)
    (args.output_dir / 'validation.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'raw_artifact_sha256'}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
