"""Payload validation and normalization for routing commands."""
from models import PayloadError


def validate_payload(command, payload):
    """Validate a command payload and return a new normalized dictionary."""
    if command not in ("create", "update", "delete"):
        raise ValueError("unknown command: " + command)
    if not isinstance(payload, dict):
        raise PayloadError("payload must be a dictionary")
    normalized = {}
    if command in ("update", "delete"):
        identifier = payload.get("id")
        if type(identifier) is not int or identifier <= 0:
            raise PayloadError("id must be positive integer")
        normalized["id"] = identifier
    if command in ("create", "update"):
        name = payload.get("name")
        if not isinstance(name, str) or not name.strip():
            raise PayloadError("name must be nonempty string")
        normalized["name"] = name.strip()
    return normalized
