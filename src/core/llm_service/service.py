import logging
from typing import Optional, Dict, Any, List, Tuple

from core.config_loader import ConfigLoader
from .constants import DEFAULT_SERVICE_ORDER
from .clients import initialize_clients
from .prompts import build_structured_json_prompt
from .parsing import extract_json_from_response_text
from .generator import TextGenerator

logger = logging.getLogger(__name__)


class LLMService:
    """
    Facade for LLM operations. Initializes provider clients from config and
    exposes text generation and structured JSON generation helpers.
    """

    def __init__(self, config_loader: ConfigLoader):
        self.config_loader = config_loader
        clients, api_keys, llm_settings = initialize_clients(config_loader)
        self.clients = clients
        self.api_keys = api_keys
        self.llm_settings = llm_settings
        # Ensure service order exists
        self.llm_settings.setdefault('service_preference_order', DEFAULT_SERVICE_ORDER)
        self._text_generator = TextGenerator(self.clients, self.llm_settings)

    async def generate_text(
        self,
        prompt: str,
        service_preference: Optional[str] = None,
        system_prompt: Optional[str] = None,
        messages: Optional[List[Dict[str, str]]] = None,
        **call_params: Any,
    ) -> Optional[str]:
        return await self._text_generator.generate_text(
            prompt,
            service_preference=service_preference,
            system_prompt=system_prompt,
            messages=messages,
            **call_params,
        )

    async def generate_structured(
        self,
        task_instruction: str,
        schema: Dict[str, Any],
        *,
        service_preference: Optional[str] = None,
        require_markdown_fences: bool = False,
        max_retries: int = 2,
        system_prompt: Optional[str] = None,
        few_shots: Optional[List[Tuple[str, Dict[str, Any]]]] = None,
        hard_character_limit: Optional[int] = None,
        **call_params: Any,
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Generate a structured JSON object following the provided schema.
        Returns (parsed_json_dict, error_message). On success, error_message is None.
        """
        prompt = build_structured_json_prompt(
            task_instruction,
            schema,
            require_markdown_fences=require_markdown_fences,
            few_shots=few_shots,
            hard_character_limit=hard_character_limit,
        )

        use_openai_json_mode = False
        if service_preference == 'openai' and 'response_format' not in call_params:
            call_params['response_format'] = {"type": "json_object"}
            use_openai_json_mode = True

        last_err: Optional[str] = None
        for attempt in range(max_retries + 1):
            text = await self.generate_text(
                prompt=prompt,
                service_preference=service_preference,
                system_prompt=system_prompt,
                **call_params,
            )
            if not text:
                last_err = "No response from LLM"
                continue

            data, err = extract_json_from_response_text(text)
            if data is not None:
                return data, None

            if use_openai_json_mode and attempt == 0:
                call_params.pop('response_format', None)
            last_err = err or "Unknown parse error"

        return None, last_err or "Failed to produce valid JSON after retries"

