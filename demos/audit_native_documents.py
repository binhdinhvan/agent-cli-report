"""Offline structural audit of native-demo report updates and pinned source evidence."""
import csv
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def main():
    rows = list(csv.DictReader((ROOT / 'research/evidence.csv').open()))
    assert len(rows) == 134 and len({r['id'] for r in rows}) == 134
    assert all(None not in r and all(v is not None for v in r.values()) for r in rows)
    for row in rows[-10:]:
        repo = ROOT.parent / ('opencode-v1' if row['tool'] == 'OpenCode v1' else 'opencode-v2')
        text = subprocess.check_output(['git', 'show', row['commit'] + ':' + row['file']], cwd=repo, text=True)
        start, end = int(row['line_start']), int(row['line_end'])
        assert 1 <= start <= end <= len(text.splitlines()), row['id']
        assert '/blob/' + row['commit'] + '/' + row['file'] + f'#L{start}-L{end}' in row['permalink']
        assert (ROOT / row['runtime_artifact']).is_file()
    documents = ['REPORT.md', 'README.md', 'PLAN.md', 'demos/README.md',
                 'demos/NATIVE_RUNTIME_RESULTS.md', 'demos/OFFLINE_DEMO_PLAN.md']
    checked = 0
    for name in documents:
        path = ROOT / name
        for target in re.findall(r'\]\(([^)]+)\)', path.read_text()):
            if target.startswith(('https://', 'http://', '#')): continue
            local = target.split('#')[0]
            assert (path.parent / local).exists(), (name, target)
            checked += 1
    state = json.loads((ROOT / 'research/experiment-state.json').read_text())
    assert state['additional_native_demos']['status'] == 'completed_with_explicit_recovery_blockers'
    assert (state['next_pilot_run_start'], state['next_pilot_config_start']) == (378, 479)
    audit = json.loads((ROOT / 'research/artifacts/NATIVE-DEMOS-REVIEW-20261111-01/validation.json').read_text())
    for name, expected in audit['raw_artifact_sha256'].items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == expected, name
    result = {'status': 'pass', 'evidence_ids': 134, 'new_pinned_source_ranges_checked': 10,
              'local_links_checked': checked, 'native_raw_from_first_audit_unchanged': True,
              'registry': ['R-0378', 'C-0479'], 'real_provider_requests': 0,
              'document_sha256': {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in documents}}
    out = ROOT / 'research/artifacts/NATIVE-DEMOS-DOCUMENTS-20261111-01'
    out.mkdir(parents=True, exist_ok=False)
    (out / 'validation.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__': main()
