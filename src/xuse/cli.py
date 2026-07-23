"""x-use command line interface (Phase 1 — see ROADMAP.md)."""
import runpy

import typer

app = typer.Typer(
    help="x-use — browser-native AI agents for X (Twitter).",
    no_args_is_help=True,
)


@app.command()
def run(
    account: str = typer.Option(None, help="Run a single account only (not wired yet)."),
    pipeline: str = typer.Option(None, help="Run a single pipeline only (not wired yet)."),
):
    """Run automation cycles (legacy orchestrator)."""
    if account or pipeline:
        typer.echo("Note: --account/--pipeline filtering is not wired yet; running all active accounts.")
    runpy.run_module("xuse.orchestrator", run_name="__main__")


@app.command()
def init():
    """Interactive setup wizard (coming in Phase 1)."""
    typer.echo("Not yet implemented — coming in Phase 1 (see ROADMAP.md).")


@app.command()
def mcp():
    """Start the MCP server (coming in Phase 1)."""
    typer.echo("Not yet implemented — coming in Phase 1 (see ROADMAP.md).")


@app.command()
def doctor():
    """Environment checks: browser, cookies, LLM keys, proxies (coming in Phase 1)."""
    typer.echo("Not yet implemented — coming in Phase 1 (see ROADMAP.md).")
