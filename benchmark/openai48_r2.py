"""Explicit fresh OpenAI rerun using verified cache-costr2, never automatic retry."""
import argparse
import csv
from decimal import Decimal
import fcntl
import json
import os
from pathlib import Path
import re
import time
from unittest.mock import patch

import openai48_cache_r2 as cache

r1 = cache.r1
ROOT, SUITE, STATE = r1.ROOT, r1.SUITE, r1.STATE
PROTOCOL = ROOT / 'benchmark/PROTOCOL_OPENAI48_R2.md'
SCOPE = 'openai-r2-explicit-4smoke-rerun-then48fresh-no-auto-retry'
PRIOR_KNOWN = Decimal('0.28655616')
PRIOR_UNPRICED = 5
UNKNOWN_WRITE_RESERVE = Decimal('0.015871')
GUARD_CARRY = PRIOR_KNOWN + UNKNOWN_WRITE_RESERVE
OFFLINE = SUITE / 'artifacts/OPENAI48-CACHE-R2-OFFLINE-20261110-01'
REVIEW = ROOT / 'research/artifacts/OPENAI-CACHE-R2-REVIEW-20261110-01/validation.json'


def make_plan():
    state = json.loads(STATE.read_text())
    if state.get('openai48_r2_batches'):
        raise PermissionError('r2 already reserved; no automatic repeat')
    review = json.loads(REVIEW.read_text())
    if review['status'] != 'pass' or review['native_synthetic_cases_passed'] != 16 or review['synthetic_exchanges'] != 40:
        raise ValueError('Cache-r2 native preflight not accepted')
    for name, expected in review['raw_artifact_sha256'].items():
        if r1.batch.digest(OFFLINE / name) != expected:
            raise ValueError('Cache-r2 preflight raw drift')
    old_plan = json.loads((OFFLINE / 'plan.json').read_text())
    for name, expected in old_plan['input_sha256'].items():
        if r1.batch.digest(ROOT / name) != expected:
            raise ValueError('Cache-r2 accepted source drift: ' + name)
    files = cache.inputs()
    for p in [Path(__file__), ROOT / 'benchmark/test_openai48_r2.py', PROTOCOL, REVIEW,
              OFFLINE / 'result.json', OFFLINE / 'plan.json',
              ROOT / 'research/artifacts/OPENAI-CACHE-R2-REPLAY-20261110-01/replay.json']:
        files[str(p.relative_to(ROOT))] = r1.batch.digest(p)
    with r1.native.ORDER.open() as stream:
        slots = r1.native.slot_mapping(csv.DictReader(stream))
    return {'revision': 'openai48-paid-cache-r2', 'scope': SCOPE, 'provider': r1.BASE, 'model': r1.MODEL,
        'protocol': str(PROTOCOL.relative_to(ROOT)), 'input_sha256': files,
        'resource_identity': r1.batch.resource_identity(), 'slots': slots,
        'proposed_run_start': state['next_pilot_run_start'], 'proposed_config_start': state['next_pilot_config_start'],
        'historical_known_usd': str(PRIOR_KNOWN), 'historical_unpriced_requests': PRIOR_UNPRICED,
        'historical_unknown_write_guard_reserve_usd': str(UNKNOWN_WRITE_RESERVE),
        'guard_carry_usd': str(GUARD_CARRY), 'budget_estimate_usd': '16',
        'remaining_guard_usd': str(Decimal('16') - GUARD_CARRY), 'invoice_cap': False,
        'cache_unknown_ttl': 'conservative12hupperestimate, not actualcharge',
        'rubric_revision': 'b01-evidence-r2', 'reasoning_effort': 'low', 'service_tier': 'default',
        'offline_native_cases_passed': 16, 'automatic_retry_fallback': False}


def validate(plan_path, approval, artifact):
    plan = json.loads(plan_path.read_text())
    if plan != make_plan():
        raise ValueError('r2 plan/source/resource/order/registry drift')
    if (approval.get('authorized') is not True or approval.get('scope') != SCOPE
            or approval.get('plan_sha256') != r1.batch.digest(plan_path)
            or approval.get('artifact') != str(artifact.relative_to(ROOT))
            or approval.get('budget_estimate_usd') != '16'
            or approval.get('prior_unknown_and_upper_estimate_acknowledged') is not True
            or approval.get('automatic_retries_authorized') is not False
            or not approval.get('approved_by') or not approval.get('approved_at_utc')):
        raise PermissionError('Bound explicit r2 rerun approval required before credential/network')
    return plan


def update_state(status, **values):
    state = json.loads(STATE.read_text())
    state.setdefault('openai48_r2', {}).update(status=status, **values)
    if 'generation_authorized' in values:
        state['user_requested_benchmark_pause'].update(status='openai48_r2_' + status,
            new_inference_or_network_probe_authorized=values['generation_authorized'], authorization_scope=SCOPE,
            active_work='OpenAI cache-r2 explicit run: ' + status)
    temp = STATE.with_suffix('.json.openai48-r2-tmp')
    with temp.open('x') as stream:
        json.dump(state, stream, ensure_ascii=False, indent=2)
        stream.write('\n'); stream.flush(); os.fsync(stream.fileno())
    os.replace(temp, STATE)


