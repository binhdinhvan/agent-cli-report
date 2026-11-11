from routing.validation import validate_payload as validate
from routing.handlers import handle_create, handle_update, handle_delete

def dispatch(command, payload):
    normalized = validate(command, payload)
    if command == "create":
        return handle_create(normalized)
    if command == "update":
        return handle_update(normalized)
    return handle_delete(normalized)
