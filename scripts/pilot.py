#!/usr/bin/env python3
"""Run the v2-benchmark pilot (implemented in M10, plan §3).

Replays every ~/hermes-workspaces/req-lab-v2 project that has an intake
prompt (appendix/00-intake.md, verbatim), with scripted answers from
pilot/answers/, collects the design §12 metrics per project and writes
pilot/report.md with a pass/fail verdict per bar.
"""
