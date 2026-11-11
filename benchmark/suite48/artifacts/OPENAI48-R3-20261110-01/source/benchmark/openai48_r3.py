"""Explicit fresh r3 launch using preserved native reasoning and cache-r2 accounting."""
import csv
from decimal import Decimal
import json
import os
from pathlib import Path
from unittest.mock import patch

import openai48_r2 as previous
import openai48_reasoning_r3 as reasoning

r1 = previous.r1
ROOT, SUITE, STATE = previous.ROOT, previous.SUITE, previous.STATE
PROTOCOL = ROOT / 'benchmark/PROTOCOL_OPENAI48_R3.md'
SCOPE = 'openai-r3-explicit-4smoke-rerun-then48fresh-no-auto-retry'
GUARD_CARRY = Decimal('0.33970766')
OFFLINE = SUITE / 'artifacts/OPENAI48-REASONING-R3-OFFLINE-20261110-01'
REVIEW = ROOT / 'research/artifacts/OPENAI-REASONING-R3-REVIEW-20261110-01/validation.json'


def make_plan():
    state = json.loads(STATE.read_text())
    if state.get('openai48_r3_batches'):
        raise PermissionError('r3 already reserved; no automatic repeat')
    review = json.loads(REVIEW.read_text())
    if (review['status'] != 'pass' or review['native_synthetic_cases_passed'] != 16
            or review['responses_lite_context_preserved_exchanges'] != 8):
        raise ValueError('Reasoning r3 preflight not accepted')
    for name, expected in review['raw_artifact_sha256'].items():
        if r1.batch.digest(OFFLINE / name) != expected:
            raise ValueError('Reasoning r3 preflight raw drift')
    accepted = json.loads((OFFLINE / 'plan.json').read_text())
    for name, expected in accepted['input_sha256'].items():
        if r1.batch.digest(ROOT / name) != expected:
            raise ValueError('Accepted reasoning r3 source drift: ' + name)
    files = reasoning.inputs()
    for p in [Path(__file__), ROOT / 'benchmark/test_openai48_r3.py', PROTOCOL, REVIEW,
              OFFLINE / 'result.json', OFFLINE / 'plan.json']:
        files[str(p.relative_to(ROOT))] = r1.batch.digest(p)
    with r1.native.ORDER.open() as stream:
        slots = r1.native.slot_mapping(csv.DictReader(stream))
    return {'revision': 'openai48-paid-reasoning-r3', 'scope': SCOPE, 'provider': r1.BASE, 'model': r1.MODEL,
        'protocol': str(PROTOCOL.relative_to(ROOT)), 'input_sha256': files, 'slots': slots,
        'resource_identity': r1.batch.resource_identity(),
        'proposed_run_start': state['next_pilot_run_start'], 'proposed_config_start': state['next_pilot_config_start'],
        'guard_carry_usd': str(GUARD_CARRY), 'budget_estimate_usd': '16',
        'remaining_guard_usd': str(Decimal('16') - GUARD_CARRY), 'historical_unpriced_requests': 6,
        'guard_carry_components': {'historical_known_usd': '0.28655616', 'old_unknown_write_guard_reserve_usd': '0.015871',
                                  'r2_guard_estimate_including_upper_bounds_usd': '0.0372805'},
        'invoice_cap': False, 'rubric_revision': 'b01-evidence-r2', 'reasoning_effort': 'low',
        'reasoning_fields_policy': 'preserve native fields includingcontextall_turns; override onlyeffort',
        'service_tier': 'default', 'automatic_retry_fallback': False}


def validate(plan_path, approval, artifact):
    plan = json.loads(plan_path.read_text())
    if plan != make_plan():
        raise ValueError('r3 plan/source/resource/order/registry drift')
    if (approval.get('authorized') is not True or approval.get('scope') != SCOPE
            or approval.get('plan_sha256') != r1.batch.digest(plan_path)
            or approval.get('artifact') != str(artifact.relative_to(ROOT))
            or approval.get('budget_estimate_usd') != '16'
            or approval.get('prior_unknown_and_upper_estimate_acknowledged') is not True
            or approval.get('automatic_retries_authorized') is not False
            or not approval.get('approved_by') or not approval.get('approved_at_utc')):
        raise PermissionError('Bound explicit r3 rerun approval required before credential/network')
    return plan


