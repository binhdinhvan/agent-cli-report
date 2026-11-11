"""Allowlist header protocol cho smoke; không chuyển credential/cookie/hop-by-hop."""

REQUEST_HEADERS = frozenset({
    "x-openai-internal-codex-responses-lite", "x-codex-beta-features",
    "x-codex-turn-metadata", "x-codex-turn-state", "x-codex-routing-hint",
    "x-codex-window-id", "session-id", "thread-id", "x-client-request-id",
    "originator", "user-agent",
})
RESPONSE_HEADERS = frozenset({
    "x-codex-turn-state", "x-request-id", "request-id", "retry-after",
})


def protocol_headers(headers, allowed):
    # Never trust a peer's hop-by-hop list, even for otherwise allowed fields.
    connection = {name.strip().lower() for name in headers.get("Connection", "").split(",")}
    result = {}
    for name, value in headers.items():
        name = name.lower()
        if name in allowed and name not in connection:
            if len(value) > 32768 or "\r" in value or "\n" in value:
                raise ValueError("Invalid protocol header value")
            result[name] = value
    return result
