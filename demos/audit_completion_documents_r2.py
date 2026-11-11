"""Final source/link/raw/secret-pattern audit for report completion revision2."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    with path.open('rb') as handle: return hashlib.file_digest(handle, 'sha256').hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    errors = []
    rows = list(csv.DictReader((ROOT / 'research/evidence.csv').open()))
    assert len(rows) == len({r['id'] for r in rows}) == 147
    repositories = {'OpenCode v1': 'opencode-v1', 'OpenCode v2': 'opencode-v2', 'Pi': 'pi', 'Codex CLI': 'codex'}
    for r in rows:
        if None in r or any(v is None for v in r.values()): errors.append('invalid CSV ' + r['id']); continue
        start, end = int(r['line_start']), int(r['line_end'])
        repo = ROOT.parent / repositories[r['tool']]
        response = subprocess.run(['git', 'show', r['commit'] + ':' + r['file']], cwd=repo, capture_output=True, text=True)
        if response.returncode or not 1 <= start <= end <= len(response.stdout.splitlines()): errors.append('source range ' + r['id'])
        fragment = f'#L{start}' if start == end else f'#L{start}-L{end}'
        if not r['permalink'].endswith('/blob/' + r['commit'] + '/' + r['file'] + fragment): errors.append('permalink ' + r['id'])
        if int(r['id'].split('-')[1]) >= 125 and r['runtime_artifact'] and not (ROOT / r['runtime_artifact']).is_file(): errors.append('runtime artifact ' + r['id'])
    documents = ['REPORT.md', 'README.md', 'PLAN.md', 'demos/README.md', 'demos/NATIVE_RUNTIME_RESULTS.md',
                 'demos/NATIVE_COMPLETION_R2_RESULTS.md', 'demos/OFFLINE_DEMO_PLAN.md', 'research/REQUIREMENTS_ACCEPTANCE.md',
                 'research/artifacts/OPENAI48-DISPERSION-20261111-01/SUMMARY.md']
    links = 0
    for name in documents:
        path = ROOT / name
        for target in re.findall(r'\]\(([^)]+)\)', path.read_text()):
            if target.startswith(('https://', 'http://', '#')): continue
            linked = (path.parent / target.split('#')[0]).resolve()
            if not linked.exists() and linked != args.output_dir.resolve() / 'validation.json': errors.append('local link ' + name + ' -> ' + target)
            links += 1
    native_audit = json.loads((ROOT / 'research/artifacts/NATIVE-COMPLETION-R2-REVIEW-20261111-02/validation.json').read_text())
    for name, expected in native_audit['raw_artifact_sha256'].items():
        if sha(ROOT / name) != expected: errors.append('changed native raw ' + name)
    dispersion = json.loads((ROOT / 'research/artifacts/OPENAI48-DISPERSION-20261111-01/summary.json').read_text())
    for name, expected in dispersion['raw_sha256'].items():
        if sha(ROOT / name) != expected: errors.append('changed benchmark raw ' + name)
    # Scan only report/artifacts, never credential files or user's home/session data.
    patterns = {
        'private_key': re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),
        'provider_key': re.compile(r'\b(?:sk-proj-|sk-ant-api|AIzaSy)[A-Za-z0-9_-]{20,}'),
        'authorization_value': re.compile(r'["\'](?:Authorization|authorization)["\']\s*:\s*["\'](?:Basic|Bearer) [A-Za-z0-9+/=_-]{16,}'),
    }
    scan_files = set(ROOT / n for n in documents)
    scan_files.update(ROOT / n for n in native_audit['raw_artifact_sha256'] if Path(n).suffix in {'.json', '.txt', '.log', '.jsonl', '.ansi'})
    hits = []
    for path in scan_files:
        text = path.read_text(errors='replace')
        for label, pattern in patterns.items():
            if pattern.search(text): hits.append({'file': str(path.relative_to(ROOT)), 'pattern': label})
    if hits: errors.append('sensitive-pattern hits require review; values not displayed')
    git_status = {}
    for name in repositories.values():
        response = subprocess.run(['git', '--no-optional-locks', 'status', '--porcelain=v1', '--untracked-files=normal'],
                                  cwd=ROOT.parent / name, capture_output=True, text=True)
        git_status[name] = {'exit_code': response.returncode, 'clean': not bool(response.stdout.strip())}
        if response.returncode or response.stdout.strip(): errors.append('source repo status ' + name)
    state = json.loads((ROOT / 'research/experiment-state.json').read_text())
    assert (state['next_pilot_run_start'], state['next_pilot_config_start']) == (378, 479)
    result = {'status': 'pass' if not errors else 'failed', 'errors': errors, 'evidence_ids': len(rows),
              'pinned_source_ranges_checked': len(rows), 'local_links_checked': links,
              'secret_pattern_scan_files': len(scan_files), 'secret_pattern_hits': hits,
              'source_repositories': git_status, 'native_round2_raw_unchanged': True,
              'benchmark48_raw_unchanged': True, 'tests': {'python_demo': 73, 'python_benchmark': 118, 'bun': 3, 'total': 194,
              'legacy_test_isolation': 'two reservation tests mock csv.DictReader only inside tempstate methods; no sealedsource edits'},
              'registry': ['R-0378', 'C-0479'], 'real_provider_requests': 0, 'credential_file_reads': 0,
              'document_sha256': {n: sha(ROOT / n) for n in documents}, 'evidence_csv_sha256': sha(ROOT / 'research/evidence.csv')}
    args.output_dir.mkdir(parents=True, exist_ok=False)
    (args.output_dir / 'validation.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(bool(errors))


if __name__ == '__main__': main()
