"""Small deterministic job scheduling helpers."""

import heapq


def task_names(jobs):
    """List known task names in sorted order."""
    return sorted(jobs)


def execution_order(jobs):
    """Return dependency order, breaking ties by the smallest available name."""
    remaining = {}
    dependents = {name: [] for name in jobs}
    for name, prerequisites in jobs.items():
        unique_prerequisites = set(prerequisites)
        for prerequisite in unique_prerequisites:
            if prerequisite not in jobs:
                raise ValueError(f"Unknown prerequisite: {prerequisite!r}")
            dependents[prerequisite].append(name)
        remaining[name] = len(unique_prerequisites)

    available = [name for name, count in remaining.items() if count == 0]
    heapq.heapify(available)
    order = []
    while available:
        name = heapq.heappop(available)
        order.append(name)
        for dependent in dependents[name]:
            remaining[dependent] -= 1
            if remaining[dependent] == 0:
                heapq.heappush(available, dependent)

    if len(order) != len(jobs):
        raise ValueError("Dependency cycle detected")
    return order
