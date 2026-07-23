import logging
import os
from typing import Optional, Dict, Any, Tuple

from xuse.core.config_loader import ConfigLoader
from xuse.utils.env import load_env
from .constants import API_KEY_PLACEHOLDERS

logger = logging.getLogger(__name__)

# Optional SDK imports, guarded by availability flags
try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    from pydantic import SecretStr  # Used by langchain_google_genai for API keys
    GEMINI_AVAILABLE = True
except Exception:
    ChatGoogleGenerativeAI = None  # type: ignore
    SecretStr = None  # type: ignore
    GEMINI_AVAILABLE = False

try:
    from openai import AsyncOpenAI, AsyncAzureOpenAI
    OPENAI_AVAILABLE = True
except Exception:
    AsyncOpenAI = None  # type: ignore
    AsyncAzureOpenAI = None  # type: ignore
    OPENAI_AVAILABLE = False


def _is_api_key_valid(key_name: str, key_value: Optional[str]) -> bool:
    if not key_value:
        return False
    placeholder = API_KEY_PLACEHOLDERS.get(key_name)
    if placeholder and key_value.strip().upper() == placeholder:
        return False
    if "YOUR_" in key_value.upper() and "_KEY" in key_value.upper():
        return False
    return True


# Env vars that override config/settings.json api_keys per provider. Env wins.
_ENV_KEY_NAMES: Dict[str, str] = {
    'gemini_api_key': 'GEMINI_API_KEY',
    'openai_api_key': 'OPENAI_API_KEY',
    'azure_openai_api_key': 'AZURE_OPENAI_API_KEY',
}


def _resolve_api_key(key_name: str, config_value: Optional[str]) -> Tuple[Optional[str], str]:
    """
    Resolve an API key: environment variable first, then settings.json.

    Returns (value, source_label). Value is None when neither source supplies
    a non-empty key. The value is never logged; the source label is safe to log.
    """
    env_var = _ENV_KEY_NAMES.get(key_name)
    if env_var:
        env_value = os.environ.get(env_var)
        if env_value and env_value.strip():
            return env_value, f"env var {env_var}"
    if config_value and str(config_value).strip():
        return str(config_value), "settings.json"
    return None, "none"


def initialize_clients(config_loader: ConfigLoader) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
    """
    Initialize available LLM clients based on config and installed SDKs.

    API key precedence per provider: environment variable (see _ENV_KEY_NAMES,
    loaded from the process env or a project-root .env file) > settings.json
    api_keys. _is_api_key_valid remains the final gate on the winning source.
    Key values are never logged; only the supplying source is.

    Returns: (clients, api_keys, llm_settings)
      clients: {
        'gemini_client': ChatGoogleGenerativeAI | None,
        'openai_client': AsyncOpenAI | None,
        'azure_openai_client': AsyncAzureOpenAI | None,
      }
    """
    load_env()  # idempotent; no-op when no .env file exists

    api_keys: Dict[str, Any] = config_loader.get_setting('api_keys', {})
    llm_settings: Dict[str, Any] = config_loader.get_setting('llm_settings', {})

    gemini_client = None
    openai_client = None
    azure_openai_client = None

    # Gemini client
    if GEMINI_AVAILABLE:
        gemini_config = llm_settings.get('gemini', {})
        gemini_api_key, gemini_key_source = _resolve_api_key('gemini_api_key', api_keys.get('gemini_api_key'))
        if _is_api_key_valid('gemini_api_key', gemini_api_key):
            try:
                model_name = gemini_config.get('model', 'gemini-2.5-flash')
                gemini_client = ChatGoogleGenerativeAI(
                    model=model_name,
                    api_key=SecretStr(gemini_api_key) if SecretStr else gemini_api_key,
                    temperature=gemini_config.get('temperature', 0.7),
                )
                logger.info(f"Gemini client initialized with model '{model_name}' (API key source: {gemini_key_source}).")
            except Exception as e:
                logger.error(f"Failed to initialize Gemini client: {e}", exc_info=True)
        else:
            logger.info(f"Gemini API key not configured or is a placeholder (source: {gemini_key_source}). Gemini client not initialized.")
    else:
        logger.info("Gemini SDK not available. Gemini client cannot be initialized.")

    # OpenAI client
    if OPENAI_AVAILABLE:
        openai_api_key, openai_key_source = _resolve_api_key('openai_api_key', api_keys.get('openai_api_key'))
        if _is_api_key_valid('openai_api_key', openai_api_key):
            try:
                openai_client = AsyncOpenAI(api_key=openai_api_key)
                logger.info(f"AsyncOpenAI client initialized (API key source: {openai_key_source}).")
            except Exception as e:
                logger.error(f"Failed to initialize AsyncOpenAI client: {e}", exc_info=True)
        else:
            logger.info(f"OpenAI API key not configured or is a placeholder (source: {openai_key_source}). OpenAI client not initialized.")
    else:
        logger.info("OpenAI SDK not available. OpenAI and Azure OpenAI clients cannot be initialized.")

    # Azure OpenAI client
    if OPENAI_AVAILABLE:
        azure_config = llm_settings.get('azure', {})
        azure_api_key, azure_key_source = _resolve_api_key('azure_openai_api_key', api_keys.get('azure_openai_api_key'))
        azure_endpoint = api_keys.get('azure_openai_endpoint')
        azure_deployment_name = azure_config.get('deployment_name') or api_keys.get('azure_openai_deployment')
        azure_api_version = azure_config.get('api_version') or api_keys.get('azure_api_version', '2024-05-01-preview')

        if (
            _is_api_key_valid('azure_openai_api_key', azure_api_key)
            and _is_api_key_valid('azure_openai_endpoint', azure_endpoint)
            and _is_api_key_valid('azure_openai_deployment', azure_deployment_name)
        ):
            try:
                azure_openai_client = AsyncAzureOpenAI(
                    api_key=azure_api_key,
                    azure_endpoint=azure_endpoint,
                    api_version=azure_api_version,
                )
                logger.info(f"AsyncAzureOpenAI client initialized for endpoint '{azure_endpoint}' (API key source: {azure_key_source}).")
            except Exception as e:
                logger.error(f"Failed to initialize AsyncAzureOpenAI client: {e}", exc_info=True)
        else:
            logger.info(f"Azure OpenAI credentials incomplete or placeholders (key source: {azure_key_source}). Azure client not initialized.")

    return (
        {
            'gemini_client': gemini_client,
            'openai_client': openai_client,
            'azure_openai_client': azure_openai_client,
        },
        api_keys,
        llm_settings,
    )

