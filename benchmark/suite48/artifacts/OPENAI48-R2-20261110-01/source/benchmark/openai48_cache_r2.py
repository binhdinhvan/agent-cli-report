"""Cache-cost fix adapter and offline native acceptance only. No paid CLI or credential IO."""
import argparse
import contextlib
import csv
from decimal import Decimal
import json
from pathlib import Path
import re
from unittest.mock import patch

import openai48 as r1
from openai_cache_cost_r2 import estimate

ROOT, SUITE = r1.ROOT, r1.SUITE
PROTOCOL = ROOT / 'benchmark/OPENAI_CACHE_FIX_R2.md'
REVISION = 'openai48-cache-fix-r2'
CARRY = Decimal('0.28655616')
UNPRICED_CARRY = 5
_context = r1.context
_pricing = r1.pricing
_synthetic = r1.native.SyntheticProvider


def pricing():
    rates = _pricing()
    profile = json.loads(r1.PROFILE.read_text())['pricing_usd_per_million']
    if (profile['cache_write_30m'], profile['cache_write_12h']) != ('2.50', '5'):
        raise ValueError('Cache tariffs changed; review required')
    return {**rates, 'cache_write_30m': profile['cache_write_30m'], 'cache_write_12h': profile['cache_write_12h']}


@contextlib.contextmanager
def context(*, paid=False, carry=CARRY, smoke=False):
    # Reuses the exact transport/guard implementation; only the estimator changes.
    # No paid entrypoint is provided here; future launch still needs a fresh plan/approval.
    with patch.object(r1, 'pricing', pricing), patch.object(r1, 'estimate', estimate), \
            _context(paid=paid, carry=carry, smoke=smoke):
        yield


class CacheWriteSyntheticProvider(_synthetic):
    """Memory-only responses with positive writes and no lifetime breakdown on every turn."""
    def open(self, request, timeout):
        old = super().open(request, timeout)
        lines = []
        for line in old:
            if line.startswith(b'data:'):
                event = json.loads(line[5:])
                if event.get('type') == 'response.completed':
                    event['response']['usage'] = {'input_tokens': 3112, 'output_tokens': 32, 'total_tokens': 3144,
                        'input_tokens_details': {'cached_tokens': 0, 'cache_write_tokens': 3109},
                        'output_tokens_details': {'reasoning_tokens': 0}}
                    line = b'data: ' + json.dumps(event).encode() + b'\n'
            lines.append(line)
        return r1.native.Response(b''.join(lines))


def inputs():
    files = r1.inputs()
    for path in [Path(__file__), PROTOCOL, ROOT / 'benchmark/openai_cache_cost_r2.py',
                 ROOT / 'benchmark/test_openai_cache_r2.py']:
        files[str(path.relative_to(ROOT))] = r1.batch.digest(path)
    audit_path = ROOT / 'research/artifacts/OPENAI48-REVIEW-20261110-01/validation.json'
    audit = json.loads(audit_path.read_text())
    for name, expected in audit['raw_artifact_sha256'].items():
        if r1.batch.digest(ROOT / audit['artifact'] / name) != expected:
            raise ValueError('Old OpenAI raw changed: ' + name)
    files[str(audit_path.relative_to(ROOT))] = r1.batch.digest(audit_path)
    return files


def offline(artifact):
    with r1.native.ORDER.open() as stream:
        rows = [r for r in r1.native.slot_mapping(csv.DictReader(stream)) if r['repetition'] == '1']
    plan = {'revision': REVISION, 'generation_authorized': False, 'scope': 'offline-only-16-native-cachewrite-synthetic',
        'input_sha256': inputs(), 'resource_identity': r1.batch.resource_identity(),
        'prior_known_usd': str(CARRY), 'prior_unpriced_requests': UNPRICED_CARRY,
        'budget_estimate_usd': '16', 'remaining_known_guard_usd': str(Decimal('16') - CARRY)}
    artifact.mkdir(parents=True, exist_ok=False)
    r1.native.write(artifact / 'plan.json', plan)
    for name in plan['input_sha256']:
        dest = artifact / 'source' / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes((ROOT / name).read_bytes())
    with context(), patch.object(r1.native, 'SyntheticProvider', CacheWriteSyntheticProvider):
        result = r1.batch.run_batch(artifact, rows, input_hashes=plan['input_sha256'], resources=plan['resource_identity'])
    result.update(revision=REVISION, scope=plan['scope'], generation_authorized=False, cohort='OpenAI-direct-r2-offline-only',
        pricing_semantics='synthetic guard costs, not real spend', prior_known_usd=str(CARRY), prior_unpriced_requests=UNPRICED_CARRY)
    r1.native.write(artifact / 'result.json', result)
    if len(result['runs']) != 16 or not result['all_slots_executed'] or any(r['status'] != 'success' for r in result['runs']):
        raise ValueError('Native cache-write acceptance did not pass16/16')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--offline', action='store_true', required=True)
    parser.add_argument('--artifact-dir', type=Path, required=True)
    args = parser.parse_args()
    artifact = args.artifact_dir.resolve()
    if not artifact.is_relative_to(SUITE / 'artifacts') or not re.fullmatch(r'[A-Za-z0-9-]+', artifact.name):
        parser.error('Fresh suite artifact directory required')
    offline(artifact)


if __name__ == '__main__':
    main()
