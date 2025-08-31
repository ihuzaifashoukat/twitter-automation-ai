import os
from pathlib import Path

# Reuse the single source of truth for project root from core.config_loader
from core.config_loader import PROJECT_ROOT as CONFIG_PROJECT_ROOT

# Project root (repo root), consistent with ConfigLoader
PROJECT_ROOT: Path = CONFIG_PROJECT_ROOT
DEFAULT_WDM_CACHE_PATH: Path = PROJECT_ROOT / ".wdm_cache"

# Environment variable key used by webdriver_manager to control SSL verification
WDM_SSL_VERIFY_ENV = "WDM_SSL_VERIFY"

def set_wdm_ssl_verify(enabled: bool) -> None:
    os.environ[WDM_SSL_VERIFY_ENV] = '1' if enabled else '0'
