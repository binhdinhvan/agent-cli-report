"""Ước tính riêng từ usage đã lưu và giá user-reported; không gọi API hoặc đọc key."""

import argparse
import datetime
from decimal import Decimal, InvalidOperation
import hashlib
import json
import pathlib


ROOT = pathlib.Path(__file__).resolve().parents[1]


def pricing_ready(pricing):
    try:
        unit = Decimal(str(pricing["unit_tokens"]))
        rates = [Decimal(str(pricing[k])) for k in ["input_uncached", "input_cache_read", "output"]]
        return unit.is_finite() and unit > 0 and all(r.is_finite() and r >= 0 for r in rates)
    except (KeyError, TypeError, ValueError, InvalidOperation):
        return False


def require_pricing(model, base_url):
    pricing = json.loads((ROOT / "research/provider-pricing.json").read_text())
    if pricing.get("model") != model or pricing.get("provider_base_url") != base_url or not pricing_ready(pricing):
        raise ValueError("Pricing pending/mismatched: no paid request allowed until rates for this model/provider are supplied")
    return pricing


def estimate(usage, pricing):
    if not pricing_ready(pricing):
        return {"usage": usage, "estimated_cost_usd": None, "reason": "Pricing missing/invalid; not replaced with zero or another model's rates"}
    if not isinstance(usage, dict):
        return {"usage": usage, "estimated_cost_usd": None, "reason": "Usage is not an object"}
    details = usage.get("input_tokens_details")
    if not isinstance(details, dict):
        details = {}
    required = {"input": usage.get("input_tokens"), "output": usage.get("output_tokens"),
                "cached_input": details.get("cached_tokens")}
    if not all(type(value) is int and value >= 0 for value in required.values()):
        return {"usage": usage, "estimated_cost_usd": None, "reason": "Missing/non-integer input/output/cached usage; not replaced with zero"}
    if required["cached_input"] > required["input"]:
        return {"usage": usage, "estimated_cost_usd": None, "reason": "cached input exceeds input; semantics need review"}
    uncached = required["input"] - required["cached_input"]
    unit = Decimal(pricing["unit_tokens"])
    components = {
        "uncached_input_usd": Decimal(uncached) * Decimal(pricing["input_uncached"]) / unit,
        "cached_input_usd": Decimal(required["cached_input"]) * Decimal(pricing["input_cache_read"]) / unit,
        "output_usd": Decimal(required["output"]) * Decimal(pricing["output"]) / unit,
    }
    return {"usage": usage, "uncached_input_tokens": uncached,
            "components": {key: format(value, "f") for key, value in components.items()},
            "estimated_cost_usd": format(sum(components.values()), "f"),
            "estimate_status": "user-reported rates applied to provider-reported usage; not invoice-confirmed"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--probe", type=pathlib.Path, action="append", required=True)
    parser.add_argument("--artifact-dir", type=pathlib.Path, required=True)
    args = parser.parse_args()
    artifact = args.artifact_dir.resolve()
    if not artifact.is_relative_to(ROOT / "demos/artifacts"):
        parser.error("Artifact must be under demos/artifacts")
    artifact.mkdir(parents=True, exist_ok=False)
    pricing_path = ROOT / "research/provider-pricing.json"
    pricing = json.loads(pricing_path.read_text())
    entries = []
    for path in args.probe:
        path = path.resolve()
        if not path.is_relative_to(ROOT / "demos/artifacts"):
            parser.error("Only reviewed probe artifacts under demos/artifacts are accepted")
        data = json.loads(path.read_text())
        if data.get("base_url") != pricing["provider_base_url"] or data.get("model") != pricing["model"]:
            raise ValueError("Provider/model does not match pricing manifest")
        responses = [request.get("response", {}) for request in data.get("requests", []) if request.get("method") == "POST"]
        if data.get("terminal_response") is not None:
            responses.append(data["terminal_response"])
        for index, response in enumerate(responses, 1):
            entries.append({"probe": str(path.relative_to(ROOT)), "probe_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                            "generation_index": index, **estimate(response.get("usage") or {}, pricing)})
    complete = bool(entries) and all(entry["estimated_cost_usd"] is not None for entry in entries)
    result = {
        "created_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "pricing_manifest": str(pricing_path.relative_to(ROOT)),
        "pricing_sha256": hashlib.sha256(pricing_path.read_bytes()).hexdigest(),
        "script_sha256": hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),
        "entries": entries, "all_entries_estimable": complete,
        "estimated_total_usd": format(sum(Decimal(entry["estimated_cost_usd"]) for entry in entries), "f") if complete else None,
        "measured_charge_usd": None,
        "limitations": [pricing["verification_status"], pricing["calculation_assumption"],
                        "No account balance, additional fees, invoice or provider-internal token accounting verified"],
    }
    (artifact / "estimate.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"entries": len(entries), "estimated_total_usd": result["estimated_total_usd"],
                      "measured_charge_usd": None, "artifact": str(artifact.relative_to(ROOT) / "estimate.json")}, indent=2))


if __name__ == "__main__":
    main()
