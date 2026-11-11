"""Helpers for half-open integer intervals."""


def merge_intervals(intervals):
    """Return sorted, merged half-open intervals without changing the input.

    Each interval must contain two integers with start < end; otherwise raise
    ValueError. Intervals that only touch remain separate.
    """
    validated = []
    for interval in intervals:
        try:
            start, end = interval
        except (TypeError, ValueError) as exc:
            raise ValueError("each interval must be a pair of integers") from exc
        if not isinstance(start, int) or not isinstance(end, int) or start >= end:
            raise ValueError("each interval must contain integers with start < end")
        validated.append((start, end))

    validated.sort()
    merged = []
    for start, end in validated:
        if merged and start < merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))
    return merged
