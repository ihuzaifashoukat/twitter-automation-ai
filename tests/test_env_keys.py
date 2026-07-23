"""Tests for LLM API key resolution (xuse.core.llm_service.clients +
xuse.utils.env): environment variables beat settings.json, settings.json is
the fallback when the env var is absent, placeholders are rejected from both
sources, a missing .env file is a no-op, and key values never appear in logs.

No network: client constructors (AsyncOpenAI etc.) do not call out at init.
"""
import logging
import os

import pytest

import xuse.utils.env as env_module
from xuse.core.llm_service import clients as clients_module
from xuse.core.llm_service.clients import _resolve_api_key, initialize_clients

PROVIDER_ENV_VARS = ("OPENAI_API_KEY", "GEMINI_API_KEY", "AZURE_OPENAI_API_KEY")


@pytest.fixture(autouse=True)
def clean_provider_env(monkeypatch):
    """Every test starts with no provider keys in the process environment."""
    for var in PROVIDER_ENV_VARS:
        monkeypatch.delenv(var, raising=False)


@pytest.fixture(autouse=True)
def no_real_dotenv(monkeypatch):
    """Isolate initialize_clients from any real project-root .env file."""
    monkeypatch.setattr(clients_module, "load_env", lambda: None)


@pytest.fixture
def fresh_dotenv_loader(monkeypatch, tmp_path):
    """Point load_env at a tmp project root and reset its one-shot flag."""
    monkeypatch.setattr(env_module, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(env_module, "_loaded", False)
    return tmp_path


# --- _resolve_api_key precedence -------------------------------------------


def test_env_var_beats_settings_json(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-env-secret-AAA")
    value, source = _resolve_api_key("openai_api_key", "sk-config-secret-BBB")
    assert value == "sk-env-secret-AAA"
    assert source == "env var OPENAI_API_KEY"


def test_settings_json_is_fallback_when_env_absent():
    value, source = _resolve_api_key("openai_api_key", "sk-config-secret-BBB")
    assert value == "sk-config-secret-BBB"
    assert source == "settings.json"


def test_blank_env_var_falls_through_to_settings_json(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "   ")
    value, source = _resolve_api_key("openai_api_key", "sk-config-secret-BBB")
    assert value == "sk-config-secret-BBB"
    assert source == "settings.json"


def test_no_key_anywhere_resolves_to_none():
    value, source = _resolve_api_key("openai_api_key", None)
    assert value is None
    assert source == "none"


# --- placeholder rejection from both sources (end to end) -------------------


@pytest.mark.skipif(not clients_module.OPENAI_AVAILABLE, reason="openai SDK not installed")
def test_placeholder_from_env_is_rejected(monkeypatch, make_config_loader):
    monkeypatch.setenv("OPENAI_API_KEY", "YOUR_OPENAI_API_KEY")
    loader = make_config_loader(settings={"api_keys": {}}, accounts=[])
    clients, _, _ = initialize_clients(loader)
    assert clients["openai_client"] is None


@pytest.mark.skipif(not clients_module.OPENAI_AVAILABLE, reason="openai SDK not installed")
def test_placeholder_from_settings_json_is_rejected(make_config_loader):
    loader = make_config_loader(
        settings={"api_keys": {"openai_api_key": "YOUR_OPENAI_API_KEY"}}, accounts=[]
    )
    clients, _, _ = initialize_clients(loader)
    assert clients["openai_client"] is None


# --- end-to-end precedence through initialize_clients -----------------------


@pytest.mark.skipif(not clients_module.OPENAI_AVAILABLE, reason="openai SDK not installed")
def test_initialize_clients_uses_env_key_over_config(monkeypatch, make_config_loader):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-env-secret-AAA")
    loader = make_config_loader(
        settings={"api_keys": {"openai_api_key": "sk-config-secret-BBB"}}, accounts=[]
    )
    clients, _, _ = initialize_clients(loader)
    assert clients["openai_client"] is not None
    assert clients["openai_client"].api_key == "sk-env-secret-AAA"


@pytest.mark.skipif(not clients_module.OPENAI_AVAILABLE, reason="openai SDK not installed")
def test_initialize_clients_falls_back_to_config_key(make_config_loader):
    loader = make_config_loader(
        settings={"api_keys": {"openai_api_key": "sk-config-secret-BBB"}}, accounts=[]
    )
    clients, _, _ = initialize_clients(loader)
    assert clients["openai_client"] is not None
    assert clients["openai_client"].api_key == "sk-config-secret-BBB"


# --- .env loading ------------------------------------------------------------


def test_missing_dotenv_is_a_noop(fresh_dotenv_loader, monkeypatch):
    monkeypatch.delenv("XUSE_TEST_SENTINEL", raising=False)
    env_module.load_env()  # must not raise, must not change the environment
    assert os.environ.get("XUSE_TEST_SENTINEL") is None
    env_module.load_env()  # idempotent second call
    assert os.environ.get("XUSE_TEST_SENTINEL") is None


def test_existing_dotenv_is_loaded(fresh_dotenv_loader, monkeypatch):
    monkeypatch.delenv("XUSE_TEST_SENTINEL", raising=False)
    (fresh_dotenv_loader / ".env").write_text("XUSE_TEST_SENTINEL=loaded-123\n", encoding="utf-8")
    env_module.load_env()
    assert os.environ.get("XUSE_TEST_SENTINEL") == "loaded-123"


def test_dotenv_never_overrides_process_env(fresh_dotenv_loader, monkeypatch):
    monkeypatch.setenv("XUSE_TEST_SENTINEL", "from-process-env")
    (fresh_dotenv_loader / ".env").write_text("XUSE_TEST_SENTINEL=from-dotenv\n", encoding="utf-8")
    env_module.load_env()
    assert os.environ.get("XUSE_TEST_SENTINEL") == "from-process-env"


# --- key values never reach the logs ----------------------------------------


@pytest.mark.skipif(not clients_module.OPENAI_AVAILABLE, reason="openai SDK not installed")
def test_key_values_never_appear_in_logs(monkeypatch, make_config_loader, caplog):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-SENTINEL-ENV-999")
    loader = make_config_loader(
        settings={"api_keys": {"gemini_api_key": "AIza-SENTINEL-CONFIG-888"}}, accounts=[]
    )
    with caplog.at_level(logging.INFO):
        initialize_clients(loader)
    assert "sk-SENTINEL-ENV-999" not in caplog.text
    assert "AIza-SENTINEL-CONFIG-888" not in caplog.text
    # The safe-to-log source label is present instead.
    assert "env var OPENAI_API_KEY" in caplog.text
