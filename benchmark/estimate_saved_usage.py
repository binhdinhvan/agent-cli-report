"""Ước tính riêng từ provider ledger đã lưu; không API, key hoặc sửa raw result."""
import argparse
import datetime
from decimal import Decimal
import hashlib
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / "demos"))
from estimate_provider_cost import estimate, require_pricing


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--result", type=pathlib.Path, required=True)
    parser.add_argument("--artifact-dir", type=pathlib.Path, required=True)
    args = parser.parse_args()
    source, target = args.result.resolve(), args.artifact_dir.resolve()
    if not all(p.is_relative_to(ROOT / "benchmark/artifacts") for p in [source, target]):
        parser.error("Only benchmark artifact paths accepted")
    data = json.loads(source.read_text())
    model, provider = data.get("model"), data.get("provider")
    pricing = require_pricing(model, provider)
    requests = data.get("provider_requests", [])
    if not requests:
        parser.error("No provider request ledger found")
    entries = []
    for request in requests:
        if request.get("model") != model or request.get("response_model") not in [None, model]:
            raise ValueError("Mixed model ledger; do not apply one model's rates")
        usage = request.get("cost", {}).get("usage")
        entries.append({"request_index": request["request_index"], "http_status": request.get("http_status"), **estimate(usage, pricing)})
    complete = all(e["estimated_cost_usd"] is not None for e in entries)
    totals = {}
    if complete:
        totals = {"input_tokens": sum(e["usage"]["input_tokens"] for e in entries),
                  "cached_input_tokens": sum(e["usage"]["input_tokens_details"]["cached_tokens"] for e in entries),
                  "uncached_input_tokens": sum(e["uncached_input_tokens"] for e in entries),
                  "output_tokens": sum(e["usage"]["output_tokens"] for e in entries)}
    pricing_path = ROOT / "research/provider-pricing.json"
    result = {"created_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
              "scope": "Offline estimate from existing sol diagnostic; no extra provider requests or key reads",
              "model": model, "provider": provider, "source_result": str(source.relative_to(ROOT)), "source_sha256": sha(source),
              "pricing_manifest": str(pricing_path.relative_to(ROOT)), "pricing_sha256": sha(pricing_path), "pricing": pricing,
              "estimator_sha256": sha(pathlib.Path(__file__)), "arithmetic_helper_sha256": sha(ROOT / "demos/estimate_provider_cost.py"),
              "entries": entries, "all_entries_estimable": complete, "usage_totals": totals,
              "estimated_total_usd": format(sum(Decimal(e["estimated_cost_usd"]) for e in entries), "f") if complete else None,
              "measured_charge_usd": None, "limitations": [pricing["verification_status"], pricing["calculation_assumption"], "No account balance, surcharges or billing token accounting independently verified"]}
    target.mkdir(parents=True, exist_ok=False)
    (target / "estimate.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"entries": len(entries), "usage_totals": totals, "estimated_total_usd": result["estimated_total_usd"],
                      "measured_charge_usd": None, "artifact": str(target.relative_to(ROOT) / "estimate.json")}, indent=2))


if __name__ == "__main__":
    main()
