# req3

Plug-and-play **Requirement & Spec service**. A caller (usually an
orchestrator agent) sends a user's prompt; req3 asks clarifying questions
until the requirements are clear, gets them confirmed, then produces a
bounded, review-checked spec in the caller's chosen output format.

Design: `~/kaizen/design/req3-design.md` (normative; rendered diagrams in
`~/kaizen/design/req3-diagrams/`) · Plan: `~/kaizen/design/req3-implementation-plan.md`

Status: **M0 bootstrap** — skeleton only; feature code lands per milestone (M1+).

## Layout

| Path | What |
|---|---|
| `req3/` | Python package: `api/` `engine/` `executor/` `repo/` `render/` `checks/` `store/` |
| `roles.yaml` | Backend-neutral role → model tier / permissions / skills (M2) |
| `prompts/` `schemas/` `checklists/` | Backend-neutral prompts / JSON Schemas / review checklists (M2–M4) |
| `profiles/builtin/` | Output profiles: `default`, `json`, `men` (M3, M8) |
| `opencode/` | opencode server config (**generated** in M2, do not hand-edit) + skills |
| `scripts/` | `gen_opencode_config.py` `render_diagrams.sh` `deploy.sh` `pilot.py` |
| `tests/` | `unit/` `contract/` `live/` (live = real LLM stack, opt-in marker `live`) |
| `docker/` + `docker-compose.yml` | Container builds + compose stack (M2/M4/M9) |
| `pilot/` | Scripted answers + pilot report (M10) |

## Develop (.184)

```bash
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
.venv/bin/pytest -q            # unit + contract (no LLM)
.venv/bin/pytest -m live       # real opencode/LLM stack (M2+)
```

## Deploy (.183)

```bash
scripts/deploy.sh              # rsync code + .env (mode 600) + docker compose up -d --build
```

Secrets: copy `.env.example` → `.env`, set real values, `chmod 600 .env`.
Never commit `.env`.

## Caller quickstart (curl)

Lands with the API milestones (M1+): submit → track → answer → confirm →
revise → download artifacts.
