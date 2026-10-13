"""Output-profile renderer (design §8): render(profile, requirements, spec,
meta) -> files. Pure function — the LLM is never involved; same inputs
produce byte-identical outputs.

- Built-in profiles live in profiles/builtin/<name>/profile.json.
- Custom profiles arrive as dicts (validated here); their templates are
  inline Jinja sources.
- Templates run in a Jinja2 SandboxedEnvironment with a DictLoader (no
  filesystem access, no includes beyond the profile's own templates), a
  wall-clock render timeout and an output size cap.
- manifest.json is ALWAYS produced by code (builtin:manifest), never by a
  template.
"""
from __future__ import annotations

import concurrent.futures
import json
from pathlib import Path, PurePosixPath
from typing import Any

from jinja2 import DictLoader, StrictUndefined
from jinja2.exceptions import SecurityError, TemplateError
from jinja2.sandbox import SandboxedEnvironment

from ..paths import PROFILES_DIR
from .manifest import build_manifest
from .trace import build_trace

RENDER_TIMEOUT_S = 5.0
MAX_TEMPLATE_OUTPUT_BYTES = 5 * 1024 * 1024

CODE_GENERATORS = frozenset(
    {"builtin:manifest", "builtin:requirements.json", "builtin:spec.json",
     "builtin:men"}
)


class RenderError(Exception):
    """Profile invalid or rendering failed."""


class RenderTimeout(RenderError):
    pass


def validate_profile(defn: Any) -> list[str]:
    """Validate a profile definition (design §8). Returns error strings."""
    if not isinstance(defn, dict):
        return ["profile must be a JSON object"]
    errors: list[str] = []
    name = defn.get("name")
    if not isinstance(name, str) or not name.strip():
        errors.append("profile.name is required")
    files = defn.get("files")
    if not isinstance(files, list) or not files:
        errors.append("profile.files must be a non-empty list")
    else:
        for index, entry in enumerate(files):
            prefix = f"files[{index}]"
            if not isinstance(entry, dict):
                errors.append(f"{prefix} must be an object")
                continue
            path = entry.get("path")
            if not isinstance(path, str) or not path.strip():
                errors.append(f"{prefix}.path is required")
            else:
                pure = PurePosixPath(path)
                if pure.is_absolute() or ".." in pure.parts or path == "manifest.json":
                    errors.append(f"{prefix}.path is unsafe or reserved: {path!r}")
            template = entry.get("template")
            if not isinstance(template, str) or not template.strip():
                errors.append(
                    f"{prefix}.template is required ('builtin:…' or inline Jinja source)"
                )
    links = defn.get("links")
    if links is not None and not isinstance(links, dict):
        errors.append("profile.links must be an object")
    extensions = defn.get("extensions")
    if extensions is not None:
        if not isinstance(extensions, list):
            errors.append("profile.extensions must be a list")
        else:
            for index, ext in enumerate(extensions):
                if not isinstance(ext, dict) or not isinstance(ext.get("key"), str):
                    errors.append(f"extensions[{index}].key (string) is required")
                elif not ext.get("schema") or not isinstance(ext.get("schema"), dict):
                    errors.append(f"extensions[{index}].schema must be a JSON Schema object")
                elif not isinstance(ext.get("instruction"), str):
                    errors.append(f"extensions[{index}].instruction (string) is required")
    return errors


def load_builtin_profile(name: str) -> dict[str, Any]:
    path = PROFILES_DIR / "builtin" / name / "profile.json"
    if not path.is_file():
        raise RenderError(f"unknown builtin profile: {name!r}")
    return json.loads(path.read_text(encoding="utf-8"))


def _json_bytes(doc: dict[str, Any]) -> bytes:
    return (json.dumps(doc, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def _environment(templates: dict[str, str]) -> SandboxedEnvironment:
    return SandboxedEnvironment(
        loader=DictLoader(templates),
        undefined=StrictUndefined,
        autoescape=False,  # we render markdown/json text, not HTML
    )


def _context(
    profile: dict[str, Any],
    requirements: dict[str, Any] | None,
    spec: dict[str, Any] | None,
    meta: dict[str, Any],
) -> dict[str, Any]:
    requirements = requirements or {}
    spec = spec or {}
    trace = None
    links = profile.get("links") or {}
    traceability = links.get("traceability") or {}
    if traceability.get("enabled") and requirements and spec:
        trace = build_trace(requirements, spec)
    return {
        "r": requirements,
        "s": spec,
        "meta": meta,
        "trace": trace,
        "traceability_in": traceability.get("in"),
    }


def render_profile(
    profile: dict[str, Any] | str,
    *,
    requirements: dict[str, Any] | None,
    spec: dict[str, Any] | None,
    meta: dict[str, Any],
) -> dict[str, bytes]:
    """Render artifacts for one output profile. Returns {path: bytes}."""
    if isinstance(profile, str):
        profile = load_builtin_profile(profile)
    errors = validate_profile(profile)
    if errors:
        raise RenderError("invalid profile: " + "; ".join(errors))

    outputs: dict[str, bytes] = {}
    templates: dict[str, str] = {}
    template_paths: list[str] = []
    profile_dir = PROFILES_DIR / "builtin" / str(profile.get("name"))

    for entry in profile["files"]:
        path, template = entry["path"], entry["template"]
        if template in CODE_GENERATORS:
            if template == "builtin:requirements.json":
                if requirements is None:
                    raise RenderError("requirements doc missing for builtin:requirements.json")
                outputs[path] = _json_bytes(requirements)
            elif template == "builtin:spec.json":
                if spec is None:
                    raise RenderError("spec doc missing for builtin:spec.json")
                outputs[path] = _json_bytes(spec)
            elif template == "builtin:men":
                if requirements is None:
                    raise RenderError("requirements doc missing for builtin:men")
                from .men_bridge import MenBridgeError, men_bundle

                try:
                    outputs.update(men_bundle(requirements, spec, meta))
                except MenBridgeError as exc:
                    raise RenderError(str(exc)) from exc
            continue  # builtin:manifest is appended below, always
        if template.startswith("builtin:"):
            template_file: Path = profile_dir / template[len("builtin:"):]
            if not template_file.is_file():
                raise RenderError(f"builtin template not found: {template}")
            templates[path] = template_file.read_text(encoding="utf-8")
        else:
            templates[path] = template  # inline Jinja source (custom profile)
        template_paths.append(path)

    context = _context(profile, requirements, spec, meta)
    environment = _environment(templates)
    pool = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    try:
        for path in template_paths:
            try:
                future = pool.submit(
                    environment.get_template(path).render, **context
                )
                rendered = future.result(timeout=RENDER_TIMEOUT_S)
            except concurrent.futures.TimeoutError as exc:
                raise RenderTimeout(
                    f"template {path!r} exceeded {RENDER_TIMEOUT_S}s render timeout"
                ) from exc
            except (TemplateError, SecurityError) as exc:
                raise RenderError(f"template {path!r} failed: {exc}") from exc
            encoded = rendered.encode("utf-8")
            if len(encoded) > MAX_TEMPLATE_OUTPUT_BYTES:
                raise RenderError(
                    f"template {path!r} output exceeds {MAX_TEMPLATE_OUTPUT_BYTES} bytes"
                )
            outputs[path] = encoded
    finally:
        pool.shutdown(wait=False)
    outputs["manifest.json"] = _json_bytes(
        build_manifest(meta, outputs, requirements, spec)
    )
    return outputs
