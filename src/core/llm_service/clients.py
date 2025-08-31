import logging
from typing import Optional, Dict, Any, Tuple

from core.config_loader import ConfigLoader
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


def initialize_clients(config_loader: ConfigLoader) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
    """
    Initialize available LLM clients based on config and installed SDKs.

    Returns: (clients, api_keys, llm_settings)
      clients: {
        'gemini_client': ChatGoogleGenerativeAI | None,
        'openai_client': AsyncOpenAI | None,
        'azure_openai_client': AsyncAzureOpenAI | None,
      }
    """
    api_keys: Dict[str, Any] = config_loader.get_setting('api_keys', {})
    llm_settings: Dict[str, Any] = config_loader.get_setting('llm_settings', {})

    gemini_client = None
    openai_client = None
    azure_openai_client = None

    # Gemini client
    if GEMINI_AVAILABLE:
        gemini_config = llm_settings.get('gemini', {})
        gemini_api_key = api_keys.get('gemini_api_key')
        if _is_api_key_valid('gemini_api_key', gemini_api_key):
            try:
                model_name = gemini_config.get('model', 'gemini-2.5-flash')
                gemini_client = ChatGoogleGenerativeAI(
                    model=model_name,
                    api_key=SecretStr(gemini_api_key) if SecretStr else gemini_api_key,
                    temperature=gemini_config.get('temperature', 0.7),
                )
                logger.info(f"Gemini client initialized with model '{model_name}'.")
            except Exception as e:
                logger.error(f"Failed to initialize Gemini client: {e}", exc_info=True)
        else:
            logger.info("Gemini API key not configured or is a placeholder. Gemini client not initialized.")
    else:
        logger.info("Gemini SDK not available. Gemini client cannot be initialized.")

    # OpenAI client
    if OPENAI_AVAILABLE:
        openai_api_key = api_keys.get('openai_api_key')
        if _is_api_key_valid('openai_api_key', openai_api_key):
            try:
                openai_client = AsyncOpenAI(api_key=openai_api_key)
                logger.info("AsyncOpenAI client initialized.")
            except Exception as e:
                logger.error(f"Failed to initialize AsyncOpenAI client: {e}", exc_info=True)
        else:
            logger.info("OpenAI API key not configured or is a placeholder. OpenAI client not initialized.")
    else:
        logger.info("OpenAI SDK not available. OpenAI and Azure OpenAI clients cannot be initialized.")

    # Azure OpenAI client
    if OPENAI_AVAILABLE:
        azure_config = llm_settings.get('azure', {})
        azure_api_key = api_keys.get('azure_openai_api_key')
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
                logger.info(f"AsyncAzureOpenAI client initialized for endpoint '{azure_endpoint}'.")
            except Exception as e:
                logger.error(f"Failed to initialize AsyncAzureOpenAI client: {e}", exc_info=True)
        else:
            logger.info("Azure OpenAI credentials incomplete or placeholders. Azure client not initialized.")

    return (
        {
            'gemini_client': gemini_client,
            'openai_client': openai_client,
            'azure_openai_client': azure_openai_client,
        },
        api_keys,
        llm_settings,
    )

