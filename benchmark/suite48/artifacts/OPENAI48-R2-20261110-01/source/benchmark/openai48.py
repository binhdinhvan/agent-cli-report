"""Fresh OpenAI-direct cohort; reuse sealed dispatcher without modifying historical inputs."""
import argparse
import contextlib
import csv
from decimal import Decimal
import fcntl
import json
import os
from pathlib import Path
import re
from unittest.mock import patch

import continue48 as inherited

batch = inherited.batch
native = batch.native
ROOT, SUITE, STATE = batch.ROOT, inherited.SUITE, batch.STATE
BASE = "https://api.openai.com/v1"
MODEL = "gpt-6.1-sol"
PROFILE = ROOT / "research/model-profiles/openai-gpt-6.1-sol.json"
PROTOCOL = ROOT / "benchmark/PROTOCOL_OPENAI48_R1.md"
SCOPE = "openai-direct-4-native-smoke-then48-new-slots-no-retry"
CARRY = Decimal("0.28498016")
REMAINING = Decimal("16") - CARRY
SMOKE_PROMPT = ('Use your shell execution tool to run exactly python3 -c \'print("OFF48_NATIVE_APPLY_DONE")\'. '
                'Do not edit any file. After observing successful execution, reply exactly OFF48_NATIVE_APPLY_DONE.')


def pricing():
    p = json.loads(PROFILE.read_text())
    if p['model'] != MODEL or p['provider_base_url'] != BASE:
        raise ValueError('OpenAI pricing provider mismatch')
    rates = p['pricing_usd_per_million']
    if (rates['input_uncached'], rates['input_cached'], rates['output']) != ('2', '0.10', '10'):
        raise ValueError('Pricing drift needs review')
    return {'unit_tokens': '1000000', 'input_uncached': rates['input_uncached'],
            'input_cache_read': rates['input_cached'], 'output': rates['output']}


def estimate(usage, rates):
    from estimate_provider_cost import estimate as old
    answer = old(usage, rates)
    if isinstance(usage, dict):
        details = usage.get('input_tokens_details') or {}
        if details.get('cache_write_tokens', 0) != 0 or usage.get('input_tokens', 0) > 272000:
            answer.update(estimated_cost_usd=None, reason='Cache-write or long-context billing needs review')
    answer['estimate_status'] = 'published OpenAI standard short-context rates; provider-reported usage; not invoice-confirmed'
    return answer


def config(spec, root, nonce, prompt):
    args = inherited_config(spec, root, nonce, prompt)
    tool = spec['tool']
    if tool.startswith('opencode'):
        path = root / 'xdg-config/opencode/opencode.json'
        cfg = json.loads(path.read_text())
        if tool == 'opencode-v1':
            model = cfg['provider']['openai']['models'][MODEL]
            model.update(reasoning=True, options={'reasoningEffort': 'low'})
        else:
            provider = cfg['providers'].pop('shopaikey')
            provider['name'] = 'OpenAI direct isolated broker'
            model = provider['models'][MODEL]
            model['capabilities']['reasoning'] = {'supported': True}
            model['settings'] = {'reasoningEffort': 'low'}
            model['body'] = {'reasoning': {'effort': 'low'}, 'service_tier': 'default'}
            cfg['providers']['openaidirect'] = provider
            cfg['model'] = 'openaidirect/' + MODEL
            args = [x.replace('shopaikey/', 'openaidirect/') for x in args]
        native.write(path, cfg)
    elif tool == 'pi':
        path = root / 'agent/models.json'
        cfg = json.loads(path.read_text())
        provider = cfg['providers'].pop('shopaikey')
        provider['models'][0]['reasoning'] = True
        cfg['providers']['openaidirect'] = provider
        native.write(path, cfg)
        args[args.index('--provider') + 1] = 'openaidirect'
        args[args.index('--thinking') + 1] = 'low'
    else:
        path = root / 'codex-home/config.toml'
        path.write_text(path.read_text().replace('shopaikey', 'openaidirect')
                        .replace('model_reasoning_effort = "none"', 'model_reasoning_effort = "low"'))
    return args


inherited_config = native.pilot_config


