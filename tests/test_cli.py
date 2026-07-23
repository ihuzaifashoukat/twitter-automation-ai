"""CLI contract tests (Typer CliRunner): --help lists the four commands,
`run` validates --pipeline/--account with exit code 2, and `doctor` prints
PASS/FAIL/SKIP rows with a non-zero exit when any check fails.

Orchestrator and doctor internals are mocked — no browser, no network.
"""
import pytest
from typer.testing import CliRunner

import xuse.doctor as doctor_module
import xuse.orchestrator as orchestrator_module
from xuse.cli import app

runner = CliRunner()


# --- --help ------------------------------------------------------------------


def test_help_lists_all_commands():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    for command in ("run", "init", "mcp", "doctor"):
        assert command in result.output


# --- run ---------------------------------------------------------------------


def test_run_rejects_unknown_pipeline_with_exit_2():
    result = runner.invoke(app, ["run", "--pipeline", "bogus"])
    assert result.exit_code == 2
    assert "bogus" in result.output
    for name in (
        "competitor_reposts",
        "keyword_replies",
        "keyword_retweets",
        "likes",
        "content_curation",
        "community_engagement",
    ):
        assert name in result.output


def test_run_rejects_unknown_account_with_exit_2(monkeypatch):
    class FakeOrchestrator:
        def __init__(self):
            self.accounts_data = [{"account_id": "real_acc", "is_active": True}]
            self.global_settings = {}

        async def run(self):  # pragma: no cover - must never be reached
            raise AssertionError("orchestrator.run() should not execute for an unknown account")

    monkeypatch.setattr(orchestrator_module, "TwitterOrchestrator", FakeOrchestrator)

    result = runner.invoke(app, ["run", "--account", "ghost"])
    assert result.exit_code == 2
    assert "ghost" in result.output
    assert "real_acc" in result.output  # available accounts are listed


# --- doctor ------------------------------------------------------------------


def _stub_doctor_checks(monkeypatch, checks_by_func):
    for func_name, checks in checks_by_func.items():
        monkeypatch.setattr(doctor_module, func_name, lambda *a, _c=checks, **k: list(_c))


def test_doctor_failing_checks_exit_nonzero_and_print_status_rows(monkeypatch):
    Check = doctor_module.Check
    _stub_doctor_checks(monkeypatch, {
        "_check_config_files": [Check("config/settings.json", "PASS", "loaded")],
        "_check_browser": [Check("browser:chrome", "FAIL", "no chrome binary found", "install chrome")],
        "_check_cookies": [Check("cookies", "SKIP", "no accounts configured")],
        "_check_llm_keys": [Check("llm:OpenAI", "PASS", "key from env:OPENAI_API_KEY")],
        "_check_proxies": [Check("proxy", "SKIP", "no per-account proxies configured")],
    })

    result = runner.invoke(app, ["doctor"])
    assert result.exit_code == 1
    assert "PASS" in result.output
    assert "FAIL" in result.output
    assert "SKIP" in result.output
    assert "browser:chrome" in result.output


def test_doctor_all_passing_exits_zero(monkeypatch):
    Check = doctor_module.Check
    _stub_doctor_checks(monkeypatch, {
        "_check_config_files": [Check("config/settings.json", "PASS", "loaded")],
        "_check_browser": [Check("browser:chrome", "PASS", "/usr/bin/chrome")],
        "_check_cookies": [Check("cookies", "SKIP", "no accounts configured")],
        "_check_llm_keys": [Check("llm:OpenAI", "PASS", "key from env:OPENAI_API_KEY")],
        "_check_proxies": [Check("proxy", "SKIP", "no per-account proxies configured")],
    })

    result = runner.invoke(app, ["doctor"])
    assert result.exit_code == 0
    assert "All checks passed" in result.output
