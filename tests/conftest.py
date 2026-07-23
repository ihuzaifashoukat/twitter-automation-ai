"""Shared fixtures for the x-use pure-logic test suite.

All fixtures keep test state inside pytest's tmp_path — nothing here touches
the real repo config/, data/, or logs/ directories.
"""

import json
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import pytest

from xuse.core.config_loader import ConfigLoader


def write_json(path: Path, data: Any) -> Path:
    """Write data as JSON to path, creating parent directories."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return path


@pytest.fixture
def make_config_loader(tmp_path) -> Callable[..., ConfigLoader]:
    """Factory building a ConfigLoader backed by tmp JSON files.

    Never reads the real config/settings.json or config/accounts.json.
    """

    def _factory(
        settings: Optional[Dict[str, Any]] = None,
        accounts: Optional[List[Dict[str, Any]]] = None,
    ) -> ConfigLoader:
        settings_file = tmp_path / "settings.json"
        accounts_file = tmp_path / "accounts.json"
        write_json(settings_file, settings if settings is not None else {})
        write_json(accounts_file, accounts if accounts is not None else [])
        return ConfigLoader(settings_file=settings_file, accounts_file=accounts_file)

    return _factory
