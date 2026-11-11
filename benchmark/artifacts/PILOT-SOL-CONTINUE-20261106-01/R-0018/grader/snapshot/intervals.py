"""Helpers for half-open integer intervals."""


def merge_intervals(intervals):
    """Return sorted, merged intervals without changing the caller's data."""
    ordered = []
    for interval in intervals:
        try:
            start, end = interval
        except (TypeError, ValueError):
            raise ValueError("each interval must be a pair of integers") from None
        if (not isinstance(start, int) or isinstance(start, bool)
                or not isinstance(end, int) or isinstance(end, bool)
                or start >= end):
            raise ValueError("each interval must contain integers with start < end")
        ordered.append((start, end))

    ordered.sort()
    if not ordered:
        return []

    merged = [ordered[0]]
    for start, end in ordered[1:]:
        previous_start, previous_end = merged[-1]
        if start < previous_end:
            merged[-1] = (previous_start, max(previous_end, end))
        else:
            merged.append((start, end))
    return merged
