"""x-use MCP server package.

FastMCP-based (MCP Python SDK v1.x) stdio server exposing the engine as nine
tools with draft mode (default on) and a lazy, warm per-account browser pool.

- ``server.py``      — FastMCP app, server factory, stdio entry point
- ``tools.py``       — tool helpers, read-only tools, approve_draft, registrar
- ``write_tools.py`` — post_tweet, generate_and_post, reply_to_tweet, run_cycle
- ``engage.py``      — engage tool (analyzer-gated like/retweet)
- ``executor.py``    — shared context, pacing, dedup, metrics, error contract
- ``actions.py``     — browser/LLM executors used by direct mode and approvals
- ``drafts.py``      — draft store (brand-safety gate)
- ``sessions.py``    — lazy per-account browser session pool
"""

from .server import create_server, main, shutdown

__all__ = ["create_server", "main", "shutdown"]