@contextlib.contextmanager
def context(*, paid=False, carry=CARRY, smoke=False):
    """All overrides process-local; never edit the frozen old cohort or its price file."""
    real_handler = native.handler
    real_request = native.model_smoke.urllib.request.Request
    real_opener = native.model_smoke.urllib.request.build_opener
    rates = pricing()

    def handler(key, nonce, ledger, lock, _old_rates, deadline, **kwargs):
        kwargs['budget_limit'] = str(Decimal('16') - carry)
        return real_handler(key, nonce, ledger, lock, rates, deadline, **kwargs)

    # Factory records effective settings on the active request ledger through this hook.
    active_ledgers = []
    base_handler = handler

    def tracked_handler(key, nonce, ledger, *args, **kwargs):
        if not active_ledgers or active_ledgers[-1] is not ledger:
            active_ledgers.append(ledger)
        return base_handler(key, nonce, ledger, *args, **kwargs)

    def request(url, data=None, **options):
        if url != BASE + '/responses':
            raise ValueError('Unexpected OpenAI endpoint')
        payload = json.loads(data)
        original = {k: payload.get(k) for k in ('reasoning', 'service_tier')}
        payload.update(reasoning={'effort': 'low'}, service_tier='default', store=False)
        if active_ledgers and active_ledgers[-1]:
            active_ledgers[-1][-1].update(native_requested_settings=original,
                effective_settings={'reasoning': payload['reasoning'], 'service_tier': 'default', 'store': False}, provider=BASE)
        return real_request(url, data=json.dumps(payload).encode(), **options)

    def opener(*args, **kwargs):
        underlying = real_opener(*args, **kwargs)

        class Opener:
            def open(self, req, timeout):
                try:
                    response = underlying.open(req, timeout=timeout)
                except native.model_smoke.urllib.error.HTTPError as error:
                    response = error
                # Never let partial-key errors reach the native CLI or saved stdout.
                class CleanResponse:
                    code = response.code
                    headers = response.headers
                    def __enter__(self):
                        response.__enter__()
                        return self
                    def __exit__(self, *exc):
                        return response.__exit__(*exc)
                    def __iter__(self):
                        for line in response:
                            clean = re.sub(rb'\bsk-[A-Za-z0-9_.*-]{4,}', b'[REDACTED-KEY]', line)
                            if line.startswith(b'data:'):
                                try:
                                    event = json.loads(line[5:])
                                except (ValueError, UnicodeDecodeError):
                                    event = {}
                                if event.get('type') in ('response.completed', 'response.incomplete', 'response.failed') and active_ledgers and active_ledgers[-1]:
                                    terminal = event.get('response', {})
                                    active_ledgers[-1][-1].update(response_service_tier=terminal.get('service_tier'),
                                        response_output_types=[x.get('type') for x in terminal.get('output', [])])
                            yield clean
                return CleanResponse()
        return Opener()

    with contextlib.ExitStack() as stack:
        for obj, name, value in [(batch, 'SUITE', inherited.REV), (inherited.runtime, 'SUITE', inherited.REV),
                (native, 'SUITE', inherited.REV), (native, 'BASE_URL', BASE),
                (native.model_smoke, 'BASE_URL', BASE), (batch, 'BUDGET', Decimal('16') - carry),
                (native, 'pilot_config', lambda s, r, n, p: config(s, r, n, SMOKE_PROMPT if smoke else p)),
                (native, 'handler', tracked_handler), (native.model_smoke, 'estimate', estimate),
                (native.model_smoke.urllib.request, 'Request', request)]:
            stack.enter_context(patch.object(obj, name, value))
        if paid:
            stack.enter_context(patch.object(native.model_smoke.urllib.request, 'build_opener', opener))
        yield


def inputs():
    files = {**batch.inputs(), **inherited.revision_inputs()}
    for path in [Path(__file__), ROOT / 'benchmark/test_openai48.py', PROTOCOL, PROFILE,
                 ROOT / 'demos/openai_direct_check.py']:
        files[str(path.relative_to(ROOT))] = batch.digest(path)
    for name in ['CONTINUE43-REVIEW-20261110-01', 'OPENAI-DIRECT-CHECK-REVIEW-20261110-01']:
        audit_path = ROOT / 'research/artifacts' / name / 'validation.json'
        audit = json.loads(audit_path.read_text())
        base = ROOT / (audit.get('batch') or audit['artifact'])
        for relative, expected in audit['raw_artifact_sha256'].items():
            if batch.digest(base / relative) != expected:
                raise ValueError('Prior raw drift: ' + relative)
        files[str(audit_path.relative_to(ROOT))] = batch.digest(audit_path)
    return files


