"""Helpers for half-open integer intervals."""


def merge_intervals(intervals):
    """Merge overlapping half-open integer intervals without changing input.

    Raise ValueError if an interval is not a pair of integers with start < end.
    """
    validated = []
    for interval in intervals:
        try:
            start, end = interval
        except (TypeError, ValueError) as exc:
            raise ValueError("Each interval must be a pair of integers") from exc
        if not isinstance(start, int) or not isinstance(end, int) or start >= end:
            raise ValueError("Each interval must contain integers with start < end")
        validated.append((start, end))

    validated.sort()
    merged = []
    for start, end in validated:
        if merged and start < merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))
    return merged
