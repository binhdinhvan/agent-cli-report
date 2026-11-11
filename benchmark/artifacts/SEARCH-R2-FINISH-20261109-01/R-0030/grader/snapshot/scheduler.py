"""Small deterministic job scheduling helpers."""

import heapq


def task_names(jobs):
    """List known task names in sorted order."""
    return sorted(jobs)


def execution_order(jobs):
    """Return dependency order, breaking ties by the smallest available name."""
    task_set = set(jobs)
    dependents = {task: [] for task in jobs}
    remaining = {}

    for task, required_tasks in jobs.items():
        unique_requirements = set(required_tasks)
        unknown = unique_requirements - task_set
        if unknown:
            raise ValueError("Unknown prerequisite: {!r}".format(min(unknown)))

        remaining[task] = len(unique_requirements)
        for required_task in unique_requirements:
            dependents[required_task].append(task)

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
