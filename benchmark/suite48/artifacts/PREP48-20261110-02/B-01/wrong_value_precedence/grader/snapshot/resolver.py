"""Resolve values without changing caller-owned configuration."""
from aliases import canonical_name
from defaults import DEFAULTS


def resolve(name, cli, env, config):
    key = canonical_name(name)
    for source in (cli, env, config, DEFAULTS):
        if key in source:
            return source[key]
    raise KeyError(key)
