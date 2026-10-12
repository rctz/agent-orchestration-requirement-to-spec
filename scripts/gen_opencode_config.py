#!/usr/bin/env python3
"""Generate opencode/opencode.json from roles.yaml + prompts/ (design §2.1).

opencode.json is GENERATED — never hand-edit it. Re-run this script after
changing roles.yaml or prompts/. Provider credentials stay env-based
({env:LITELLM_BASE_URL} / {env:LITELLM_API_KEY}); the User-Agent header is
required by the owner's LiteLLM (design §6.2 / plan gotchas).

Usage:
  python3 scripts/gen_opencode_config.py \
      [--roles roles.yaml] [--prompts prompts] \
      [--design-model glm-5.3-flash] [--review-model glm-5.3] \
      [--out opencode/opencode.json]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

PERMISSIONS = {
    "bash": "deny",
    "webfetch": "deny",
    "edit": "deny",
    "external_directory": "deny",
}


def build(
    roles_path: Path,
    prompts_dir: Path,
    design_model: str,
    review_model: str,
) -> dict:
    data = yaml.safe_load(roles_path.read_text(encoding="utf-8")) or {}
    tiers = {"design": design_model, "review": review_model}
    agents: dict[str, dict] = {}
    for name, role in (data.get("roles") or {}).items():
        model = tiers[role["model_tier"]]
        prompt_file = prompts_dir / f"{name}.md"
        if prompt_file.is_file():
            prompt = prompt_file.read_text(encoding="utf-8").strip()
        else:
            print(f"warning: no prompt file {prompt_file}; role {name} gets empty prompt",
                  file=sys.stderr)
            prompt = role.get("prompt", "")
        entry: dict = {
            "mode": role.get("mode", "primary"),
            "model": f"litellm/{model}",
            "prompt": prompt,
            "description": role.get("description", ""),
            "permission": dict(PERMISSIONS),
        }
        tools = {
            tool: (value == "allow")
            for tool, value in (role.get("tools") or {}).items()
        }
        if tools:
            entry["tools"] = tools
        agents[name] = entry
    models = sorted(set(tiers.values()))
    return {
        "$schema": "https://opencode.ai/config.json",
        "provider": {
            "litellm": {
                "npm": "@ai-sdk/openai-compatible",
                "name": "LiteLLM",
                "options": {
                    "baseURL": "{env:LITELLM_BASE_URL}",
                    "apiKey": "{env:LITELLM_API_KEY}",
                    "headers": {"User-Agent": "curl/8.7.1"},
                },
                "models": {model: {"name": model} for model in models},
            }
        },
        "model": f"litellm/{design_model}",
        "share": "disabled",
        "autoupdate": False,
        "permission": dict(PERMISSIONS),
        "agent": agents,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--roles", default="roles.yaml")
    parser.add_argument("--prompts", default="prompts")
    parser.add_argument("--design-model", default="glm-5.3-flash")
    parser.add_argument("--review-model", default="glm-5.3")
    parser.add_argument("--out", default="opencode/opencode.json")
    args = parser.parse_args()
    config = build(Path(args.roles), Path(args.prompts), args.design_model, args.review_model)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(config, indent=2, ensure_ascii=False) + "\n",
                        encoding="utf-8")
    print(f"wrote {out_path} ({len(config['agent'])} agents, "
          f"models: {sorted(set([args.design_model, args.review_model]))})")


if __name__ == "__main__":
    main()
