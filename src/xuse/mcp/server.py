"""x-use MCP server — official MCP Python SDK v1.x ``FastMCP`` over stdio.

Exposes the engine as nine tools (see ``tools.py``) with draft mode on by
default and a lazy, warm per-account browser pool. Run directly::

    python -m xuse.mcp.server

or via the CLI: ``x-use mcp``.

Config (all optional, additive — ``config/settings.json``)::

    "mcp": {
        "draft_mode": true,                    // default ON
        "session_idle_timeout_seconds": 600,   // warm-session reap threshold
        "cold_start_timeout_seconds": 180,     // browser start + cookie login
        "drafts_file": "data/drafts.jsonl"     // draft persistence
    }

SDK note: pinned to ``mcp>=1,<2``. The v2 alpha renames FastMCP to
``MCPServer`` (``mcp.server.mcpserver``) — do not migrate until v2 is stable.
"""
import asyncio
import logging
import sys
from typing import Optional, Union
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from xuse.core.config_loader import ConfigLoader, PROJECT_ROOT

from . import tools as _tools
from .drafts import DraftStore
from .executor import Ctx
from .sessions import SessionPool

logger = logging.getLogger(__name__)


class _StderrProxy:
    """Forward stray text writes (print, progress bars) to stderr while
    exposing the real stdout ``.buffer`` — the MCP stdio transport wraps that
    buffer directly when ``server.run()`` starts, so protocol bytes still go
    to genuine stdout and everything else lands on stderr."""

    def __init__(self, real_stdout, stderr):
        self._stderr = stderr
        self.buffer = real_stdout.buffer

    def write(self, data):
        return self._stderr.write(data)

    def flush(self):
        return self._stderr.flush()

    def __getattr__(self, name):
        return getattr(self._stderr, name)


def _enforce_stdio_stdout_hygiene() -> None:
    """Keep stdout reserved for JSON-RPC. The engine's root logger is
    configured (at import time, by xuse.orchestrator/publisher) with a
    StreamHandler bound to the real sys.stdout, and utils.progress.Progress
    writes bars via sys.stdout.write — both would corrupt the stdio
    transport. Re-point handlers at stderr and proxy remaining sys.stdout
    writes there too."""
    real_stdout = sys.stdout
    for handler in logging.getLogger().handlers:
        if isinstance(handler, logging.StreamHandler) and getattr(handler, "stream", None) is real_stdout:
            handler.setStream(sys.stderr)
    sys.stdout = _StderrProxy(real_stdout, sys.stderr)  # type: ignore[assignment]

SERVER_NAME = "x-use"
SERVER_INSTRUCTIONS = (
    "Browser-native automation for X (Twitter): post, reply, search, and engage "
    "across multiple accounts. Write tools run in DRAFT MODE by default — they "
    "return a reviewable draft and change nothing until you call approve_draft "
    "with the returned draft_id. Read-only tools (list_accounts, get_metrics) "
    "never start a browser."
)


def create_server(
    config_loader: Optional[ConfigLoader] = None,
    *,
    draft_mode: Optional[bool] = None,
    session_pool: Optional[SessionPool] = None,
    draft_store: Optional[DraftStore] = None,
) -> FastMCP:
    """Build the FastMCP server. All dependencies are injectable so contract
    tests can supply a custom config, a fake-browser pool, and a tmp draft
    store without touching real browsers or data files."""
    config_loader = config_loader or ConfigLoader()
    mcp_cfg = config_loader.get_setting("mcp", {}) or {}
    if not isinstance(mcp_cfg, dict):
        mcp_cfg = {}
    if draft_mode is None:
        draft_mode = bool(mcp_cfg.get("draft_mode", True))  # default ON
    # NB: explicit `is not None` — DraftStore defines __len__, so an empty
    # store is falsy and `or` would silently discard an injected one.
    pool = session_pool if session_pool is not None else SessionPool(
        config_loader,
        idle_timeout_seconds=float(mcp_cfg.get("session_idle_timeout_seconds", 600)),
        cold_start_timeout_seconds=float(mcp_cfg.get("cold_start_timeout_seconds", 180)),
    )
    store = draft_store if draft_store is not None else DraftStore(
        Path(mcp_cfg["drafts_file"]) if mcp_cfg.get("drafts_file") else PROJECT_ROOT / "data" / "drafts.jsonl"
    )
    ctx = Ctx(
        config_loader=config_loader,
        session_pool=pool,
        draft_store=store,
        draft_mode=draft_mode,
    )
    server = FastMCP(SERVER_NAME, instructions=SERVER_INSTRUCTIONS)
    _tools.register_tools(server, ctx)
    server.xuse_ctx = ctx  # reachable for shutdown hooks and tests
    logger.info(
        "x-use MCP server created (draft_mode=%s, idle_timeout=%ss).",
        ctx.draft_mode,
        pool.idle_timeout_seconds,
    )
    return server


async def shutdown(server: FastMCP) -> None:
    """Close all warm browser sessions (idempotent, never raises)."""
    ctx: Union[Ctx, None] = getattr(server, "xuse_ctx", None)
    if ctx is None:
        return
    try:
        await ctx.session_pool.close_all()
    except Exception:
        logger.exception("Error while closing MCP session pool.")


def main() -> None:
    """Console entry point: run the stdio server until the client disconnects."""
    _enforce_stdio_stdout_hygiene()
    server = create_server()
    try:
        server.run()  # stdio transport; blocks for the server lifecycle
    finally:
        # run() closes its event loop on exit; close browsers on a fresh one.
        try:
            asyncio.run(shutdown(server))
        except Exception:
            logger.exception("MCP server shutdown cleanup failed.")


if __name__ == "__main__":
    main()
