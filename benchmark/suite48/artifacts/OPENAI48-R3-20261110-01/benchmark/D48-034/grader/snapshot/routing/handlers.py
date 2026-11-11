"""Service delegation for validated command payloads."""

import service


def handle_create(normalized):
    """Accept a validated dict and return the create service result."""
    return service.create(normalized["name"])


def handle_update(normalized):
    """Accept a validated dict and return the update service result."""
    return service.update(normalized["id"], normalized["name"])


def handle_delete(normalized):
    """Accept a validated dict and return the delete service result."""
    return service.delete(normalized["id"])
