from routing import validation, handlers

def dispatch(command, payload):
    normalized = validation.validate_payload(command, payload)
    return getattr(handlers, "handle_" + command)(normalized)