def reserve(plan, artifact):
    state = json.loads(STATE.read_text())
    if state.get('openai48_r2_batches') or (state['next_pilot_run_start'], state['next_pilot_config_start']) != (plan['proposed_run_start'], plan['proposed_config_start']):
        raise PermissionError('r2 registry moved/already reserved')
    used_runs, used_configs = set(), set(state.get('retired_config_ids', []))
    for batches in ('benchmark48_paid_batches', 'openai48_batches'):
        for batch in state.get(batches, []):
            for row in batch['reserved']:
                used_runs.add(row['run_id']); used_configs.add(row['config_id'])
    for name in ('runs.csv', 'runs-search-r2.csv', 'runs-benchmark48.csv'):
        path = ROOT / 'benchmark' / name
        if path.exists():
            with path.open() as stream:
                for row in csv.DictReader(stream):
                    used_runs.add(row.get('run_id')); used_configs.add(row.get('config_id'))
    smoke = [{'slot': f'OAI-R2-SMOKE-{i+1}', 'tool': tool, 'task_id': 'B-02', 'repetition': 'smoke',
              'attempt_kind': 'explicit_smoke_retry' if i == 0 else 'first_native_smoke',
              **({'retry_of': 'R-0222'} if i == 0 else {})}
             for i, tool in enumerate(('opencode-v1', 'opencode-v2', 'pi', 'codex'))]
    rows = []
    for i, slot in enumerate(smoke + plan['slots']):
        row = {**slot, 'run_id': f"R-{plan['proposed_run_start']+i:04d}",
               'config_id': f"C-{plan['proposed_config_start']+i:04d}", 'status': 'not_run'}
        if row['run_id'] in used_runs or row['config_id'] in used_configs or (r1.native.RUNTIME / row['config_id']).exists():
            raise ValueError('Fresh r2 ID collision')
        rows.append(row)
    state['next_pilot_run_start'] += 52; state['next_pilot_config_start'] += 52
    state['openai48_r2_batches'] = [{'artifact': str(artifact.relative_to(ROOT)), 'reserved': rows, 'status': 'reserved'}]
    state['openai48_r2'] = {'status': 'native_smoke_running', 'artifact': str(artifact.relative_to(ROOT)),
                           'generation_authorized': True, 'scope': SCOPE}
    temp = STATE.with_suffix('.json.openai48-r2-reserve')
    with temp.open('x') as stream:
        json.dump(state, stream, ensure_ascii=False, indent=2)
        stream.write('\n'); stream.flush(); os.fsync(stream.fileno())
    os.replace(temp, STATE)
    return rows


def dispatch(artifact, rows, plan, *, key, carry=GUARD_CARRY, smoke=False):
    with patch.object(r1, 'context', cache.context):
        result = r1.dispatch(artifact, rows, plan, paid=True, key=key, carry=carry, smoke=smoke)
    result.update(scope=SCOPE, revision='openai48-paid-cache-r2', prior_unpriced_requests=PRIOR_UNPRICED,
                  historical_known_usd=str(PRIOR_KNOWN), unknown_old_write_guard_reserve_usd=str(UNKNOWN_WRITE_RESERVE))
    r1.native.write(artifact / 'result.json', result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepare-plan', action='store_true')
    parser.add_argument('--paid', action='store_true')
    parser.add_argument('--artifact-dir', type=Path, required=True)
    parser.add_argument('--plan', type=Path)
    parser.add_argument('--approval', type=Path)
    args = parser.parse_args()
    artifact = args.artifact_dir.resolve()
    if not artifact.is_relative_to(SUITE / 'artifacts') or not re.fullmatch(r'[A-Za-z0-9-]+', artifact.name) or args.prepare_plan == args.paid:
        parser.error('Choose prepare-plan/paid and fresh safe suite artifact path')
    if args.prepare_plan:
        plan = make_plan(); artifact.mkdir(parents=True, exist_ok=False)
        r1.native.write(artifact / 'launch-plan.json', plan)
        return
    if not args.plan or not args.approval:
        parser.error('Bound plan/approval required')
    approval = json.loads(args.approval.read_text())
    validate(args.plan, approval, artifact)
    with (ROOT / 'research/.batch48-launch.lock').open('a') as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        plan = validate(args.plan, approval, artifact)
        artifact.mkdir(parents=True, exist_ok=False)
        rows = reserve(plan, artifact)
        summary = {'status': 'native_smoke_running', 'scope': SCOPE, 'benchmark_attempts': 0,
                   'benchmark_not_run': 48, 'measured_charge_usd': None}
        try:
            for name, value in [('plan', plan), ('approval', approval), ('reserved', rows), ('result', summary)]:
                r1.native.write(artifact / (name + '.json'), value)
            for name in plan['input_sha256']:
                dest = artifact / 'source' / name; dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes((ROOT / name).read_bytes())
            from openai_direct_check import credential
            key = credential()
            smoke_dir = artifact / 'native-smoke'; smoke_dir.mkdir()
            smoke = dispatch(smoke_dir, rows[:4], plan, key=key, smoke=True)
            summary.update(native_smoke=smoke)
            if not smoke['native_smoke_pass']:
                summary['status'] = 'native_smoke_gate_failed'
                return
            summary['status'] = 'benchmark_running'
            r1.native.write(artifact / 'result.json', summary)
            update_state('benchmark_running', generation_authorized=True)
            time.sleep(30)  # intentional cross-phase request pacing, never job polling
            bench_dir = artifact / 'benchmark'; bench_dir.mkdir()
            result = dispatch(bench_dir, rows[4:], plan, key=key,
                              carry=GUARD_CARRY + Decimal(smoke['known_usage_estimate_usd']))
            summary.update(benchmark=result, status='completed' if result['all_slots_executed'] else 'stopped',
                benchmark_attempts=len(result['runs']), benchmark_not_run=sum(r['status'] == 'not_run' for r in result['plan']))
        except Exception as error:
            summary.update(status='launcher_error', error_type=type(error).__name__)
            raise
        finally:
            r1.native.write(artifact / 'result.json', summary)
            update_state(summary['status'], generation_authorized=False, result=str((artifact / 'result.json').relative_to(ROOT)))


if __name__ == '__main__':
    main()