def save_state(state):
    temp = STATE.with_suffix('.json.openai48-r3-tmp')
    with temp.open('x') as stream:
        json.dump(state, stream, ensure_ascii=False, indent=2)
        stream.write('\n'); stream.flush(); os.fsync(stream.fileno())
    os.replace(temp, STATE)


def update_state(status, **values):
    state = json.loads(STATE.read_text())
    state.setdefault('openai48_r3', {}).update(status=status, **values)
    if 'generation_authorized' in values:
        state['user_requested_benchmark_pause'].update(status='openai48_r3_' + status,
            new_inference_or_network_probe_authorized=values['generation_authorized'], authorization_scope=SCOPE,
            active_work='OpenAI reasoning-r3 explicit run: ' + status)
    save_state(state)


def reserve(plan, artifact):
    state = json.loads(STATE.read_text())
    if state.get('openai48_r3_batches') or (state['next_pilot_run_start'], state['next_pilot_config_start']) != (plan['proposed_run_start'], plan['proposed_config_start']):
        raise PermissionError('r3 registry moved/already reserved')
    used_runs, used_configs = set(), set(state.get('retired_config_ids', []))
    for key in ('benchmark48_paid_batches', 'openai48_batches', 'openai48_r2_batches'):
        for batch in state.get(key, []):
            for row in batch['reserved']:
                used_runs.add(row['run_id']); used_configs.add(row['config_id'])
    for name in ('runs.csv', 'runs-search-r2.csv', 'runs-benchmark48.csv'):
        path = ROOT / 'benchmark' / name
        if path.exists():
            with path.open() as stream:
                for row in csv.DictReader(stream):
                    used_runs.add(row.get('run_id')); used_configs.add(row.get('config_id'))
    smoke = [{'slot': f'OAI-R3-SMOKE-{i+1}', 'tool': tool, 'task_id': 'B-02', 'repetition': 'smoke',
              'attempt_kind': 'explicit_supplementary_smoke_retry', 'retry_of': f'R-{274+i:04d}'}
             for i, tool in enumerate(('opencode-v1', 'opencode-v2', 'pi', 'codex'))]
    rows = []
    for i, slot in enumerate(smoke + plan['slots']):
        row = {**slot, 'run_id': f"R-{plan['proposed_run_start']+i:04d}",
               'config_id': f"C-{plan['proposed_config_start']+i:04d}", 'status': 'not_run'}
        if row['run_id'] in used_runs or row['config_id'] in used_configs or (r1.native.RUNTIME / row['config_id']).exists():
            raise ValueError('Fresh r3 ID collision')
        rows.append(row)
    state['next_pilot_run_start'] += 52; state['next_pilot_config_start'] += 52
    state['openai48_r3_batches'] = [{'artifact': str(artifact.relative_to(ROOT)), 'reserved': rows, 'status': 'reserved'}]
    state['openai48_r3'] = {'status': 'native_smoke_running', 'artifact': str(artifact.relative_to(ROOT)),
                           'generation_authorized': True, 'scope': SCOPE}
    save_state(state)
    return rows


def dispatch(artifact, rows, plan, *, key, carry=GUARD_CARRY, smoke=False):
    with patch.object(r1, 'context', reasoning.context):
        result = r1.dispatch(artifact, rows, plan, paid=True, key=key, carry=carry, smoke=smoke)
    result.update(scope=SCOPE, revision='openai48-paid-reasoning-r3', prior_unpriced_requests=6,
                  historical_guard_carry_usd=str(GUARD_CARRY), guard_carry_includes_upper_bounds=True)
    r1.native.write(artifact / 'result.json', result)
    return result


def main():
    # Reuse the verified durable two-phase loop, without editing any historical source.
    with patch.object(previous, 'make_plan', make_plan), patch.object(previous, 'validate', validate), \
            patch.object(previous, 'reserve', reserve), patch.object(previous, 'dispatch', dispatch), \
            patch.object(previous, 'update_state', update_state), patch.object(previous, 'SCOPE', SCOPE), \
            patch.object(previous, 'GUARD_CARRY', GUARD_CARRY):
        previous.main()


if __name__ == '__main__':
    main()
