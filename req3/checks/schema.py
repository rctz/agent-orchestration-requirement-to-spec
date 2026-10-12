"""JSON Schema validation for canonical documents (design §7).

All schemas are JSON Schema 2020-12 files in schemas/. Validation failure
anywhere upstream triggers the repair loop with these exact error strings
(design §7) — keep messages precise and stable.
"""
from __future__ import annotations

import json
from functools import cache
from typing import Any

import jsonschema

from ..paths import SCHEMAS_DIR


@cache
def load_schema(name: str) -> dict[str, Any]:
    path = SCHEMAS_DIR / f"{name}.schema.json"
    if not path.is_file():
        raise FileNotFoundError(f"schema not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def validate(instance: Any, schema: dict[str, Any]) -> list[str]:
    """Return a list of human-readable errors ([] = valid)."""
    validator = jsonschema.Draft202012Validator(schema)
    errors = []
    for error in validator.iter_errors(instance):
        location = "/".join(str(part) for part in error.absolute_path) or "<root>"
        errors.append(f"{location}: {error.message}")
    return errors


def validate_named(instance: Any, name: str) -> list[str]:
    return validate(instance, load_schema(name))