def make_plan():
    state = json.loads(STATE.read_text())
    if state.get('openai48_batches'):
        raise PermissionError('OpenAI cohort already reserved; no auto-repeat')
    with native.ORDER.open() as stream:
        slots = native.slot_mapping(csv.DictReader(stream))
    pricing()
    return {'revision': 'openai-direct48-r1', 'scope': SCOPE, 'provider': BASE, 'model': MODEL,
        'protocol': str(PROTOCOL.relative_to(ROOT)), 'rubric_revision': 'b01-evidence-r2',
        'budget_estimate_usd': '16', 'prior_known_usd': str(CARRY), 'prior_unpriced_requests': 4,
        'remaining_known_guard_usd': str(REMAINING), 'invoice_cap': False,
        'slots': slots, 'input_sha256': inputs(), 'resource_identity': batch.resource_identity(),
        'proposed_run_start': state['next_pilot_run_start'], 'proposed_config_start': state['next_pilot_config_start'],
        'reasoning_effort': 'low', 'service_tier': 'default', 'retry_policy': 'none',
        'native_smoke_max_requests': 32, 'benchmark_max_requests': 384}


def validate(plan_path, approval):
    plan = json.loads(plan_path.read_text())
    if plan != make_plan():
        raise ValueError('OpenAI plan/hash/resource/registry drift')
    if (approval.get('authorized') is not True or approval.get('scope') != SCOPE
            or approval.get('plan_sha256') != batch.digest(plan_path)
            or approval.get('budget_estimate_usd') != '16' or approval.get('retries_authorized') is not False
            or approval.get('prior_unpriced_acknowledged') is not True or not approval.get('approved_by')
            or not approval.get('approved_at_utc')):
        raise PermissionError('Bound explicit OpenAI benchmark approval required before key/network')
    preflight = json.loads((plan_path.parent / 'offline-result.json').read_text())
    if (len(preflight['runs']) != 16 or not preflight['all_slots_executed']
            or any(r['status'] != 'success' for r in preflight['runs'])
            or approval.get('offline_sha256') != batch.digest(plan_path.parent / 'offline-result.json')):
        raise PermissionError('16/16 synthetic native preflight required')
    return plan


def reserve(plan, artifact):
    state = json.loads(STATE.read_text())
    if state.get('openai48_batches') or (state['next_pilot_run_start'], state['next_pilot_config_start']) != (plan['proposed_run_start'], plan['proposed_config_start']):
        raise PermissionError('Already reserved or registry moved')
    smoke = [{'slot': 'OAI-SMOKE-' + str(i + 1), 'tool': tool, 'task_id': 'B-02', 'repetition': 'smoke'}
             for i, tool in enumerate(('opencode-v1', 'opencode-v2', 'pi', 'codex'))]
    rows = []
    for i, slot in enumerate(smoke + plan['slots']):
        row = {**slot, 'run_id': f"R-{plan['proposed_run_start'] + i:04d}",
               'config_id': f"C-{plan['proposed_config_start'] + i:04d}", 'status': 'not_run'}
        if (native.RUNTIME / row['config_id']).exists() or row['config_id'] in state.get('retired_config_ids', []):
            raise ValueError('Runtime ID collision')
        for filename in ('runs.csv', 'runs-search-r2.csv', 'runs-benchmark48.csv'):
            path = ROOT / 'benchmark' / filename
            if path.exists():
                with path.open() as stream:
                    if any(r.get('run_id') == row['run_id'] or r.get('config_id') == row['config_id'] for r in csv.DictReader(stream)):
                        raise ValueError('Indexed ID collision')
        rows.append(row)
    state['next_pilot_run_start'] += 52
    state['next_pilot_config_start'] += 52
    state['openai48_batches'] = [{'artifact': str(artifact.relative_to(ROOT)), 'reserved': rows,
                                 'status': 'reserved_before_smoke', 'provider': BASE, 'model': MODEL}]
    temp = STATE.with_suffix('.json.openai48-tmp')
    with temp.open('x') as stream:
        json.dump(state, stream, ensure_ascii=False, indent=2)
        stream.write('\n'); stream.flush(); os.fsync(stream.fileno())
    os.replace(temp, STATE)
    return rows


