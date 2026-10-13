"""men_spi — FORMAT #1: Men's orchestrator SPI bundle (requirement.json + spec.md).

Target (from Men's orchestrator_expected_input.zip, 2026-09-21):
  requirement.json — ticket_key, spec_version, title, safety_tier,
      safety_rationale, acceptance_criteria[{id,text,risk_flags}],
      out_of_scope[], confidence, risk_flags[]
  spec.md — speckit-style layout carrying req-lab content verbatim.

plan.md is deliberately NOT emitted: Men's own sample declares plan.md as
the output of HIS Design stage (its Input header = spec.md). We stop at
spec.md — producing plan.md would duplicate his stage.

GAP FIELDS (design doc §7, blocking questions Q1–Q4 with Men):
  ticket_key / safety_tier / safety_rationale / confidence have no req-lab
  source. They come from caller options at start time; absent options fall
  back to the documented defaults below. Never invented silently: the
  provenance block records which values were defaulted.

Deterministic: sorted keys, LF newlines, single trailing newline. Same
ParsedProject → byte-identical output.
"""
from __future__ import annotations

import json
import re

from .base import ConvertedFile, Converter, FieldGap
from . import canonical  # noqa: F401  (parse() feeds this adapter)
from . import register   # noqa: F401  (decorator enrolls this class)


DEFAULT_TICKET_PREFIX = "REQ2"          # → REQ2-<n> if caller gave nothing
DEFAULT_SAFETY_TIER = "normal"
DEFAULT_CONFIDENCE = 1.0


def _vnum(version_str: str) -> int:
    # v2.2 list headers may carry suffixes: "v13 (DONE)" — take the leading vN.
    m = re.match(r"[vV]?(\d+)\b", version_str.strip())
    if not m:
        raise FieldGap(f"cannot turn requirements version {version_str!r} "
                       f"into an integer spec_version")
    return int(m.group(1))


def _trunc(s: str, n: int) -> str:
    """Cut at n chars but back off to a word boundary — never slice a token
    like REQ-014 into 'REQ-0' (found on real csv2js data)."""
    if len(s) <= n:
        return s
    return re.sub(r"\s*\S+$", "", s[:n]) + " …"


