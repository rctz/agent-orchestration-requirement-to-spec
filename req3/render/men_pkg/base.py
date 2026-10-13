"""base.py — the interface every output converter implements.

A converter turns a PARSED canonical project (dicts from canonical.py)
into named files in the consumer's machine format. Rules (see README):

- deterministic pure code, no LLM, no network, no clock;
- every target field is mapped EXPLICITLY — missing source data raises
  FieldGap at convert time with a precise message, never silently drops;
- output must be stable: same input dicts -> byte-identical bytes.
"""
from __future__ import annotations

from dataclasses import dataclass


class FieldGap(Exception):
    """Canonical artifacts lack data the target format requires.

    Raised while BUILDING the field map (dev time, ideally) or at convert
    time. Carries: target field, why it is needed, what is missing.
    """


@dataclass
class ConvertedFile:
    filename: str      # e.g. "spec.json" — exactly what the consumer expects
    content: bytes     # serialized, deterministic (sorted keys where JSON)
    media_type: str    # e.g. "application/json"


class Converter:
    """Subclass + @register in a sibling module. One class = one format."""

    #: unique format name the caller uses in options.output_format
    name: str = ""
    #: one-line human description shown in errors / docs
    description: str = ""

    def convert(self, project: dict, options: dict | None = None) -> list[ConvertedFile]:
        """project = ParsedProject dict (shape defined in canonical.py).

        options = caller-supplied values for consumer-specific fields the
        canonical model lacks (e.g. ticket_key, safety_tier). Adapters must
        treat options as OPTIONAL and document their defaults — never
        require the caller to know a format's internals.

        Returns the full file set for this format. MUST be pure:
        no filesystem writes, no side effects — the gateway attaches the
        returned files as artifacts.
        """
        raise NotImplementedError

    # -- helper available to all converters -----------------------------
    @staticmethod
    def require(project: dict, *path: str) -> object:
        """Fetch project[field][sub][...] or raise FieldGap with the path.

        Use for every target field that has a canonical source, so a
        pipeline change shows up as a named gap instead of a KeyError.
        """
        node: object = project
        walked: list[str] = []
        for key in path:
            walked.append(str(key))
            if not isinstance(node, dict) or key not in node:
                raise FieldGap(
                    f"canonical project has no {'.'.join(walked)} — "
                    f"needed by output_format '{type(self).name}'")
            node = node[key]
        return node
