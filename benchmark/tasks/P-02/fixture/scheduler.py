"""Small deterministic job scheduling helpers."""


def task_names(jobs):
    """List known task names in sorted order."""
    return sorted(jobs)


def execution_order(jobs):
    """Return dependency order, breaking ties by the smallest available name."""
    raise NotImplementedError("Dependency ordering is not implemented yet")
