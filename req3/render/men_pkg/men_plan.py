"""men_plan — design-stage export for Men's orchestrator: plan.md + traceability.json.

Mapping from req-lab's APPROVED spec (Men's plan.md sections → req-lab source):

  Men's plan.md section      req-lab spec source (deterministic)
  -----------------------    ----------------------------------------
  header (Branch/Input)      slug / intake verbatim / spec version
  Summary                    spec §1.1 Goal and success condition
  Technical Context          spec §4 module design (language, storage,
                             testing facts are quoted verbatim from the
                             entities/formats/§9 NFR sections)
  Design Elements (DE-n)     spec §4.x subsections — ONE DE per module
                             section, body verbatim
  Notes on Clarifications    decision register rows owned by user
  (Constitution/Complexity)  deliberately omitted — Men's internal gate;
                             req-lab has its own mechval/adv/cold-audit
                             trail recorded in spec.md's Provenance

traceability.json:
  map[]                 AC-n → DE ids   (from §1.2 requirement map:
                         REQ → designed-in §4.x, joined with AC ↔ REQ)
  design_elements[]     DE-n → backed_by ACs (inverse map), ref into plan.md
  confidence/risk_flags from verdict + gates (same formula as men-spi)

DE ids are positional (DE-1..DE-n over §4.1..§4.n) and therefore STABLE for
a given spec version — §4 numbering is part of the spec contract.
"""
from __future__ import annotations

import json
import re

from .base import ConvertedFile, Converter, FieldGap
from . import canonical  # noqa: F401
from . import register   # noqa: F401

from .men_spi import _vnum