@register
class MenSpi(Converter):
    name = "men-spi"
    description = ("Men's orchestrator SPI: requirement.json + spec.md "
                   "(plan.md is Men's own Design-stage output)")

    #: required target fields → how they are filled. Every REQUIRED consumer
    #: field gets a line so a pipeline change shows up as a named gap.
    FIELD_MAP = {
        "requirement.json:ticket_key":        "options.ticket_key | default REQ2-<spec_version>",
        "requirement.json:spec_version":      "provenance.requirements_version (int)",
        "requirement.json:title":             "first sentence of intake goal | options.title",
        "requirement.json:safety_tier":       "options.safety_tier | default 'normal'",
        "requirement.json:safety_rationale":  "options.safety_rationale | derived from verdict",
        "requirement.json:acceptance_criteria": "requirements[].acceptance (verbatim)",
        "requirement.json:out_of_scope":      "out_of_scope bullets (verbatim)",
        "requirement.json:confidence":        "options.confidence | formula from verdict+gates",
        "requirement.json:risk_flags":        "[] at COMPLETE (0 open questions by C12)",
        "spec.md":                            "speckit layout, content verbatim from canonical",
    }

    def convert(self, project: dict, options: dict | None = None) -> list[ConvertedFile]:
        options = options or {}
        p = project
        self._require(p, "requirements")
        self._require(p, "out_of_scope")
        self._require(p, "provenance")

        defaults_used: list[str] = []

        # ---- requirement.json -------------------------------------------
        rv = str(self._require(p["provenance"], "requirements_version"))
        spec_version = _vnum(rv)

        ticket_key = options.get("ticket_key") or f"{DEFAULT_TICKET_PREFIX}-{spec_version}"
        if "ticket_key" not in options:
            defaults_used.append("ticket_key")

        safety_tier = options.get("safety_tier") or DEFAULT_SAFETY_TIER
        if "safety_tier" not in options:
            defaults_used.append("safety_tier")

        if options.get("safety_rationale"):
            safety_rationale = options["safety_rationale"]
        else:
            verdict = p.get("verdict") or "READY"
            safety_rationale = (f"Derived by req-lab export: verdict {verdict}; "
                                f"no auth/payments/PII flags exist in the req-lab "
                                f"artifact set — classify manually if uncertain.")
            defaults_used.append("safety_rationale")

        acs = []
        for i, r in enumerate(p["requirements"], 1):
            text = r.get("acceptance") or r.get("body")
            if not text:
                raise FieldGap(f"requirement {r['id']} has neither acceptance nor body")
            # EXACTLY the consumer's AC shape — {id, text, risk_flags} only.
            # AC↔REQ traceability lives in spec.md's Traceability table, which
            # ships in the same package (self-contained, no external refs).
            acs.append({
                "id": f"AC-{i}",
                "text": text,
                "risk_flags": [],
            })

        if "confidence" in options:
            confidence = float(options["confidence"])
        else:
            # agreed-formula placeholder (design doc §7 Q4): 1.0 iff READY +
            # zero open questions — which COMPLETE guarantees; advisory rows
            # are recorded in risk_flags instead of shaving confidence.
            confidence = 1.0 if p.get("verdict") == "READY" else 0.5

        req_json = {
            "ticket_key": ticket_key,
            "spec_version": spec_version,
            "title": options.get("title") or self._title_from(p),
            "safety_tier": safety_tier,
            "safety_rationale": safety_rationale,
            "acceptance_criteria": acs,
            "out_of_scope": list(p["out_of_scope"]),
            "confidence": confidence,
            "risk_flags": [],
        }
        rj_bytes = (json.dumps(req_json, indent=2, ensure_ascii=False,
                               sort_keys=False) + "\n").encode("utf-8")

        # ---- spec.md -----------------------------------------------------
        spec_md = self._render_spec_md(p, req_json)
        sm_bytes = spec_md.encode("utf-8")

        return [
            ConvertedFile("requirement.json", rj_bytes, "application/json"),
            ConvertedFile("spec.md", sm_bytes, "text/markdown"),
        ]

    # ---- helpers ---------------------------------------------------------

    @staticmethod
    def _title_from(p: dict) -> str:
        iv = p.get("intake_verbatim") or ""
        first = re.split(r"(?<=[.!?])\s", iv.strip(), 1)[0]
        return (first or p["provenance"]["slug"])[:140]

    def _render_spec_md(self, p: dict, req_json: dict) -> str:
        prov = p["provenance"]
        L: list[str] = []
        L.append(f"# Feature Specification: {req_json['title']}")
        L.append("")
        L.append(f"**Feature Branch**: `{prov['slug'][:60]}`")
        L.append("")
        created = (prov.get("complete_at") or "")[:10] or "n/a"
        L.append(f"**Created**: {created}")
        L.append("")
        if prov.get("complete_at"):
            L.append(f"**Status**: Approved (req-lab verdict {prov.get('verdict')})")
        else:
            # requirement-stage export (user approval gate): the spec is not
            # approved yet — the user is confirming the REQUIREMENT set.
            L.append("**Status**: Requirements final — awaiting user approval "
                     "(requirement-stage export)")
        L.append("")
        L.append(f"**Input**: User description: {p['intake_verbatim']}")
        L.append("")

        # Clarifications — verbatim Q/A from user decisions
        L.append("## Clarifications")
        L.append("")
        user_ds = [d for d in p["decisions"] if d["owner"] == "user"]
        if user_ds:
            L.append(f"### User answers ({len(user_ds)} decisions, owner=user)")
            L.append("")
            for d in user_ds:
                L.append(f"- **{d['id']}**: {d['decision']} — status {d['status']}")
            L.append("")
        L.append("All questions answered before approval; none pending.")
        L.append("")

        # Goal & success condition (§1, verbatim; source section number kept
        # so plan.md's "spec §x.y" DE references resolve inside this package)
        if p.get("sections", {}).get("goal"):
            L.append("## Goal & Success Condition (§1)")
            L.append("")
            L.append(p["sections"]["goal"])
            L.append("")

        # Users and roles (§2, verbatim)
        if p.get("sections", {}).get("users"):
            L.append("## Users & Roles (§2)")
            L.append("")
            L.append(p["sections"]["users"])
            L.append("")

        # Scope (§3.1 in-scope bullets, verbatim; out-of-scope has its own section)
        if p.get("sections", {}).get("in_scope"):
            L.append("## In Scope (§3.1)")
            L.append("")
            L.append(p["sections"]["in_scope"])
            L.append("")

        # Requirements — FR bullets
        L.append("## Requirements *(mandatory)*")
        L.append("")
        L.append("### Functional Requirements")
        L.append("")
        for r in p["requirements"]:
            if r["kind"] != "FR":
                continue
            L.append(f"- **{r['id']}**: {r['title']}. {r['body']}")
        L.append("")
        L.append("### Non-Functional Requirements")
        L.append("")
        for r in p["nfrs"]:
            L.append(f"- **{r['id']}**: {r['title']}. {r['body']}")
        L.append("")

        # Key Entities (§5.1, verbatim)
        if p.get("sections", {}).get("entities"):
            L.append("### Key Entities (§5.1)")
            L.append("")
            L.append(p["sections"]["entities"])
            L.append("")

        # Data & Integration formats (§5.2, verbatim — includes the output
        # byte contract, which is normative for any implementor)
        if p.get("sections", {}).get("formats"):
            L.append("### Data Formats (§5.2)")
            L.append("")
            L.append(p["sections"]["formats"])
            L.append("")

        # Acceptance scenarios from ACs (declarative verbatim)
        L.append("## User Scenarios & Testing *(mandatory)*")
        L.append("")
        for i, ac in enumerate(req_json["acceptance_criteria"], 1):
            L.append(f"### Scenario {i} — {ac['id']}")
            L.append("")
            L.append(ac["text"])
            L.append("")

        # Key entities → skip if not in canonical (thin model: only if present)
        # Success criteria
        L.append("## Success Criteria *(mandatory)*")
        L.append("")
        L.append("### Measurable Outcomes")
        L.append("")
        for i, ac in enumerate(req_json["acceptance_criteria"], 1):
            L.append(f"- **SC-{i:03d}**: {ac['text']}")
        L.append("")

        # Assumptions from user decisions
        L.append("## Assumptions")
        L.append("")
        designer_ds = [d for d in p["decisions"] if d["owner"] != "user"]
        for d in designer_ds:
            L.append(f"- {d['id']}: {d['decision']}")
        L.append("")

        # Traceability block — self-contained: references only AC ids and
        # REQ/NFR ids that live in THIS package (spec.md + requirement.json)
        L.append("## Traceability")
        L.append("")
        L.append("| AC | source REQ/NFR | designed in | test | evidence |")
        L.append("|---|---|---|---|---|")
        trace = {t["id"]: t for t in p["traceability"]}
        for i, r in enumerate(p["requirements"], 1):
            t = trace.get(r["id"], {})
            L.append(f"| AC-{i} | {r['id']} — {r['title']} | {t.get('designed_in', '—')} | "
                     f"{t.get('test', '—')} | {t.get('evidence', '—')} |")
        L.append("")

        L.append("## Out of Scope")
        L.append("")
        for o in p["out_of_scope"]:
            L.append(f"- {o}")
        L.append("")

        # Glossary (§8, verbatim — normative definitions incl. line-counting basis)
        if p.get("sections", {}).get("glossary"):
            L.append("## Glossary (§8)")
            L.append("")
            L.append(p["sections"]["glossary"])
            L.append("")

        L.append("## Provenance")
        L.append("")
        L.append(f"Machine-generated by req-lab v2 converter `men-spi`. This package "
                 f"is self-contained and DERIVED from the req-lab v2 workspace "
                 f"`{prov['slug']}` (canonical markdown bundle is authoritative).")
        L.append(f"- requirements: {prov['requirements_version']} (APPROVED "
                 f"{(prov.get('user_approval') or {}).get('at', 'n/a').strip()})")
        L.append(f"- spec: {prov['spec_version']} (APPROVED)")
        L.append(f"- gates: {'; '.join(prov.get('gates', []))}")
        L.append("")
        return "\n".join(L)

    @staticmethod
    def _require(project: dict, *path: str):
        node = project
        walked = []
        for key in path:
            walked.append(str(key))
            if not isinstance(node, dict) or key not in node:
                raise FieldGap(
                    f"canonical project has no {'.'.join(walked)} — "
                    f"needed by output_format 'men-spi'")
            node = node[key]
        return node
