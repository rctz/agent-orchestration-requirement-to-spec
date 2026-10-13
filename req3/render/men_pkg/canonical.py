"""canonical.py — the SINGLE deterministic parser: workspace → ParsedProject.

Everything downstream (converters/adapters) receives what this module
produces, never raw markdown. Parsing grammar intentionally mirrors the
mechanical validator (req2_validate.py, checks C1–C17): if a project reached
COMPLETE, this structure parses — the pipeline's own gates enforce it.

Design rules (see README.md):
- pure function, deterministic, no LLM, no network, no clock;
- fail LOUD: unrecognized shape raises ParseGap with file + reason, never a
  silent skip that would invent or drop requirements;
- verbatim-first: text fields are carried as written, not paraphrased.

Accepted requirement-id conventions (measured across real projects):
  v2.1 (csv2js):   **REQ-001 — Title.**  … *Acceptance:* …
  older (CI proj): ### FR-100 — Title     … (NFRs may live in a table)

The canonical model is deliberately THIN: every key exists because a consumer
needed it. Do not add keys speculatively.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

REQ_ID_RE = r"(?:REQ|FR|NFR)-\d+"


class ParseGap(Exception):
    """A workspace file does not match the expected grammar.

    Carries file path + reason. Callers treat this as a converter-layer
    warning (fail-soft delivery), tests treat it as a hard failure.
    """


# ---------------------------------------------------------------- helpers

def _read(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise ParseGap(f"expected file missing: {p}") from None


def header_fields(text: str, origin: str) -> dict:
    """Parse the '| field | value |' table every v2.1 artifact starts with."""
    out: dict[str, str] = {}
    in_table = False
    for ln in text.splitlines():
        m = re.match(r"^\|\s*([^|]+?)\s*\|\s*(.*?)\s*\|\s*$", ln)
        if not m:
            if in_table:
                break  # first table ended — later tables are content, not header
            continue
        in_table = True
        k, v = m.group(1), m.group(2)
        if k.lower() in ("field", "---", "") or set(k) <= set("-: "):
            continue
        if k.lower() in out:  # second table started (e.g. entities) — stop
            break
        out[k.lower()] = v
    if "status" not in out or "version" not in out:
        # v2.2 list-style header (DeepSeek designers, e.g. mini-issue-tracker
        # v13/17): "- Version: v13" / "- Status: APPROVED" lines at the top.
        # Additive fallback — table style above still wins when present.
        for ln in text.splitlines()[:30]:
            m = re.match(r"^-\s*([A-Za-z][A-Za-z _]*?)\s*:\s*(.+?)\s*$", ln)
            if not m:
                continue
            k = m.group(1).lower()
            if k in ("field", ""):
                continue
            out.setdefault(k, m.group(2))
            if "status" in out and "version" in out:
                break
    if "status" not in out or "version" not in out:
        raise ParseGap(f"{origin}: artifact header lacks status/version "
                       f"(found keys: {sorted(out)})")
    return out


def _latest(folder: Path, kind: str) -> Path:
    fs = sorted(folder.glob("*.md"))
    if not fs:
        raise ParseGap(f"no {kind} markdown found in {folder}")
    return fs[-1]


# ---------------------------------------------------------------- requirements

# v2.2.2 (2026-10-11 dummy-login-page): the closing bold may be followed
# by a trailing classification marker — "**REQ-001 — Title.** (FR)" —
# before end of line. Optional so all earlier shapes still match.
_BOLD_REQ = re.compile(
    r"(?ms)^\*\*((?:REQ|FR|NFR)-(\d+))\s*[—–-]\s*(.+?)\.\*\*(?:\s*\((?:FR|NFR)\))?\s*$(.*?)(?=^\*\*(?:REQ|FR|NFR)-\d+\s*[—–-]|^#{1,6}\s|\Z)")
_HEAD_REQ = re.compile(
    r"(?ms)^#{2,4}\s+((?:REQ|FR|NFR)-(\d+))\s*[—–-]\s*(.+?)\s*$(.*?)(?=^#{2,4}\s+(?:REQ|FR|NFR)-\d+\s*[—–-]|^#{1,6}\s|\Z)")
# v2.2 colon-style headings: "### FR-001: User registration" (DeepSeek
# designers). Same block boundaries as _HEAD_REQ.
_HEAD_REQ_COLON = re.compile(
    r"(?ms)^#{2,4}\s+((?:REQ|FR|NFR)-(\d+))\s*:\s*(.+?)\s*$(.*?)(?=^#{2,4}\s+(?:REQ|FR|NFR)-\d+\s*[:—–-]|^#{1,6}\s|\Z)")
# v2.2.1 bare-space heading (2026-10-05 eval fixtures, older Thai projects):
# "### FR-01 ยื่นคำขอยืม" — heading + plain-space title, no separator.
# Last-resort fallback: only consulted when no separator-style matched.
_HEAD_REQ_SPACE = re.compile(
    r"(?ms)^#{2,4}\s+((?:REQ|FR|NFR)-(\d+))\s+(.+?)\s*$(.*?)(?=^#{2,4}\s+(?:REQ|FR|NFR)-\d+|^#{1,6}\s|\Z)")
# v2.2 list-style (2026-10-05 web-scraper): "- **FR-001 (Title)**: body…"
# — bullet + bold id with parenthesised title, colon body. Block ends at
# the next bullet REQ, any heading, or EOF.
_LIST_REQ = re.compile(
    r"(?ms)^[-*]\s+\*\*((?:REQ|FR|NFR)-(\d+))\s*\(([^)]+)\)\*\*\s*:\s*(.+?)(?=^[-*]\s+\*\*(?:REQ|FR|NFR)-\d+|^#{1,6}\s|\Z)")
# v2.2.1 bare-bullet dash style (2026-10-05 greeting-function, glm-5.3-flash
# designer): "- REQ-001 — Title: body…" / "- REQ-002 — Title" + continuation
# lines (colon optional). No bold, no parens. Block ends at the next bullet
# REQ, any heading, or EOF. Title = remainder of the first line; body = the
# whole block (same shape as _HEAD_REQ), so acceptance scanning still works.
_LIST_REQ_DASH = re.compile(
    r"(?ms)^[-*]\s+((?:REQ|FR|NFR)-(\d+))\s*[—–-]\s+([^\n]+)"
    r"((?:\n(?![-*]\s+(?:REQ|FR|NFR)-\d+\s*[—–-]|#{1,6}\s)[^\n]*)*)")
_NFR_TABLE = re.compile(
    r"(?m)^\|\s*(NFR-\d+)\s*\(([^)]+)\)\s*\|\s*(.+?)\s*\|\s*(AC-[^|]+)\|")


def _parse_req_block(rid: str, title: str, body: str, origin: str) -> dict:
    am = re.search(r"\*Acceptance:\*\s*(.+?)(?=\n\s*\n|\n#{1,6}\s|\Z)", body, re.S)
    acceptance = " ".join(am.group(1).split()) if am else None
    q_refs = sorted(set(re.findall(r"\bQ-\d+\b", body)))
    d_refs = sorted(set(re.findall(r"\bD-\d+\b", body)))
    return {
        "id": rid,
        "kind": "NFR" if rid.startswith("NFR") else "FR",
        "title": title.strip(),
        "body": " ".join(body.split()),
        "acceptance": acceptance,
        "q_refs": q_refs,
        "d_refs": d_refs,
        "source": origin,
    }


# Annex/translation sections are NON-normative by construction (e.g. the
# 2026-10-05 greeting-function Thai translation annex, D-03): a complete
# verbatim translation restates every REQ id, which would trip the
# duplicate-id guard. Cut the document at the first annex-style heading
# before parsing; duplicates inside the normative body still fail loud.
_ANNEX_HEAD = re.compile(r"(?im)^#{1,4}\s.*(translation annex|translated annex|\bannex\b|\bappendix\b)")


def _strip_annex(text: str) -> str:
    m = _ANNEX_HEAD.search(text)
    return text[:m.start()] if m else text


def parse_requirements(text: str, origin: str) -> list[dict]:
    text = _strip_annex(text)
    reqs: list[dict] = []
    seen: set[str] = set()

    for m in _BOLD_REQ.finditer(text):
        rid = m.group(1)
        if rid in seen:
            raise ParseGap(f"{origin}: duplicate requirement id {rid}")
        seen.add(rid)
        reqs.append(_parse_req_block(rid, m.group(3), m.group(4), origin))

    if not reqs:  # fall back to heading convention (older projects)
        for rx in (_HEAD_REQ, _HEAD_REQ_COLON, _LIST_REQ, _LIST_REQ_DASH, _HEAD_REQ_SPACE):
            for m in rx.finditer(text):
                rid = m.group(1)
                if rid in seen:
                    raise ParseGap(f"{origin}: duplicate requirement id {rid}")
                seen.add(rid)
                reqs.append(_parse_req_block(rid, m.group(3), m.group(4), origin))
            if reqs:
                break

    # NFR table rows (older projects keep NFRs out of the block stream)
    for m in _NFR_TABLE.finditer(text):
        rid = m.group(1)
        if rid in seen:
            continue
        seen.add(rid)
        reqs.append({
            "id": rid, "kind": "NFR",
            "title": f"{m.group(2)} ({m.group(1)})",
            "body": m.group(3).strip(),
            "acceptance": " ".join(m.group(4).split()),
            "q_refs": [], "d_refs": [], "source": origin,
        })

    if not reqs:
        raise ParseGap(f"{origin}: no requirement ids recognized "
                       f"(neither bold-block nor heading convention)")
    return reqs


# ---------------------------------------------------------------- register / questions

_DECISION_ROW = re.compile(
    r"^\|\s*(D-\d+)\s*\|\s*(.+?)\s*\|\s*([A-Z_]+)\s*\|\s*(\S+)\s*\|\s*(.+?)\s*\|\s*$")


def parse_decision_register(text: str, origin: str) -> list[dict]:
    rows = []
    for ln in text.splitlines():
        m = _DECISION_ROW.match(ln)
        if not m:
            continue
        rows.append({"id": m.group(1), "decision": m.group(2), "status": m.group(3),
                     "owner": m.group(4), "source": m.group(5)})
    if not rows:
        raise ParseGap(f"{origin}: decision register has no parseable rows")
    unresolved = [r["id"] for r in rows if r["status"] in
                  ("USER_DECISION_REQUIRED", "DESIGN_DECISION_REQUIRED", "BLOCKED")]
    if unresolved:
        raise ParseGap(f"{origin}: unresolved decisions remain: {unresolved}")
    return rows


def parse_open_questions(text: str) -> list[dict]:
    """Closed-marker aware (v2.1 'Status: NONE OPEN', Thai legacy, and the
    2026-10-06 designer style: prose 'No open questions remain.' plus
    table rows whose status column reads 'ANSWERED: …')."""
    if (re.search(r"(?i)status:\s*none open", text)
            or re.search(r"(?i)no open questions", text)
            or "คำถามค้าง: 0" in text or "(ไม่มี)" in text):
        return []
    qs = []
    for ln in text.splitlines():
        m = re.match(r"^\|\s*(Q-\d+)[^|]*\|", ln)
        if m and not re.search(r"CLOSED|ANSWERED", ln, re.I):
            qs.append({"id": m.group(1), "line": ln})
    return qs


def parse_out_of_scope(text: str) -> list[str]:
    """'Explicitly out of scope' bullets, verbatim.

    The heading must carry BOTH '3.2' and 'out of scope' on ONE line —
    a greedy cross-line match would run to the next incidental 'out of
    scope' sentence deep in the NFR prose (found on real csv2js data).
    """
    m = re.search(
        r"(?ms)^#{2,4}[^\n]*3\.2[^\n]*[Oo]ut of scope[^\n]*\n(.*?)(?=^#{1,4}\s|\Z)",
        text)
    if not m:
        return []
    items = []
    for ln in m.group(1).splitlines():
        t = ln.strip()
        if t.startswith(("- ", "* ", "• ")):
            items.append(t[2:].strip())
        elif re.match(r"^\d+\.\s", t):
            items.append(re.sub(r"^\d+\.\s+", "", t))
        elif t and items and not t.startswith("#") and not re.match(r"^[-=_*]+$", t):
            # continuation line of the current bullet — multi-line bullets
            # were being silently truncated to their first line
            items[-1] = " ".join(x for x in (items[-1], t) if x)
    return items


def parse_intake_verbatim(text: str) -> str:
    m = re.search(r"(?ms)^##\s*Raw requirement \(verbatim\)\s*$.*?---+\s*\n(.*?)(?=\n## |\Z)", text)
    if not m:
        m = re.search(r"(?ms)^##\s*Raw requirement \(verbatim\)\s*\n(.*?)(?=\n## |\Z)", text)
    if not m:
        raise ParseGap("00-intake.md: 'Raw requirement (verbatim)' section not found")
    return m.group(1).strip()




def section_block(text: str, num: str) -> str:
    """Verbatim markdown body of a numbered section ('1', '3.1', '8', ...).

    Matches the heading line (^##/### <num>[.] Title) and captures until
    the next heading of equal-or-higher level. Returns '' when absent —
    callers decide whether absence is a gap.
    """
    pat = (r"(?ms)^#{2,3}\s+" + re.escape(num) + r"\.?\s+[^\n]*\n"
           r"(.*?)(?=^#{1,3}\s|\Z)")
    m = re.search(pat, text)
    return m.group(1).strip() if m else ""

# ---------------------------------------------------------------- spec

def parse_spec_map(text: str) -> list[dict]:
    """Requirement-map rows: | REQ/NFR | title | where designed |."""
    m = re.search(r"(?ms)^#{1,4}\s*1\.2\s+Requirement map.*?\n(.*?)(?=^#{1,4}\s|\Z)", text)
    rows = []
    if not m:
        return rows
    for ln in m.group(1).splitlines():
        rm = re.match(r"^\|\s*((?:REQ|FR|NFR)-\d+)\s*\|\s*([^|]+)\|\s*([^|]+)\|", ln)
        if rm:
            rows.append({"id": rm.group(1), "title": rm.group(2).strip(),
                         "where": rm.group(3).strip()})
    return rows


def parse_traceability(text: str) -> list[dict]:
    """Traceability-matrix rows: | REQ/NFR | designed in | invariant | failure id | test | evidence |."""
    m = re.search(r"(?ms)^#{1,4}\s*11\.?\s*Traceability matrix.*?\n(.*?)(?=\n#\s|\Z)", text)
    if not m:
        # v2.2 spec shape (mini-issue-tracker v17): the matrix is §10 and the
        # section title itself carries the term, whatever the number.
        m = re.search(r"(?ms)^#{1,4}\s*\d+\.?\s*Traceability matrix.*?\n(.*?)(?=\n#\s|\Z)", text)
    if not m:
        raise ParseGap("spec: no traceability-matrix section (mechval C11 requires one)")
    rows = []
    for ln in m.group(1).splitlines():
        cells = [c.strip() for c in ln.split("|")]
        if len(cells) >= 7 and re.match(rf"^{REQ_ID_RE}$|^Impl detail$", cells[1]):
            rows.append({
                "id": cells[1], "designed_in": cells[2], "invariant": cells[3],
                "failure_id": cells[4], "test": cells[5], "evidence": cells[6],
            })
    if not rows:
        raise ParseGap("spec: traceability matrix found but no parseable rows")
    return rows




DESIGN_TOPS = ("2", "4", "6", "7")   # FALLBACK ONLY when titles don't match
DESIGN_SINGLE = ("5.1", "9")        # whole-section DEs (fallback ids)

# Title-driven DE discovery (2026-10-06, shopping-cart incident): the
# spec's top-section NUMBERING is the designer's choice, not a contract —
# csv2json put "Module-by-module design" at §4, shopping-cart put
# "Module designs" at §3, and DESIGN_TOPS=("2","4","6","7") missed §3
# entirely → REQ-008/009 landed on no DE → traceability.json shipped ACs
# with empty design_elements. Match sections by TITLE keywords instead;
# the numeric DESIGN_TOPS stay as a fallback for specs whose titles
# don't use the vocabulary below.
_DE_TITLE_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    # (kind, (any-of keywords in lowercase title))
    ("architecture", ("architecture",)),
    ("module", ("module", "module-by-module", "module design", "designs")),
    ("state", ("state & flow", "state and flow", "state machine", "state & flows", "flows")),
    ("interface", ("interface contract", "interface")),
    ("error", ("error", "recovery", "failure")),
    ("data", ("data model", "domain model", "data dictionary", "entities")),
    ("nfr", ("non-functional", "nfr")),
)


def _classify_top_section(title: str) -> str | None:
    t = (title or "").lower()
    for kind, kws in _DE_TITLE_RULES:
        if any(kw in t for kw in kws):
            return kind
    return None


def parse_design_elements(text: str) -> list[dict]:
    """Design-bearing spec sections as Men's DE-n design elements.

    TITLE-DRIVEN (2026-10-06): subsections of whichever top sections carry
    architecture/module/state/interface/error/NFR titles become DEs,
    WHATEVER their section numbers are; plus the state-machine and NFR
    top sections as whole DEs. Numeric DESIGN_TOPS ("2","4","6","7") remain
    only as a fallback when no title matches. With this set every REQ/NFR
    the spec maps via §1.2/§11 'designed in' lands on >=1 DE (verified on
    csv2json spec v16 + shopping-cart spec v4).
    Bodies verbatim; ids positional in document order (stable per version).
    """
    des: list[dict] = []
    # subsection DEs: capture "## 4.1 Title" .. until next #/##/### heading
    tops: list[tuple[str, str]] = []   # (section number, kind) in doc order
    for tm in re.finditer(r"(?m)^#{1,3}\s+(\d+)\.?\s+([^\n]+)$", text):
        kind = _classify_top_section(tm.group(2))
        if kind:
            tops.append((tm.group(1), kind))
    if not tops:
        tops = [(n, "") for n in DESIGN_TOPS]
    for top, _kind in tops:
        for sm in re.finditer(
                r"(?ms)^#{2,3}\s+(" + top + r"\.\d+)\s+([^\n]+)\n(.*?)(?=^#{1,3}\s|\Z)",
                text):
            sec, title, body = sm.group(1), sm.group(2), sm.group(3)
            if not any(d["section"] == sec for d in des):
                des.append({"section": sec, "title": title.strip(),
                            "kind": _kind or None,
                            "body": body.strip(), "_pos": sm.start()})
    # whole-section DEs: the NFR top (usually one undivided block) and a
    # state top with NO captured subsections; whatever their numbers
    # ("5.1"/"9" kept as fallback when titles don't match)
    whole: list[tuple[str, str]] = [(t, k) for t, k in tops if k in ("state", "nfr")]
    if not whole:
        whole = [(s, "state" if s != "9" else "nfr") for s in DESIGN_SINGLE]
    for sec, kind in whole:
        if kind == "state" and any(d["section"].startswith(sec + ".") for d in des):
            continue  # subsection DEs already carry the state machine
        m = re.search(
            r"(?ms)^#{1,3}\s+" + re.escape(sec) + r"\.?\s+([^\n]*)\n(.*?)(?=^#{1,2}\s|\Z)",
            text)
        if m and not any(d["section"] == sec for d in des):
            des.append({"section": sec, "title": m.group(1).strip() or sec,
                        "kind": kind,
                        "body": m.group(2).strip(), "_pos": m.start()})
    des.sort(key=lambda d: d["_pos"])
    out = []
    for d in des:
        d.pop("_pos", None)
        d["id"] = "DE-" + str(len(out) + 1)
        out.append(d)
    if not out:
        raise ParseGap("spec: no design-bearing sections parsed "
                       "(no titled architecture/module/state/interface/"
                       "error/NFR tops, fallback 2/4/5.1/6/7/9 either)")
    return out


def parse_spec_design_sections(text: str) -> list[dict]:
    """§2 architecture / §2.3 ADRs — plan.md input (Technical Context)."""
    out = []
    for num, label in [("2.1", "component_diagram"), ("2.2", "component_responsibilities"),
                       ("2.3", "adr_decisions"), ("2.4", "deliberately_absent")]:
        b = section_block(text, num)
        if b:
            out.append({"key": label, "section": num, "body": b})
    return out

# ---------------------------------------------------------------- entry point

REQUIREMENT_STAGES = ("AWAIT_USER", "AWAIT_USER_ON_CARD", "AWAIT_USER_APPROVAL",
                      "REQ_REVIEW", "SPEC_DESIGN", "SPEC_REVIEW", "ADV_REVIEW",
                      "COLD_AUDIT", "FINAL_REPORT", "COMPLETE")


def parse(workspace: Path, stage: str = "design") -> dict:
    """workspace = req-lab project root (STATE.json, requirements/, ...).

    stage='requirement'  — the requirement set is final (req-review PASS /
        user gate); spec need not exist yet. Powers the requirement.json +
        spec.md export Men's orchestrator shows the user for confirmation.
    stage='design'       — full pipeline COMPLETE; spec APPROVED. Powers
        the plan.md + traceability.json export for the implementor.

    Returns the ParsedProject dict every converter consumes. Raises ParseGap
    with file+reason on unrecognized shapes — never invents content.
    """
    workspace = Path(workspace)
    state = json.loads(_read(workspace / "STATE.json"))
    phase = state.get("phase")
    if stage == "design" and phase != "COMPLETE":
        raise ParseGap(f"STATE.json: phase is {phase!r}, not COMPLETE")
    if stage == "requirement" and phase not in REQUIREMENT_STAGES:
        raise ParseGap(f"STATE.json: phase {phase!r} too early for a "
                       f"requirement-stage export (requirements not finalized)")

    req_f = _latest(workspace / "requirements", "requirements")
    spec_f = _latest(workspace / "spec", "spec") if (stage == "design" and (workspace / "spec").exists()) else None
    req_txt = _read(req_f)
    req_hdr = header_fields(req_txt, str(req_f))

    if stage == "requirement":
        # The requirement set must be review-PASSED AND finalized: header
        # status APPROVED, OR the pipeline is legitimately holding at the
        # user-approval gate (STATE.json phase == 'AWAIT_USER_APPROVAL')
        # where the flip to APPROVED only happens after the user approves.
        # Any other phase (question rounds, REQ_REVIEW, post-gate) with a
        # non-APPROVED header is still refused.
        if (req_hdr.get("status") != "APPROVED"
                and phase != "AWAIT_USER_APPROVAL"):
            raise ParseGap(f"requirements status is {req_hdr.get('status')!r}, "
                           f"not APPROVED (requirement-stage export needs the "
                           f"finalized set)")
        spec_txt, spec_hdr = "", {}
    else:
        spec_txt = _read(spec_f)
        spec_hdr = header_fields(spec_txt, str(spec_f))
        if req_hdr.get("status") != "APPROVED" or spec_hdr.get("status") != "APPROVED":
            raise ParseGap(f"requirements/spec not APPROVED "
                           f"(req={req_hdr.get('status')!r}, spec={spec_hdr.get('status')!r})")

    intake_txt = _read(workspace / "appendix" / "00-intake.md")
    decisions = parse_decision_register(
        _read(workspace / "appendix" / "03-decision-register.md"),
        "appendix/03-decision-register.md")
    open_qs = parse_open_questions(_read(workspace / "appendix" / "02-open-questions.md"))
    if open_qs and stage == "design":
        raise ParseGap(f"open questions remain: {[q['id'] for q in open_qs]}")

    requirements = parse_requirements(req_txt, str(req_f.relative_to(workspace)))

    provenance = {
        "slug": state.get("slug", workspace.name),
        "verdict": state.get("verdict"),
        "complete_at": state.get("complete_at"),
        "requirements_file": str(req_f.relative_to(workspace)),
        "spec_file": str(spec_f.relative_to(workspace)) if spec_f else None,
        "requirements_version": req_hdr.get("version"),
        "spec_version": spec_hdr.get("version"),
        "user_approval": state.get("user_approval"),
        "gates": _gate_trail(state),
    }

    out = {
        "slug": state.get("slug", workspace.name),
        "verdict": state.get("verdict"),
        "intake_verbatim": parse_intake_verbatim(intake_txt),
        "requirements": requirements,
        "nfrs": [r for r in requirements if r["kind"] == "NFR"],
        "out_of_scope": parse_out_of_scope(req_txt),
        "decisions": decisions,
        "n_user_decisions": sum(1 for d in decisions if d["owner"] == "user"),
        "open_questions": open_qs,
        "spec_map": parse_spec_map(spec_txt) if stage == "design" else [],
        "traceability": parse_traceability(spec_txt) if stage == "design" else [],
        "sections": {
            "goal": section_block(req_txt, "1"),
            "users": section_block(req_txt, "2"),
            "in_scope": section_block(req_txt, "3.1"),
            "entities": section_block(req_txt, "5.1"),
            "formats": section_block(req_txt, "5.2"),
            "glossary": section_block(req_txt, "8"),
        },
        "provenance": provenance,
    }
    if stage == "design":
        out["design_elements"] = parse_design_elements(spec_txt)
        out["spec_design_sections"] = parse_spec_design_sections(spec_txt)
    return out


def _gate_trail(state: dict) -> list[str]:
    """Human-readable gate trail from STATE.json approvals + mechval."""
    gates = []
    ua = state.get("user_approval") or {}
    if ua.get("decision") == "APPROVED":
        gates.append(f"user gate: APPROVED {ua.get('at', '')}".strip())
    mv = state.get("mechval") or {}
    if mv:
        last = max(mv.items(), key=lambda kv: kv[1].get("cycle", 0))
        gates.append(f"mechval final: {last[1].get('result')} (cycle {last[1].get('cycle')})")
    gates.append(f"cold-audit: {state.get('verdict', '?')}")
    return gates
