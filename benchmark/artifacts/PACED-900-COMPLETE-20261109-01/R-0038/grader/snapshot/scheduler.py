"""Small deterministic job scheduling helpers."""

import heapq


def task_names(jobs):
    """List known task names in sorted order."""
    return sorted(jobs)


def execution_order(jobs):
    """Return dependency order, breaking ties by the smallest available name."""
    dependencies = {task: set(prerequisites) for task, prerequisites in jobs.items()}
    dependents = {task: [] for task in jobs}

    for task, prerequisites in dependencies.items():
        unknown = prerequisites.difference(jobs)
        if unknown:
            raise ValueError(f"Unknown prerequisite(s) for {task!r}: {sorted(unknown)!r}")
        for prerequisite in prerequisites:
            dependents[prerequisite].append(task)

    remaining = {task: len(prerequisites) for task, prerequisites in dependencies.items()}
    available = [task for task, count in remaining.items() if count == 0]
    heapq.heapify(available)
    order = []

    while available:
        task = heapq.heappop(available)
        order.append(task)
        for dependent in dependents[task]:
            remaining[dependent] -= 1
            if remaining[dependent] == 0:
                heapq.heappush(available, dependent)

    if len(order) != len(jobs):
        raise ValueError("Dependency cycle detected")
    return order
