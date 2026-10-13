# req3

Plug-and-play **Requirement & Spec service**. A caller (usually an
orchestrator agent) sends a user's prompt; req3 asks clarifying questions
until the requirements are clear, gets them confirmed, then produces a
bounded, review-checked spec in the caller's chosen output format.

Design: `~/kaizen/design/req3-design.md` (normative; rendered diagrams in
`~/kaizen/design/req3-diagrams/`) · Plan: `~/kaizen/design/req3-implementation-plan.md`

Status: **M0–M9 complete** — full pipeline (requirement → spec → render),
REST v1 + SSE, A2A adapter, signed webhooks, output-profile registry,
Docker deployment with healthchecks and memory limits. M10 pilot pending.

## Layout

| Path | What |
|---|---|
| `req3/` | Python package: `api/` `engine/` `executor/` `repo/` `render/` `checks/` `store/` |
| `roles.yaml` | Backend-neutral role → model tier / permissions / skills (M2) |
| `prompts/` `schemas/` `checklists/` | Backend-neutral prompts / JSON Schemas / review checklists (M2–M4) |
| `profiles/builtin/` | Output profiles: `default`, `json`, `men` (M3, M8) |
| `req3/render/men_pkg/` | Verbatim v2 converter port — behavior pinned by golden tests, not linted |
| `opencode/` | opencode server config (**generated** in M2, do not hand-edit) + skills |
| `scripts/` | `gen_opencode_config.py` `render_diagrams.sh` `deploy.sh` `live_check.py` `pilot.py` |
| `tests/` | `unit/` `contract/` `live/` (live = real LLM stack, opt-in marker `live`) |
| `docker/` + `docker-compose.yml` | Container builds + hardened compose stack (M2/M4/M9) |
| `pilot/` | Scripted answers + pilot report (M10) |

## Develop (.184)

```bash
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
.venv/bin/pytest -q            # unit + contract (no LLM)
.venv/bin/pytest -m live       # real opencode/LLM stack (M2+)
```

## Deploy (any Docker host)

```bash
# 1. secrets — never committed
cp .env.example .env && $EDITOR .env && chmod 600 .env
#    keys: LITELLM_BASE_URL, LITELLM_API_KEY, REQ3_API_KEY,
#          REQ3_WEBHOOK_SECRET, OPENCODE_SERVER_PASSWORD

# 2. build + run (this repo)
docker compose up -d --build
curl -s http://localhost:7790/healthz        # {"status": "ok", ...}

# 2b. or deploy to a remote host with one command (rsync + compose)
REQ3_DEPLOY_HOST=pi@<host> scripts/deploy.sh
```

The gateway publishes `:7790` (bearer-key guarded); the opencode executor
stays on the internal compose network (`:4096` never published). Jobs and
SQLite state live in the `req3-data` named volume; put repos you want
scannable under a host dir mounted read-only at `/repos`
(`repo.allowed_roots` in `docker/gateway.config.yaml`).

## Caller quickstart (curl only)

```bash
API=http://localhost:7790
AUTH="Authorization: Bearer $REQ3_API_KEY"

# 1) submit a job (any language prompt; pick an output profile)
JOB=$(curl -s -X POST "$API/v1/jobs" -H "$AUTH" -H 'Content-Type: application/json' \
  -d '{"prompt": "Build a celsius-to-fahrenheit converter function",
       "output_profile": "default",
       "callback_url": "https://caller.example/hook"}' | python3 -c 'import json,sys;print(json.load(sys.stdin)["job_id"])')

# 2) track it (poll, or GET /v1/jobs/$JOB/events?format=json, or SSE)
curl -s "$API/v1/jobs/$JOB" -H "$AUTH"

# 3) answer clarifying questions when status=input_required, gate=questions
curl -s -X POST "$API/v1/jobs/$JOB/answers" -H "$AUTH" -H 'Content-Type: application/json' \
  -d '{"answers": {"Q-01": "int and float only"}}'

# 4) confirm the requirements at the confirm_requirements gate
curl -s -X POST "$API/v1/jobs/$JOB/answers" -H "$AUTH" -H 'Content-Type: application/json' \
  -d '{"action": "confirm"}'
#    or send it back: {"action": "change_request", "text": "add Kelvin"}

# 5) post-completion change request
curl -s -X POST "$API/v1/jobs/$JOB/revise" -H "$AUTH" -H 'Content-Type: application/json' \
  -d '{"text": "Use SQLite instead of a JSON file"}'

# 6) download artifacts (versioned; ?version=N for older ones)
curl -s "$API/v1/jobs/$JOB/artifacts"      -H "$AUTH"          # list + manifest
curl -s "$API/v1/jobs/$JOB/artifacts/spec.md" -H "$AUTH"        # one file
curl -s "$API/v1/jobs/$JOB/artifacts.zip"  -H "$AUTH" -o out.zip
```

Webhook deliveries (if `callback_url` set) are POSTed on `input_required`,
`completed`, `completed_with_issues`, `failed`, signed with
`X-Req3-Signature: sha256=HMAC-SHA256(body, REQ3_WEBHOOK_SECRET)` and
retried with backoff. Verify a delivery on your side:

```bash
BODY='{"job_id":"...","event":"completed"}'   # the RAW body bytes you received
printf '%s' "$BODY" | openssl dgst -sha256 -hmac "$REQ3_WEBHOOK_SECRET" | awk '{print $2}'
# must equal the hex part of the X-Req3-Signature header ("sha256=<hex>")
```

### A2A (JSON-RPC) — v2 clients work unchanged

```bash
curl -s -X POST "$API/a2a" -H "$AUTH" -H 'Content-Type: application/json' -d '{
  "jsonrpc": "2.0", "id": 1, "method": "message/send",
  "params": {"message": {"role": "user", "parts": [
    {"kind": "text", "text": "Build a tiny CLI"},
    {"kind": "data", "data": {"options": {"output_profile": "men"}}}]}}}'
# task states: submitted/working/input-required/completed/failed
# reply text "APPROVE" at the confirm gate, "REJECT: <reason>" to send back
curl -s "$API/.well-known/agent.json"        # agent card
```

### Output profiles

Builtin: `default` (requirement.md + spec.md), `json` (canonical JSON),
`men` (Men's-orchestrator SPI bundle). Register your own (Jinja2,
sandboxed, deterministic):

```bash
curl -s -X POST "$API/v1/output-profiles" -H "$AUTH" -H 'Content-Type: application/json' \
  -d '{"definition": {"name": "my-format", "files": [
        {"path": "out.md", "template": "{{ requirements.goal }}"}]}}'
curl -s -X POST "$API/v1/jobs" ... -d '{"prompt": "...", "output_profile": "my-format"}'
```
