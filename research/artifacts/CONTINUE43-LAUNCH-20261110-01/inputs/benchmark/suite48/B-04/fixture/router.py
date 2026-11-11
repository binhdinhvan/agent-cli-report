"""Command dispatcher to refactor without behavior changes.

Required extraction API:
validate_payload(command, payload) -> normalized new dict (id/name as needed).
handle_create(normalized), handle_update(normalized), handle_delete(normalized)
-> service result. Handlers accept a validated dict; no validation repetition.
dispatch(command, payload) must validate exactly once then call the right handler.
"""
from models import PayloadError
import service


def dispatch(command, payload):
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
    if command == "create":
        return service.create(normalized["name"])
    if command == "update":
        return service.update(normalized["id"], normalized["name"])
    return service.delete(normalized["id"])
