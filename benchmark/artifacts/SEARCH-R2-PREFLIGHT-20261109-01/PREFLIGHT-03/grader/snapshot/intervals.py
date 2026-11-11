"""Helpers for half-open integer intervals."""


def merge_intervals(intervals):
    """Return sorted, merged intervals without changing the caller's data."""
    intervals.sort()
    merged = [intervals[0]]
    for start, end in intervals[1:]:
        if start <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    return [tuple(interval) for interval in merged]
