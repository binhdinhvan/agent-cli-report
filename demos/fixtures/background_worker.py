"""Fixture local bounded; không phải implementation/background acceptance của tool."""

import argparse
import json
import signal
import time


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=["success", "error"], default="success")
    parser.add_argument("--steps", type=int, default=3)
    args = parser.parse_args()
    if not 1 <= args.steps <= 30:
        parser.error("steps must be between 1 and 30")
    started = time.monotonic()
    cancelled = False
    seq = 0

    def cancel(_signum, _frame):
        nonlocal cancelled
        cancelled = True

    def emit(event, **values):
        nonlocal seq
        print(json.dumps({"fixture": "background-worker-r1", "seq": seq,
                          "event": event, "elapsed_ms": int((time.monotonic() - started) * 1000),
                          **values}), flush=True)
        seq += 1

    signal.signal(signal.SIGTERM, cancel)
    emit("ready")
    for step in range(args.steps):
        time.sleep(0.1)
        if cancelled:
            emit("cancelled")
            return 143
        emit("progress", step=step + 1)
    emit("completed" if args.mode == "success" else "error", marker="fixture-r1")
    return 0 if args.mode == "success" else 7


if __name__ == "__main__":
    raise SystemExit(main())
