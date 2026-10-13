---
name: req-lab-v3
description: "Call req3: turn a raw requirement into a review-checked, implementable spec bundle (requirements + spec, any output format). Use when you need requirements/specs produced. Drop-in successor to req-lab-v2."
version: 1.0.0
---

# req-lab-v3 — how to call this agent

You are the **caller** (consumer). This agent turns a raw requirement into a
confirmed requirements document plus a bounded, review-checked design spec,
delivered as versioned artifacts in the output format you choose. It is
long-running (**15–50 minutes** typical) and pauses to ask clarifying
questions; unanswered questions expire after 24 h and the system applies
each question's recorded default (marked as system-selected).

Everything you need is this file + one tool beside it:

```
<this folder>/tools/req3_client.py    # stdlib-only Python 3 client — THE way to call
```

Gateway URL: `http://172.28.50.183:7790` (override with `--url` or env
`REQ3_URL`). **Auth: every call must carry `X-API-Key`** (or
`Authorization: Bearer`) — pass `--api-key <KEY>` or set env `REQ3_API_KEY`,
or ship the key in `API_KEY.txt` beside this SKILL.md (one line). Check
reachability first:

```bash
REQ3_API_KEY=<key> python3 tools/req3_client.py info   # agent card JSON → alive
```

## The flow (this is the whole protocol)

```bash
# 1. start a new project  (text = raw requirement, any language, verbatim)
python3 tools/req3_client.py start "We need a web UI for borrowing lab equipment..." \
    --output-format men          # men (default) | default | json | <registered>

# 2. wait until it needs you (prints state changes, exits at a gate)
python3 tools/req3_client.py wait <task_id>

# 3. at state input-required, either answer questions...
python3 tools/req3_client.py answer <task_id> Q-01="int and float only" Q-02="Yes"
#    ...or, at the confirm gate, approve / send back:
python3 tools/req3_client.py approve <task_id>
python3 tools/req3_client.py reject <task_id> "add Kelvin support"

# 4. at state completed, download the artifacts
python3 tools/req3_client.py download <task_id> [--out dir/]
```

States: `submitted → working → input-required → … → completed | failed`.
You may cancel any time: `python3 tools/req3_client.py cancel <task_id>`.

## Output formats

- `men` (**default**): Men's-orchestrator SPI bundle — `requirement.json`
  + `spec.md` + `plan.md` + `traceability.json` in ONE delivery at
  completion (v2 delivered in two pauses; v3 ships both stages together).
  Byte-compatible with the v2 `men`/`men-spi`/`men-plan` converters.
- `default`: `requirement.md` + `spec.md` (canonical markdown).
- `json`: raw canonical JSON documents.
- registered custom profiles: ask the req3 owner, or POST your own to
  `/v1/output-profiles` (sandboxed Jinja2, deterministic).

All deliveries include `manifest.json` (versions, sha256 file list,
decisions, token/time metrics). Older artifact versions stay downloadable
(`?version=N`).

## Differences from req-lab-v2 (migration notes)

| v2 | v3 |
|---|---|
| URL `https://req2.rctz.online` | `https://req3.rctz.online` (public via Cloudflare tunnel) |
| API key for v2 gateway | new key for req3 (same `X-API-Key` header works) |
| `--output-format men-spi` / `men-plan` | alias to `men` (both files always included) |
| two deliveries (gate + completion) | one delivery at completion, all files |
| poll only | poll, SSE (`/v1/jobs/{id}/events`), or signed webhooks (`--callback-url`; verify `X-Req3-Signature: sha256=HMAC-SHA256(body, REQ3_WEBHOOK_SECRET)`) |
| sequential | up to 5 jobs run in parallel — submit freely |

## Machine contracts

- OpenAPI (REST v1): `GET /v1/openapi.json` (bearer auth)
- Agent card: `GET /.well-known/agent.json` (no auth) — also in this pack
  as `card.json`
- A2A JSON-RPC: `POST /a2a` — `message/send` (new job / answers / APPROVE /
  REJECT: text), `tasks/get`, `tasks/cancel`. Same part shapes as v2.

## Behavior guarantees

- Questions arrive in batches with a usable default answer each; expiry
  applies defaults and marks them (nothing blocks forever).
- Reviews are bounded (max rounds enforced server-side); only blocking
  findings delay delivery; P2 advisory notes ship as `known_issues`.
- Artifacts are deterministic pure renders of validated canonical JSON —
  same input, byte-identical output.
