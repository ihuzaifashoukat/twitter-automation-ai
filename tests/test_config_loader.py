"""Tests for xuse.core.config_loader.ConfigLoader (pure logic, tmp files only)."""

import json

import pytest

from xuse.core.config_loader import ConfigLoader

from conftest import write_json


SETTINGS = {
    "api_keys": {"openai_api_key": "sk-test-dummy", "gemini_api_key": "gem-test-dummy"},
    "twitter_automation": {
        "media_directory": "data/media",
        "engagement_options": {"like_probability": 0.8, "reply_probability": 0.3},
    },
    "logging": {
        "level": "DEBUG",
        "file_handler": {"enabled": False, "path": "logs/app.log"},
    },
}

ACCOUNTS = [
    {"account_id": "acc_one", "is_active": True},
    {"account_id": "acc_two", "is_active": False},
]


class TestLoading:
    def test_settings_and_accounts_round_trip(self, make_config_loader):
        loader = make_config_loader(settings=SETTINGS, accounts=ACCOUNTS)
        assert loader.get_settings() == SETTINGS
        assert loader.get_accounts_config() == ACCOUNTS

    def test_missing_files_yield_empty_defaults(self, tmp_path):
        loader = ConfigLoader(
            settings_file=tmp_path / "nope_settings.json",
            accounts_file=tmp_path / "nope_accounts.json",
        )
        assert loader.get_settings() == {}
        assert loader.get_accounts_config() == []

    def test_malformed_json_yields_default(self, tmp_path):
        settings_file = tmp_path / "settings.json"
        settings_file.write_text("{ not valid json", encoding="utf-8")
        accounts_file = write_json(tmp_path / "accounts.json", ACCOUNTS)
        loader = ConfigLoader(settings_file=settings_file, accounts_file=accounts_file)
        assert loader.get_settings() == {}
        # The valid file still loads.
        assert loader.get_accounts_config() == ACCOUNTS

    def test_directory_passed_as_file_yields_default(self, tmp_path):
        loader = ConfigLoader(settings_file=tmp_path, accounts_file=tmp_path)
        assert loader.get_settings() == {}
        assert loader.get_accounts_config() == []


class TestDotPathGetters:
    @pytest.fixture
    def loader(self, make_config_loader):
        return make_config_loader(settings=SETTINGS, accounts=ACCOUNTS)

    def test_top_level_and_nested_paths(self, loader):
        assert loader.get_setting("logging.level") == "DEBUG"
        assert loader.get_setting("logging.file_handler.path") == "logs/app.log"
        assert (
            loader.get_setting("twitter_automation.engagement_options.like_probability")
            == 0.8
        )

    def test_missing_key_returns_default(self, loader):
        assert loader.get_setting("does.not.exist") is None
        assert loader.get_setting("does.not.exist", "fallback") == "fallback"

    def test_path_through_non_dict_returns_default(self, loader):
        # 'logging.level' is a string; descending further must not raise.
        assert loader.get_setting("logging.level.deeper", "fallback") == "fallback"

    def test_get_api_key(self, loader):
        assert loader.get_api_key("openai_api_key") == "sk-test-dummy"
        assert loader.get_api_key("missing_service") is None

    def test_twitter_automation_setting(self, loader):
        assert loader.get_twitter_automation_setting("media_directory") == "data/media"
        assert (
            loader.get_twitter_automation_setting("engagement_options.reply_probability")
            == 0.3
        )
        assert loader.get_twitter_automation_setting("missing", 42) == 42

    def test_logging_setting(self, loader):
        assert loader.get_logging_setting("level") == "DEBUG"
        assert loader.get_logging_setting("missing", "INFO") == "INFO"


class TestPrecedenceInputs:
    """ConfigLoader exposes settings and accounts as separate namespaces; the
    per-account > global precedence itself is resolved downstream (orchestrator
    + pydantic models) and covered in test_orchestrator_config.py."""

    def test_account_specific_values_stay_scoped_to_accounts(self, make_config_loader):
        settings = {"twitter_automation": {"action_config": {"max_likes_per_run": 3}}}
        accounts = [{"account_id": "a1", "action_config": {"max_likes_per_run": 9}}]
        loader = make_config_loader(settings=settings, accounts=accounts)

        # Global value visible via settings...
        assert loader.get_setting("twitter_automation.action_config.max_likes_per_run") == 3
        # ...and the per-account value is carried untouched on the account dict
        # for the orchestrator/model layer to apply.
        assert loader.get_accounts_config()[0]["action_config"]["max_likes_per_run"] == 9

    def test_raw_json_types_preserved(self, make_config_loader):
        settings = {"flag": True, "count": 7, "ratio": 0.5, "nothing": None}
        loader = make_config_loader(settings=settings)
        assert loader.get_setting("flag") is True
        assert loader.get_setting("count") == 7
        assert loader.get_setting("ratio") == 0.5
        assert loader.get_setting("nothing") is None
        # A present-but-null value is not the same as a missing key.
        assert loader.get_setting("nothing", "fallback") is None
        assert loader.get_setting("absent", "fallback") == "fallback"
