"""Derive per-attempt token/time dispersion from the sealed OpenAI48 raw, no inference."""
import csv
import hashlib
import json
from pathlib import Path
import statistics

ROOT = Path(__file__).resolve().parents[1]


def main():
    out = ROOT / 'research/artifacts/OPENAI48-DISPERSION-20261111-01'
    out.mkdir(parents=True, exist_ok=False)
    rows = list(csv.DictReader((ROOT / 'benchmark/suite48/artifacts/OPENAI48-R3-SUMMARY-20261111-01/runs48.csv').open()))
    groups = {}
    hashes = {}
    for row in rows:
        p = ROOT / row['artifact'] / 'result.json'
        data = json.loads(p.read_text())
        hashes[str(p.relative_to(ROOT))] = hashlib.sha256(p.read_bytes()).hexdigest()
        tokens = {key: sum(request['cost']['usage'][key] for request in data['requests']) for key in ['input_tokens', 'output_tokens']}
        tokens.update(run_id=row['run_id'], duration_seconds=float(row['duration_seconds']))
        groups.setdefault(row['tool'], []).append(tokens)
    result = {}
    for tool, attempts in groups.items():
        assert len(attempts) == 12
        result[tool] = {'n': 12, 'attempts': attempts}
        for field in ['duration_seconds', 'input_tokens', 'output_tokens']:
            values = [a[field] for a in attempts]
            q1, _, q3 = statistics.quantiles(values, n=4, method='inclusive')
            result[tool][field] = {'median': statistics.median(values), 'q1': q1, 'q3': q3,
                                   'iqr': q3 - q1, 'min': min(values), 'max': max(values)}
    (out / 'summary.json').write_text(json.dumps({'status': 'pass', 'scope': '12attempts/CLI including failures; sum lifetime usage per request, not final turn alone',
        'quartiles': 'statistics.quantiles(n=4,method=inclusive)', 'groups': result, 'raw_sha256': hashes, 'real_provider_requests': 0}, indent=2) + '\n')
    text = '# Độ phân tán benchmark48 — derived, không inference mới\n\n12attempts/CLI, gồm2failure; token là tổng reported usage của mọi upstream request trong attempt. Input lifetime gồm cache; output gồm reasoning, không cộng lại. Duration gồm pacing/startup. Quartile inclusive (n nhỏ, không significanceclaim).\n\n'
    text += '| CLI | Duration median [Q1–Q3],s | Input median [Q1–Q3] | Output median [Q1–Q3] |\n| --- | ---: | ---: | ---: |\n'
    for tool in ['opencode-v1', 'opencode-v2', 'pi', 'codex']:
        cells = []
        for field in ['duration_seconds', 'input_tokens', 'output_tokens']:
            d = result[tool][field]
            cells.append(f"{d['median']:.2f} [{d['q1']:.2f}–{d['q3']:.2f}]")
        text += '| ' + tool + ' | ' + ' | '.join(cells) + ' |\n'
    text += '\n[JSON, all run IDs và raw hashes](summary.json); [báo cáo](../../../REPORT.md). Không đổi sealed benchmark hoặc loại failure.\n'
    (out / 'SUMMARY.md').write_text(text)
    print(text)


if __name__ == '__main__': main()
