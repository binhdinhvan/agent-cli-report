"""Preserve native reasoning fields around the sealed r1 normalizer; offline acceptance only."""
import argparse
import contextlib
import csv
from decimal import Decimal
import json
from pathlib import Path
import re
from unittest.mock import patch

import openai48_cache_r2 as cache

r1 = cache.r1
ROOT, SUITE = r1.ROOT, r1.SUITE
PROTOCOL = ROOT / 'benchmark/OPENAI_REASONING_FIX_R3.md'
LITE = 'x-openai-internal-codex-responses-lite'
GUARD_CARRY = Decimal('0.33970766')


def reasoning_fields(payload, headers):
    value = payload.get('reasoning')
    if value is not None and not isinstance(value, dict):
        raise ValueError('Native reasoning must be an object or absent/null')
    reasoning = {**(value or {}), 'effort': 'low'}
    lite = next((str(v).lower() for k, v in headers.items() if k.lower() == LITE), None)
    if lite == 'true' and reasoning.get('context') != 'all_turns':
        raise ValueError('Responses Lite requires native reasoning.context=all_turns; no protocol fallback')
    return reasoning


@contextlib.contextmanager
def context(*, paid=False, carry=GUARD_CARRY, smoke=False):
    """Reuse cache-r2 transport and guards unchanged; fix only outbound reasoning semantics."""
    with cache.context(paid=paid, carry=carry, smoke=smoke):
        normalize = r1.native.model_smoke.urllib.request.Request
        handler = r1.native.handler
        active = []

        def tracked(key, nonce, ledger, *args, **kwargs):
            if not active or active[-1] is not ledger:
                active.append(ledger)
            return handler(key, nonce, ledger, *args, **kwargs)

        def request(url, data=None, **options):
            payload = json.loads(data)
            preserved = reasoning_fields(payload, options.get('headers') or {})
            req = normalize(url, data=data, **options)
            effective = json.loads(req.data)
            effective['reasoning'] = preserved
            req.data = json.dumps(effective).encode()
            if active and active[-1]:
                item = active[-1][-1]
                item['effective_settings']['reasoning'] = preserved
                item['reasoning_normalizer_revision'] = 'preserve-native-fields-r3'
            return req

        with patch.object(r1.native, 'handler', tracked), \
                patch.object(r1.native.model_smoke.urllib.request, 'Request', request):
            yield


class ReasoningSyntheticProvider(cache.CacheWriteSyntheticProvider):
    """Reject a lost native Codex context like the observed provider400; no network."""
    def open(self, request, timeout):
        payload = json.loads(request.data)
        headers = dict(request.header_items())
        expected = reasoning_fields(payload, headers)
        if payload.get('reasoning') != expected:
            raise ValueError('Effective effort not low')
        return super().open(request, timeout)


def inputs():
    files = cache.inputs()
    for p in [Path(__file__), ROOT / 'benchmark/test_openai_reasoning_r3.py', PROTOCOL,
              ROOT / 'benchmark/openai48_r2.py', ROOT / 'benchmark/test_openai48_r2.py']:
        files[str(p.relative_to(ROOT))] = r1.batch.digest(p)
    review_path = ROOT / 'research/artifacts/OPENAI48-R2-REVIEW-20261110-01/validation.json'
    review = json.loads(review_path.read_text())
    for name, expected in review['raw_artifact_sha256'].items():
        if r1.batch.digest(ROOT / review['artifact'] / name) != expected:
            raise ValueError('Prior r2 raw drift: ' + name)
    files[str(review_path.relative_to(ROOT))] = r1.batch.digest(review_path)
    return files


def offline(artifact):
    with r1.native.ORDER.open() as stream:
        rows = [r for r in r1.native.slot_mapping(csv.DictReader(stream)) if r['repetition'] == '1']
    plan = {'revision': 'openai-reasoning-r3-offline', 'scope': 'offline-native16-preserve-reasoning',
        'generation_authorized': False, 'input_sha256': inputs(), 'resource_identity': r1.batch.resource_identity(),
        'historical_guard_carry_usd': str(GUARD_CARRY), 'historical_unpriced_requests': 6,
        'budget_estimate_usd': '16', 'remaining_guard_usd': str(Decimal('16') - GUARD_CARRY)}
    artifact.mkdir(parents=True, exist_ok=False)
    r1.native.write(artifact / 'plan.json', plan)
    for name in plan['input_sha256']:
        dest = artifact / 'source' / name; dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes((ROOT / name).read_bytes())
    with context(), patch.object(r1.native, 'SyntheticProvider', ReasoningSyntheticProvider):
        result = r1.batch.run_batch(artifact, rows, input_hashes=plan['input_sha256'], resources=plan['resource_identity'])
    result.update(revision=plan['revision'], scope=plan['scope'], generation_authorized=False,
                  cost_scope='synthetic guard estimates only, not spend')
    r1.native.write(artifact / 'result.json', result)
    if len(result['runs']) != 16 or not result['all_slots_executed'] or any(r['status'] != 'success' for r in result['runs']):
        raise ValueError('Reasoning r3 native offline did not pass16/16')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--offline', action='store_true', required=True)
    parser.add_argument('--artifact-dir', type=Path, required=True)
    args = parser.parse_args()
    artifact = args.artifact_dir.resolve()
    if not artifact.is_relative_to(SUITE / 'artifacts') or not re.fullmatch(r'[A-Za-z0-9-]+', artifact.name):
        parser.error('Fresh safe suite artifact path required')
    offline(artifact)


if __name__ == '__main__':
    main()
