"""Explicit experiment timing revisions; no per-CLI special timeout."""

POLICIES = ("legacy-300", "paced-900")


def timing_policy(name):
    if name not in POLICIES:
        raise ValueError("Unknown timing policy")
    return {"id": name, "wall_seconds": 900 if name == "paced-900" else 300,
            "minimum_request_window_seconds": 60 if name == "paced-900" else 0,
            "request_limit": 8, "output_limit": 2048, "pacing_counts_in_wall_time": True}


def validate_history_timing(source, target, explicit, protocol_explicit):
    if source == target:
        if explicit:
            raise ValueError("Timing recheck needs different revisions")
        return
    if not (explicit and protocol_explicit and source == "legacy-300" and target == "paced-900"):
        raise ValueError("Cross-timing retry/continuation needs explicit recheck and a separate protocol/group")