@register
class MenPlan(Converter):
    name = "men-plan"
    description = ("Men's orchestrator design stage: plan.md + traceability.json "
                   "(from the APPROVED req-lab spec; complements men-spi)")

    FIELD_MAP = {
        "plan.md:Summary":              "spec §1.1 goal & success condition",
        "plan.md:Technical Context":    "spec §3 entities + §5.2 formats + §9 NFRs",
        "plan.md:Design Elements":      "spec §4.x module sections (verbatim)",
        "plan.md:Notes":                "decision register (owner=user) verbatim",
        "traceability.json:map":        "AC-n ↔ DE-n via §1.2 requirement map",
        "traceability.json:design_elements": "inverse of map + plan.md refs",
        "traceability.json:confidence": "verdict formula (READY→1.0)",
        "traceability.json:risk_flags": "gates + open advisory notes",
    }

    def convert(self, project: dict, options: dict | None = None) -> list[ConvertedFile]:
        options = options or {}
        p = project
        for key in ("requirements", "design_elements", "spec_map", "provenance"):
            self._require(p, key)

        # ---- AC ↔ DE mapping: UNION of the spec's own maps --------------
        # §1.2 requirement map (REQ → where designed) + §11 traceability
        # matrix (REQ → designed in). Both name §x.y sections; map those to
        # DE ids. Using the union catches REQs that only one table carries.
        sec_to_de = {de["section"]: de["id"] for de in p["design_elements"]}
        sec_to_de.update({"5.1": sec_to_de.get("5.1", "")})  # 5.1 handled below
        where_by_id: dict[str, set[str]] = {}
        for row in p["spec_map"]:
            where_by_id.setdefault(row["id"], set()).add(row["where"])
        for row in p["traceability"]:
            if row["id"] in ("Impl detail",):
                continue
            where_by_id.setdefault(row["id"], set()).add(row["designed_in"])
        # §5.1/§9 DEs are section-level; find their REQs via body mentions
        for de in p["design_elements"]:
            if de["section"] in ("5.1", "9"):
                for r in p["requirements"]:
                    if r["id"] in de["body"]:
                        where_by_id.setdefault(r["id"], set()).add(de["section"])

        ac_to_des: dict[str, list[str]] = {}
        de_to_acs: dict[str, list[str]] = {de["id"]: [] for de in p["design_elements"]}
        map_rows = []
        for i, r in enumerate(p["requirements"], 1):
            ac_id = f"AC-{i}"
            des = []
            for where in where_by_id.get(r["id"], ()):
                for sec in re.findall(r"\d+(?:\.\d+)?", where):
                    de = sec_to_de.get(sec)
                    if de and de not in des:
                        des.append(de)
            # body-mention fallback: a DE whose text names this REQ
            # implements it (architecture sections like §2.3 ADRs cite
            # their REQ ids inline — deterministic, not invented). The
            # TITLE counts too: ros2 §5.7 "Strict-deserialization walk
            # (REQ-012)" carries the only citation in the heading.
            if not des:
                for de in p["design_elements"]:
                    if re.search(r"\b" + re.escape(r["id"]) + r"\b",
                                 de["title"] + "\n" + de["body"]):
                        des.append(de["id"])
            des.sort(key=lambda d: int(d.split("-")[1]))
            ac_to_des[ac_id] = des
            for de in des:
                de_to_acs[de].append(ac_id)

        # DE-side fallback: architecture DEs (§2.1/§2.3/§2.4/§7.3...) may
        # cite REQ ids in their bodies without being named in §1.2/§11 —
        # mine those citations so backed_by reflects the spec's own text.
        # A DE with NO REQ citation anywhere (e.g. §2.4 "deliberately
        # absent") stays honestly empty — Men's schema allows [] backed_by.
        for de in p["design_elements"]:
            if de_to_acs[de["id"]]:
                continue
            for i, r in enumerate(p["requirements"], 1):
                if re.search(r"\b" + re.escape(r["id"]) + r"\b",
                             de["title"] + "\n" + de["body"]):
                    ac_id = f"AC-{i}"
                    de_to_acs[de["id"]].append(ac_id)
                    if de["id"] not in ac_to_des[ac_id]:
                        ac_to_des[ac_id].append(de["id"])
                        ac_to_des[ac_id].sort(key=lambda d: int(d.split("-")[1]))

        map_rows = [{"ac_id": f"AC-{i}", "design_elements": ac_to_des[f"AC-{i}"]}
                    for i in range(1, len(p["requirements"]) + 1)]

        # ---- traceability.json ---------------------------------------------
        risk_flags = []
        for t in p.get("traceability", []):
            if t.get("id", "").startswith(("REQ", "NFR", "FR")) and not t.get("test"):
                risk_flags.append(f"{t['id']}: no test layer recorded in spec §11")

        trace = {
            "spec_version": _vnum(p["provenance"]["requirements_version"]),
            "map": map_rows,
            "design_elements": [
                {"id": de["id"],
                 "ref": "plan.md#design-elements",
                 "backed_by": de_to_acs[de["id"]],
                 "justification": (
                     None if de_to_acs[de["id"]] else
                     "spec §" + de["section"] + " records design-boundary "
                     "material (architecture/negative scope); it supports no "
                     "acceptance criterion directly — see plan.md Review & "
                     "Validation Trail")}
                for de in p["design_elements"]
            ],
            "confidence": 1.0 if p.get("verdict") == "READY" else 0.5,
            "risk_flags": risk_flags,
        }
        tj_bytes = (json.dumps(trace, indent=2, ensure_ascii=False) + "\n").encode("utf-8")

        # ---- plan.md --------------------------------------------------------
        plan_md = self._render_plan_md(p, ac_to_des, de_to_acs, options)
        pm_bytes = plan_md.encode("utf-8")

        return [
            ConvertedFile("plan.md", pm_bytes, "text/markdown"),
            ConvertedFile("traceability.json", tj_bytes, "application/json"),
        ]

    # ------------------------------------------------------------------ plan

    def _render_plan_md(self, p: dict, ac_to_des, de_to_acs, options: dict) -> str:
        prov = p["provenance"]
        spec_ver = prov.get("spec_version") or "v?"
        L: list[str] = []
        L.append(f"# Implementation Plan: {self._title(p, options)}")
        L.append("")
        L.append(f"**Branch**: `{prov['slug'][:60]}` | **Date**: "
                 f"{(prov.get('complete_at') or '')[:10] or 'n/a'} | "
                 f"**Spec**: req-lab spec {spec_ver or 'v?'} (APPROVED)")
        L.append("")
        L.append(f"**Input**: Feature specification `spec.md` "
                 f"(spec_version {_vnum(prov['requirements_version'])}, "
                 f"{options.get('ticket_key', prov['slug'])})")
        L.append("")

        # Summary — from the requirements' own goal section (verbatim §1)
        L.append("## Summary")
        L.append("")
        goal = (p.get("sections") or {}).get("goal") or ""
        if goal:
            L.append(goal)
        else:
            L.append(f"(from intake) {p['intake_verbatim']}")
        L.append("")

        # Technical Context — Men's key:value shape. Every line either cites
        # a real req-lab artifact or states honestly that nothing pins it;
        # nothing is invented. Works for ANY req-lab v2 project.
        L.append("## Technical Context")
        L.append("")
        nfrs = p.get("nfrs", [])

        def _nfr(*words: str):
            for n in nfrs:
                if all(w in n["title"].lower() for w in words):
                    return n
            return None

        n = _nfr("runtime") or _nfr("language")
        L.append(f"**Language/Version**: {n['id']} — {n['title']}: {n['body']}"
                 if n else
                 "**Language/Version**: not pinned as a distinct field in the "
                 "req-lab artifacts; see Non-Functional Requirements in spec.md")
        n = _nfr("dependenc")
        L.append(f"**Primary Dependencies**: {n['id']} — {n['title']}: {n['body']}"
                 if n else
                 "**Primary Dependencies**: none recorded — the requirement "
                 "set carries no dependency NFR")
        letters: set[str] = set()
        for t in p.get("traceability", []):
            tm = re.match(r"^T-([A-Z])", t.get("test") or "")
            if tm:
                letters.add(tm.group(1))
        L.append("**Testing**: test suites recorded in the req-lab spec "
                 "traceability matrix: "
                 + (", ".join(f"T-{c}-series" for c in sorted(letters))
                    if letters else "no test ids recorded")
                 + " (tests are specified, not run, at this stage)")
        L.append("**Storage**: not pinned as a distinct field; data entities "
                 "and formats are specified verbatim in spec.md (Key "
                 "Entities, Data Formats)")
        L.append("**Target Platform**: not pinned as a distinct field in the "
                 "req-lab artifacts")
        L.append("**Project Type**: not pinned as a distinct field in the "
                 "req-lab artifacts; see Summary for the deliverable shape")
        n = _nfr("performance")
        L.append(f"**Performance Goals**: {n['id']} — {n['title']}: {n['body']}"
                 if n else
                 "**Performance Goals**: none recorded in the requirement set")
        L.append(f"**Constraints**: out-of-scope commitments are listed "
                 f"verbatim in requirement.json `out_of_scope` "
                 f"({len(p.get('out_of_scope', []))} items) and spec.md's "
                 "Out of Scope section")
        fr_ids = [r["id"] for r in p["requirements"] if r["kind"] == "FR"]
        nfr_ids = [r["id"] for r in p["requirements"] if r["kind"] == "NFR"]
        parts = []
        if fr_ids:
            parts.append(f"{len(fr_ids)} functional ({fr_ids[0]}..{fr_ids[-1]})")
        if nfr_ids:
            parts.append(f"{len(nfr_ids)} non-functional ({nfr_ids[0]}..{nfr_ids[-1]})")
        L.append("**Scale/Scope**: " + ("; ".join(parts) + " — the full list "
                 "is in spec.md's Requirements section" if parts else
                 "no requirements parsed"))
        L.append("")

        # Project Structure — generic: the req-lab spec never prescribes a
        # repository layout; point at the architecture DEs that do exist.
        L.append("## Project Structure")
        L.append("")
        arch = [f"{de['id']} (spec §{de['section']})" for de in p["design_elements"]
                if de["section"].startswith("2.")]
        if arch:
            L.append("The req-lab spec does not prescribe a repository "
                     "layout; its structural design is carried by the "
                     "architecture Design Elements: " + ", ".join(arch) + ".")
        else:
            L.append("The req-lab spec does not prescribe a repository "
                     "layout and carries no architecture section; see the "
                     "Design Elements below for the module design.")
        L.append("")

        # Design Elements — one per spec §4.x, body VERBATIM
        L.append("## Design Elements")
        L.append("")
        for de in p["design_elements"]:
            backs = ", ".join(de_to_acs[de["id"]]) or "—"
            L.append(f"- **{de['id']} — {de['title']}** (spec §{de['section']})")
            L.append("")
            L.append(f"  {de['body']}")
            L.append("")
            L.append(f"  Backs: {backs}")
            L.append("")

        # Notes on Clarifications — user decisions verbatim
        L.append("## Notes on Spec Clarifications")
        L.append("")
        user_ds = [d for d in p["decisions"] if d["owner"] == "user"]
        for d in user_ds:
            L.append(f"- {d['id']}: {d['decision']}")
        L.append("")

        # Review trail
        L.append("## Review & Validation Trail (req-lab)")
        L.append("")
        L.append("This plan is a deterministic re-layout of the APPROVED req-lab "
                 "spec; the authoritative design record is the spec bundle.")
        for g in prov.get("gates", []):
            L.append(f"- {g}")
        L.append("")
        return "\n".join(L)

    @staticmethod
    def _title(p: dict, options: dict) -> str:
        if options.get("title"):
            return options["title"]
        iv = p.get("intake_verbatim") or ""
        first = re.split(r"(?<=[.!?])\s", iv.strip(), 1)[0]
        return (first or p["provenance"]["slug"])[:140]

    @staticmethod
    def _require(project: dict, *path: str):
        node = project
        walked = []
        for key in path:
            walked.append(str(key))
            if not isinstance(node, dict) or key not in node:
                raise FieldGap(
                    f"canonical project has no {'.'.join(walked)} — "
                    f"needed by output_format 'men-plan'")
            node = node[key]
        return node
