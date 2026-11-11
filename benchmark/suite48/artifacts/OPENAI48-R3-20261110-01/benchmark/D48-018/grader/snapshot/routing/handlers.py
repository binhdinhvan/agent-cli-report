"""Service delegation for already validated payloads."""
import service


def handle_create(normalized):
    """Create using a validated dict and return the service result."""
    return service.create(normalized["name"])


def handle_update(normalized):
    """Update using a validated dict and return the service result."""
    return service.update(normalized["id"], normalized["name"])


def handle_delete(normalized):
    """Delete using a validated dict and return the service result."""
    return service.delete(normalized["id"])
