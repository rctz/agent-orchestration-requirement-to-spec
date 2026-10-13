"""men — full Men's orchestrator SPI: both stages in one format name.

Men's orchestrator consumes TWO input packages at two pipeline pauses:

  stage 'requirement' (req-lab AWAIT_USER_APPROVAL, requirements final):
      requirement.json + spec.md          (user confirms requirements)
  stage 'design'      (req-lab COMPLETE, spec APPROVED):
      plan.md + traceability.json         (validate + hand to implementor)

Callers request `options.output_format: "men"`; the gateway/export tool
selects the stage from the workspace phase (see _stage()). Both men-spi
and men-plan remain independently selectable for single-stage consumers.
"""
from __future__ import annotations

from .base import ConvertedFile, Converter, FieldGap
from . import register   # noqa: F401
from .men_plan import MenPlan
from .men_spi import MenSpi


def _stage(project: dict) -> str:
    """Design stage iff the canonical parse carried design elements."""
    return "design" if project.get("design_elements") else "requirement"


@register
class Men(Converter):
    name = "men"
    description = ("Men's orchestrator full SPI: requirement stage → "
                   "requirement.json + spec.md; design stage → plan.md + "
                   "traceability.json (auto-selected by workspace phase)")

    FIELD_MAP = {
        "stage=requirement": "requirement.json + spec.md (via MenSpi)",
        "stage=design":      "plan.md + traceability.json (via MenPlan)",
    }

    def __init__(self):
        self._spi = MenSpi()
        self._plan = MenPlan()

    def convert(self, project: dict, options: dict | None = None) -> list[ConvertedFile]:
        options = options or {}
        for key in ("requirements", "provenance"):
            self._require(project, key)
        stage = _stage(project)
        if stage == "design":
            return self._plan.convert(project, options)
        return self._spi.convert(project, options)

    @staticmethod
    def _require(project: dict, *path: str):
        node = project
        walked = []
        for key in path:
            walked.append(str(key))
            if not isinstance(node, dict) or key not in node:
                raise FieldGap(
                    f"canonical project has no {'.'.join(walked)} — "
                    f"needed by output_format 'men'")
            node = node[key]
        return node
