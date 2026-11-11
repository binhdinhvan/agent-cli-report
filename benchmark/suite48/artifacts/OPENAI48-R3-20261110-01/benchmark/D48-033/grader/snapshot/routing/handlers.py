"""Service handlers accepting validated payloads."""

import service


def handle_create(normalized):
    """Create from a validated dict and return the service result."""
    return service.create(normalized["name"])


def handle_update(normalized):
    """Update from a validated dict and return the service result."""
    return service.update(normalized["id"], normalized["name"])


def handle_delete(normalized):
    """Delete from a validated dict and return the service result."""
    return service.delete(normalized["id"])
