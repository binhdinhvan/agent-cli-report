"""Command dispatcher to refactor without behavior changes.

Required extraction API:
validate_payload(command, payload) -> normalized new dict (id/name as needed).
handle_create(normalized), handle_update(normalized), handle_delete(normalized)
-> service result. Handlers accept a validated dict; no validation repetition.
dispatch(command, payload) must validate exactly once then call the right handler.
"""
from models import PayloadError
import service
from routing import handlers, validation


def dispatch(command, payload):
    normalized = validation.validate_payload(command, payload)
    if command == "create":
        return handlers.handle_create(normalized)
    if command == "update":
        return handlers.handle_update(normalized)
    return handlers.handle_delete(normalized)
