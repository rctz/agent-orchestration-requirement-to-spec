---
name: req-lab-v3
description: "Call req3: turns a raw requirement into a confirmed requirements document + review-checked design spec. Use when you need requirements or a spec produced. Long-running service you drive through gates by relaying to your user (questions in, their answers and approval back) until artifacts download."
version: 1.4.0
---

# req-lab-v3 — calling guide

req3 is a **remote service** that produces a requirements document and a
design spec from a raw requirement. You (the calling agent) submit the
user's requirement text, then drive the job through up to two kinds of
gates, then download the finished documents.

You talk to it ONLY through the client in this folder — no HTTP crafting
needed:

```
tools/req3_client.py    # stdlib-only, Python 3, no dependencies
```

- Endpoint: `https://req3.rctz.online` (default; override with `--url` or env `REQ3_URL`)
- Auth: the API key ships in `API_KEY.txt` beside this file and is read
  automatically. Nothing to configure.
- Sanity check before first use (should print an agent card JSON):

```bash
python3 tools/req3_client.py info
```

## The lifecycle you drive

```
start ──► working ──► input-required ──► working ──► ... ──► completed ──► download
             │             │
             │             ├─ gate=questions   → answer  (may repeat, <=5 rounds)
             │             └─ gate=confirm     → show user → their approve/reject
             └──► failed (terminal; error says why)
```

Run these in order. After every command the client prints the state AND
exactly what to do next — follow that.

### 1. Submit the requirement (verbatim!)

```bash
python3 tools/req3_client.py start "We need a web UI for borrowing lab equipment..." \
    --output-format default --project lab-equipment-ui
```

- The text is the user's raw requirement, **any language, passed verbatim —
  never summarize or translate it**.
- `--output-format <name>` picks the artifact format, **fixed for the
  whole job** (chosen at start, cannot change later). Options:

| name | files | use when |
|---|---|---|
| `default` | `requirement.md` + `spec.md` (+ `manifest.json`) | humans/agents reading documents (recommended) |
| `json` | `requirements.json` + `spec.json` | you want raw canonical JSON to process |
| `men` | `requirement.json` + `spec.md` + `plan.md` + `traceability.json` | the Men orchestrator pipeline |

  Omitting the flag defaults to `men`. Custom profiles may also be
  registered server-side — list what is available any time with
  `python3 tools/req3_client.py formats`. An unknown name fails fast at
  start with the valid list.
- Prints: `task <task_id>: ...` — **remember that id**, every later command
  needs it.

### 2. Wait until the service needs you

```bash
python3 tools/req3_client.py wait <task_id>
```

Polls and prints state changes; exits when the task reaches
`input-required`, `completed`, or `failed`. The job is long-running —
expect multiple `working` minutes between gates. You can also check any
time with `status <task_id>`.

### 3. At `input-required` — read what the client prints and act

**Gate `questions`** — the client prints every question in full:
id `[kind]` text, choice options, and a default answer.

**WHO answers: these are product decisions owned by your USER.**
Relay the questions to your user (show them verbatim, including options
and defaults), collect their replies, then submit:

```bash
python3 tools/req3_client.py answer <task_id> Q-01="user's reply" Q-02="user's reply"
```

- Use the exact question ids shown (`Q-01=...`, quotes around values).
- Answer EVERY question of the round before submitting.
- Answer yourself ONLY when the user explicitly delegated the decisions to
  you ("you decide"). Otherwise never invent answers — a wrong guess
  becomes a permanent decision in the documents.
- `answer <task_id> --defaults` accepts every listed default: use it only
  for unattended/batch runs, or when the user says "take the defaults".
- More question rounds may follow — relay again and repeat.

**Gate `confirm_requirements`** — the requirements draft is finished and
**the APPROVE/REJECT decision belongs to your USER**. You must:

1. Print the full draft and show it to the user:

```bash
python3 tools/req3_client.py preview <task_id>
```

2. Get the user's explicit verdict, then submit it on their behalf:

```bash
python3 tools/req3_client.py approve <task_id>          # user said OK
python3 tools/req3_client.py reject <task_id> "the user's change request"
```

Never approve on your own judgment — approving locks the requirements and
starts the spec build. (If the gate sits unanswered past its expiry, the
system auto-approves and marks it — so surface it to the user promptly.)

### 4. At `completed` — download the documents

```bash
python3 tools/req3_client.py download <task_id> --out ./req3-out/
```

Writes the files (e.g. `requirement.md`, `spec.md`, `manifest.json`) into
the output dir. `manifest.json` lists every file with sha256 plus decision
and metric summaries. Hand the documents to whoever asked.

### Anytime

```bash
python3 tools/req3_client.py status <task_id>    # current state
python3 tools/req3_client.py cancel <task_id>    # abort a running job
```

## Rules that matter

- **One task per requirement.** Submit the text once; never re-submit while
  a task is live — `wait` on it instead.
- **Questions expire** after 24 h: unanswered ones get their default answer
  applied automatically (marked `system_default_expired` in the manifest),
  so nothing blocks forever — but answering is always better.
- **Answers are the USER's decisions, phrased as decisions** — free text
  (or one of the printed options for `choice`), e.g. `Q-03="USD with 2
  decimals"`. You are the messenger, not the decider (unless delegated).
- **approve/reject only exist at the confirm gate**; answer only at the
  questions gate. The client's printout tells you which gate you are at.
  At BOTH gates you act for the user: relay questions, show the draft,
  submit THEIR verdict — never decide for them unless they delegated it.
- **failed is recoverable by resubmission**: the error line
  `[code] message` says what went wrong; fix the input and `start` again.
- Artifacts are English regardless of the prompt language; question text
  comes back in the prompt's language.

## Machine endpoints (optional, for direct integration)

- Agent card (no auth): `GET /.well-known/agent.json`
- REST API with OpenAPI spec: `GET /v1/openapi.json` (send header `X-API-Key`)
- The client itself speaks the A2A JSON-RPC protocol (`POST /a2a`) —
  `message/send`, `tasks/get`, `tasks/cancel` — if you prefer raw calls.
