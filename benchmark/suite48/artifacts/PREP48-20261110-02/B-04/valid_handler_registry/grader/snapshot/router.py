from routing.validation import validate_payload
from routing.handlers import handle_create, handle_update, handle_delete
HANDLERS = {"create": handle_create, "update": handle_update, "delete": handle_delete}

def dispatch(command, payload):
    normalized = validate_payload(command, payload)
    return HANDLERS[command](normalized)
