"""Export48row table/CSV from audited raw, offline and without credentials."""
import argparse
import csv
from decimal import Decimal
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--review', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    review = json.loads(args.review.read_text())
    assert review['status'] == 'pass' and review['valid_attempts'] == 48
    artifact = ROOT / review['artifact']
    bench = json.loads((artifact / 'benchmark/result.json').read_text())
    rows = []
    for run in bench['runs']:
        cost = sum(Decimal(q['cost']['estimated_cost_usd']) for q in run['requests'])
        rows.append({'run_id': run['run_id'], 'slot': run['slot'], 'repetition': run['repetition'], 'task_id': run['task_id'],
            'tool': run['tool'], 'status': run['status'], 'validity': run['validity'],
            'snapshot_grader_pass': run['grading']['pass'], 'duration_seconds': f"{run['execution']['duration_ms']/1000:.3f}",
            'provider_requests': len(run['requests']), 'guard_estimate_usd': str(cost),
            'artifact': str((artifact / 'benchmark' / run['slot']).relative_to(ROOT))})
    args.output_dir.mkdir(parents=True, exist_ok=False)
    with (args.output_dir / 'runs48.csv').open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    lines = ['# Toàn bộ48lượt OpenAI r3', '', 'Bảng derived từ raw đã audit; không ghi đè index hoặc kết quả gốc.', '',
             '| Run | Slot | Lần | Task | CLI | Status | Giây | Requests | Guard USD | Snapshot |',
             '|---|---|---:|---|---|---|---:|---:|---:|---|']
    for r in rows:
        lines.append('| ' + ' | '.join(str(r[k]) for k in ('run_id','slot','repetition','task_id','tool','status',
            'duration_seconds','provider_requests','guard_estimate_usd','snapshot_grader_pass')) + ' |')
    (args.output_dir / 'RUNS48.md').write_text('\n'.join(lines) + '\n')
    print('Exported48derivedrows; raw/index untouched;0API/keyread')


if __name__ == '__main__':
    main()
