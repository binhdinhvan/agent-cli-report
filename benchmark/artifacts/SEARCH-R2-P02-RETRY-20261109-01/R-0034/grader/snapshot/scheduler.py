"""Small deterministic job scheduling helpers."""

import heapq


def task_names(jobs):
    """List known task names in sorted order."""
    return sorted(jobs)


def execution_order(jobs):
    """Return dependency order, breaking ties by the smallest available name."""
    known_tasks = set(jobs)
    dependents = {task: [] for task in known_tasks}
    remaining = {}

    for task, prerequisites in jobs.items():
        unique_prerequisites = set(prerequisites)
        unknown = unique_prerequisites - known_tasks
        if unknown:
            raise ValueError("unknown prerequisite: {}".format(min(unknown)))

        remaining[task] = len(unique_prerequisites)
        for prerequisite in unique_prerequisites:
            dependents[prerequisite].append(task)

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

    if len(order) != len(known_tasks):
        raise ValueError("dependency cycle")
    return order
