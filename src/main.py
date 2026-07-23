"""Backward-compatibility shim for the legacy `python src/main.py` entry point.

Deprecated: use `x-use run` or `python -m xuse.orchestrator` instead.
Scheduled for removal no earlier than v2.1.
"""
import os
import runpy
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print(
    "DeprecationWarning: 'python src/main.py' is a legacy entry point. "
    "Use 'x-use run' (or 'python -m xuse.orchestrator') instead. "
    "This shim will be removed no earlier than v2.1.",
    file=sys.stderr,
)

runpy.run_module("xuse.orchestrator", run_name="__main__")