def dispatch(artifact, rows, plan, *, paid=False, key=None, carry=CARRY, smoke=False):
    with context(paid=paid, carry=carry, smoke=smoke):
        result = batch.run_batch(artifact, rows, paid=paid, key=key,
            input_hashes=plan['input_sha256'], resources=plan['resource_identity'])
    result.update(cohort='openai-direct', provider=BASE, model=MODEL, scope=SCOPE,
        reasoning_effort='low', service_tier='default', rubric_revision='b01-evidence-r2',
        phase='native-smoke-not-scored' if smoke else ('benchmark48' if paid else 'offline-synthetic'),
        prior_known_usd=str(carry), remaining_known_guard_usd=str(Decimal('16') - carry),
        prior_unpriced_requests=4, measured_charge_usd=None)
    if smoke:
        for run in result['runs']:
            stdout = (artifact / run['slot'] / 'stdout.jsonl').read_text() if (artifact / run['slot'] / 'stdout.jsonl').exists() else ''
            run['native_smoke_checks'] = native.event_acceptance(run['tool'], stdout)
            run['native_smoke_pass'] = (all(run['native_smoke_checks'].values()) and run.get('validity') == 'valid'
                and run.get('execution', {}).get('exit_code') == 0 and bool(run['requests'])
                and all(q.get('http_status') == 200 and q.get('terminal_type') == 'response.completed'
                        and q.get('cost', {}).get('estimated_cost_usd') is not None for q in run['requests']))
        result['native_smoke_pass'] = len(result['runs']) == 4 and all(r['native_smoke_pass'] for r in result['runs'])
    native.write(artifact / 'result.json', result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--offline', action='store_true')
    parser.add_argument('--paid', action='store_true')
    parser.add_argument('--artifact-dir', type=Path, required=True)
    parser.add_argument('--plan', type=Path)
    parser.add_argument('--approval', type=Path)
    args = parser.parse_args()
    artifact = args.artifact_dir.resolve()
    if not artifact.is_relative_to(SUITE / 'artifacts') or not re.fullmatch(r'[A-Za-z0-9-]+', artifact.name) or args.offline == args.paid:
        parser.error('Choose offline/paid and a fresh safe suite artifact path')
    if args.offline:
        plan = make_plan()
        artifact.mkdir(parents=True, exist_ok=False)
        native.write(artifact / 'launch-plan.json', plan)
        # Run all16 combinations before any credential is read or ID is allocated.
        result = dispatch(artifact, [r for r in plan['slots'] if r['repetition'] == '1'], plan)
        native.write(artifact / 'offline-result.json', result)
        if len(result['runs']) != 16 or not result['all_slots_executed'] or any(r['status'] != 'success' for r in result['runs']):
            raise SystemExit(1)
    else:
        if not args.plan or not args.approval:
            parser.error('Bound plan and approval required')
        approval = json.loads(args.approval.read_text())
        validate(args.plan, approval)
        with (ROOT / 'research/.batch48-launch.lock').open('a') as lock:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            plan = validate(args.plan, approval)
            artifact.mkdir(parents=True, exist_ok=False)
            rows = reserve(plan, artifact)
            for name, value in [('plan', plan), ('approval', approval), ('reserved', rows)]:
                native.write(artifact / (name + '.json'), value)
            for name in plan['input_sha256']:
                dest = artifact / 'source' / name
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes((ROOT / name).read_bytes())
            from openai_direct_check import credential
            key = credential()
            smoke_dir = artifact / 'native-smoke'; smoke_dir.mkdir()
            smoke_result = dispatch(smoke_dir, rows[:4], plan, paid=True, key=key, smoke=True)
            if not smoke_result['native_smoke_pass']:
                native.write(artifact / 'result.json', {'status': 'native_smoke_gate_failed',
                    'benchmark_slots_run': 0, 'benchmark_not_run': 48, 'native_smoke': smoke_result})
                return
            # No extra upstream during handover; preserve real gap from final smoke response.
            import time
            time.sleep(30)
            bench_dir = artifact / 'benchmark'; bench_dir.mkdir()
            result = dispatch(bench_dir, rows[4:], plan, paid=True, key=key,
                carry=CARRY + Decimal(smoke_result['known_usage_estimate_usd']))
            native.write(artifact / 'result.json', {'status': 'completed' if result['all_slots_executed'] else 'stopped',
                'native_smoke': smoke_result, 'benchmark': result})


if __name__ == '__main__':
    main()
