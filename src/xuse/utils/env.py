"""One-time, idempotent loading of the project-root .env file."""
import logging
from pathlib import Path

from dotenv import load_dotenv

from xuse.core.config_loader import PROJECT_ROOT

logger = logging.getLogger(__name__)

_loaded = False


def load_env() -> None:
    """Load ``<project_root>/.env`` into ``os.environ`` once per process.

    Idempotent: later calls are no-ops. A missing .env file is not an error.
    Pre-existing process environment variables always win over .env values
    (python-dotenv never overrides by default).
    """
    global _loaded
    if _loaded:
        return
    _loaded = True
    env_path = Path(PROJECT_ROOT) / ".env"
    if load_dotenv(env_path):
        logger.info(f"Loaded environment overrides from '{env_path}'.")
    else:
        logger.debug("No .env file found; using process environment only.")
