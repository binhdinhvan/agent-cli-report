"""Canonical setting names and historical aliases."""
ALIASES = {"quick": "short", "short": "timeout", "loop_a": "loop_b", "loop_b": "loop_a"}


def canonical_name(name):
    visited = set()
    while name in ALIASES:
        if name in visited:
            raise ValueError("alias cycle: " + name)
        visited.add(name)
        name = ALIASES[name]
    return name
