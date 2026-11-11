"""Audit native completion round2 without launching native binaries or providers."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import sqlite3
import struct

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / 'demos/artifacts'


def sha(path):
    with path.open('rb') as handle: return hashlib.file_digest(handle, 'sha256').hexdigest()


def load(name, file='client-result.json'): return json.loads((ART / name / file).read_text())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    accepted = {}
    for name, file in [
        ('NATIVE-BG-SERVICE-RECOVERY-20261111-04', 'client-result.json'),
        ('NATIVE-SUBAGENT-RECOVERY-20261111-01', 'client-result.json'),
        ('NATIVE-SUBAGENT-SIDEEFFECT-RECOVERY-20261111-01', 'client-result.json'),
        ('NATIVE-V1-PERMISSION-API-20261111-01', 'v1-result.json'),
        ('NATIVE-V1-SUBAGENT-20261111-03', 'v1-result.json'),
        ('NATIVE-CLIENT-FAILURES-20261111-01', 'client-result.json'),
        ('NATIVE-SDK-FAILURES-20261111-01', 'sdk-result.json'),
        ('NATIVE-UNMATCHED-PERMISSION-20261111-02', 'client-result.json'),
    ]:
        result = load(name, file)
        assert result['status'] == 'pass' and all(result['checks'].values()), name
        accepted[name] = result['checks']
    v1 = load('NATIVE-V1-SUBAGENT-20261111-03', 'v1-result.json')
    children = [e['properties']['info'] for e in v1['events'] if e['type'] == 'session.created' and e['properties']['info'].get('parentID') == v1['sessionID']]
    assert len(children) == 1
    ui_name = 'NATIVE-SHARED-UI-20261111-05'
    ui = load(ui_name, 'ui-result.json')
    assert all(ui['checks'].values()) and ui['checks']['all_clients_use_original_service_pid']
    session_id = ui['session']['data']['id']
    assert session_id in json.loads(ui['web_document']['result']['value'])['url']
    assert ui['server_info']['pid'] == ui['service_after_all_clients']['pid']
    assert ui['tui']['session_title_observed'] and ui['tui']['process_stopped']
    for name in ['desktop.png', 'web.png']:
        raw = (ART / ui_name / name).read_bytes()
        assert raw.startswith(b'\x89PNG\r\n\x1a\n') and struct.unpack('>II', raw[16:24]) == (1280, 800)
    accepted[ui_name] = ui['checks']
    migrated = load('NATIVE-V1CONFIG-ON-V2-20261111-01', 'summary.json')
    assert len(migrated['cases']) == 5
    for case in migrated['cases']:
        assert case['case']['legacy_v1_config'] and case['isolation_pass'] and case['supervisor_pid_absent']
        assert 'permission' in case['config'] and 'permissions' not in case['config']
        assert case['shell_witness_created'] == (case['case']['permission'] in ('allow', 'overlap-allow'))
    budget_name = 'NATIVE-RESUME-BUDGET-20261111-01'
    budget = load(budget_name)
    budget_review = json.loads((ROOT / 'research/artifacts/NATIVE-RESUME-BUDGET-REVIEW-20261111-01/validation.json').read_text())
    assert budget_review['status'] == 'pass_after_independent_raw_review'
    assert sha(ART / budget_name / 'client-result.json') == budget_review['raw_result_sha256']
    assert len(budget['budget_crashes']) == len(budget['requests']) == 11
    assert budget['budget_context'][-1]['outcome'] == 'failed'
    spec = load(budget_name, 'manifest.json')['spec']
    db = Path(spec['runtime_root']) / 'xdg-data/opencode/smoke.db'
    assert db.is_relative_to(Path('/tmp/opencode/agent-cli-report/smoke')) and db.parent.parent.parent.name.startswith('BP48-CL-')
    connection = sqlite3.connect('file:' + str(db) + '?mode=ro', uri=True)
    row = connection.execute('select time_suspended,resume_attempts,idle_outcome from session_v2 where id=?', (budget['sessionID'],)).fetchone()
    connection.close()
    assert row == (None, 0, 'failed')
    paths = set(accepted) | {budget_name, 'NATIVE-V1CONFIG-ON-V2-20261111-01'}
    hashes = {}
    for name in paths:
        artifact = ART / name
        manifest = artifact / 'manifest.json'
        if manifest.exists():
            m = json.loads(manifest.read_text())
            assert m['provider_requests'] == m['credential_reads'] == 0
            assert m['supervisor_pid_absent'] and not m['execution']['timed_out']
            harness = next(p for p in (artifact / 'source').iterdir() if p.name.endswith('_inside.ts'))
            assert sha(harness) == m['harness_sha256']
        for path in artifact.rglob('*'):
            if path.is_file(): hashes[str(path.relative_to(ROOT))] = sha(path)
    baseline = json.loads((ROOT / 'research/artifacts/OPENAI48-R3-FINAL-20261111-01/validation.json').read_text())
    assert all(sha(ROOT / baseline['artifact'] / p) == h for p, h in baseline['raw_artifact_sha256'].items())
    first = json.loads((ROOT / 'research/artifacts/NATIVE-DEMOS-REVIEW-20261111-01/validation.json').read_text())
    assert all(sha(ROOT / p) == h for p, h in first['raw_artifact_sha256'].items())
    state = json.loads((ROOT / 'research/experiment-state.json').read_text())
    assert (state['next_pilot_run_start'], state['next_pilot_config_start']) == (378, 479)
    attempts = []
    prefixes = ('NATIVE-BG-SERVICE-', 'NATIVE-SUBAGENT-RECOVERY-', 'NATIVE-V1-', 'NATIVE-CLIENT-FAILURES-', 'NATIVE-SDK-FAILURES-', 'NATIVE-SHARED-UI-', 'NATIVE-UNMATCHED-', 'NATIVE-RESUME-BUDGET-')
    for artifact in sorted(ART.iterdir()):
        if not artifact.is_dir() or not artifact.name.startswith(prefixes): continue
        attempts.append({'artifact': artifact.name, 'accepted': artifact.name in paths})
    result = {'status': 'pass', 'accepted_native_checks': accepted, 'legacy_v1_permission_config_on_v2_cases': 5,
              'v1_subagent_lineage_verified': True, 'resume_budget_review': str((ROOT / 'research/artifacts/NATIVE-RESUME-BUDGET-REVIEW-20261111-01/validation.json').relative_to(ROOT)),
              'budget_claim_released_and_counter_reset': True, 'native_screenshots': ['desktop.png', 'web.png'],
              'shared_ui_limits': 'Web app rendered by native Electron Chromium navigating to service URL; desktop headless; TUI raw PTY, not an emulator screenshot; no live-user display or service accessed',
              'raw_artifact_sha256': hashes, 'attempts_retained': attempts, 'benchmark48_and_round1_raw_unchanged': True,
              'registry': ['R-0378', 'C-0479'], 'real_provider_requests': 0, 'credential_file_reads': 0}
    args.output_dir.mkdir(parents=True, exist_ok=False)
    (args.output_dir / 'validation.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'raw_artifact_sha256'}, ensure_ascii=False, indent=2))


if __name__ == '__main__': main()
