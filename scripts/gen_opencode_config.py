#!/usr/bin/env python3
"""Generate opencode/opencode.json from roles.yaml (implemented in M2).

Reads the backend-neutral role definitions (roles.yaml, prompts/, design
§6.1/§11 permission rules) and emits the opencode server config: provider
litellm from env, per-agent permissions, server password. opencode.json is
GENERATED — never hand-edit it.
"""
