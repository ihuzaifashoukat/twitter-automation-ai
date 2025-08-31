import logging
from typing import Optional, Dict, Any

from core.llm_service import LLMService
from data_models import LLMSettings

logger = logging.getLogger(__name__)

MAX_TWEET_CHARS = 270

def _clamp(text: str, limit: int = MAX_TWEET_CHARS) -> str:
    if not text:
        return ""
    if len(text) <= limit:
        return text
    trimmed = text[:limit]
    # Soft trim at a boundary if possible (avoid mid-word punctuation)
    return trimmed.rstrip(" .,;:!\n")

async def generate_post_text_if_needed(
    prompt_text: str,
    llm_settings: Optional[LLMSettings],
    llm_service: LLMService,
) -> str:
    """Generate final post text if the provided text looks like a prompt.

    Returns the original text if no generation is required.
    """
    text = prompt_text
    if not llm_settings:
        return text

    lowered = (prompt_text or "").lower()
    if not any(k in lowered for k in ("generate", "write", "post")):
        return text

    logger.info("Attempting structured LLM generation for post content.")
    schema: Dict[str, Any] = {
        "type": "object",
        "properties": {
            "text": {"type": "string", "description": "Final post text under 270 characters. Avoid trailing hashtags."},
            "hashtags": {"type": "array", "items": {"type": "string"}, "description": "1-4 concise hashtags (include #)."},
            "mentions": {"type": "array", "items": {"type": "string"}},
            "safety": {
                "type": "object",
                "properties": {
                    "needs_review": {"type": "boolean"},
                    "reasons": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["needs_review"],
            },
        },
        "required": ["text", "hashtags", "safety"],
    }

    task = (
        f"Generate an engaging X (Twitter) post per the prompt: {prompt_text}. "
        f"Return JSON strictly matching the schema."
    )
    data, err = await llm_service.generate_structured(
        task_instruction=task,
        schema=schema,
        service_preference=llm_settings.service_preference,
        model_name=llm_settings.model_name_override,
        max_tokens=llm_settings.max_tokens,
        temperature=max(0.3, (llm_settings.temperature or 0.7)),
        hard_character_limit=MAX_TWEET_CHARS,
    )
    if data and isinstance(data, dict) and data.get("text"):
        base = (data.get("text") or "").strip()
        hashtags = data.get("hashtags") or []
        suffix = (" " + " ".join([h if h.startswith("#") else f"#{h}" for h in hashtags[:4]])) if hashtags else ""
        # Ensure final composed text does not exceed MAX_TWEET_CHARS
        available = MAX_TWEET_CHARS - len(suffix)
        available = max(0, available)
        base = _clamp(base, available)
        composed = (base + suffix).strip()
        safety = (data.get("safety") or {})
        if isinstance(safety, dict) and safety.get("needs_review"):
            logger.warning(f"LLM flagged content for review. Reasons: {safety.get('reasons')}")
        logger.info("Structured content generated successfully.")
        return _clamp(composed)

    logger.info(f"Structured generation failed ({err}). Falling back to plain text generation.")
    # Strengthen fallback request with explicit constraints
    constrained_prompt = (
        f"{prompt_text}\n\nConstraints: Reply with a single, concise tweet under {MAX_TWEET_CHARS} characters."
        " No hashtags in the text; you may include them only if the prompt explicitly asks."
    )
    generated_text = await llm_service.generate_text(
        prompt=constrained_prompt,
        service_preference=llm_settings.service_preference,
        model_name=llm_settings.model_name_override,
        max_tokens=llm_settings.max_tokens,
        temperature=llm_settings.temperature,
    )
    if not generated_text:
        logger.error("Failed to generate tweet text; using original text.")
        return _clamp(prompt_text)
    return _clamp(generated_text)


async def maybe_generate_quote_text(
    quote_text_prompt_or_direct: Optional[str],
    llm_settings_for_quote: Optional[LLMSettings],
    llm_service: LLMService,
) -> Optional[str]:
    """Generate quote text if a prompt was provided; otherwise return the direct text."""
    if not quote_text_prompt_or_direct:
        return None
    if not llm_settings_for_quote:
        return _clamp(quote_text_prompt_or_direct)

    lowered = quote_text_prompt_or_direct.lower()
    if not ("generate quote for" in lowered or "write a quote about" in lowered):
        return _clamp(quote_text_prompt_or_direct)

    logger.info("Generating quote text from prompt for quote tweet.")
    constrained_prompt = (
        f"{quote_text_prompt_or_direct}\n\nConstraints: Keep it under {MAX_TWEET_CHARS} characters, concise, and natural."
        " Avoid hashtags unless explicitly requested."
    )
    generated_quote = await llm_service.generate_text(
        prompt=constrained_prompt,
        service_preference=llm_settings_for_quote.service_preference,
        model_name=llm_settings_for_quote.model_name_override,
        max_tokens=llm_settings_for_quote.max_tokens,
        temperature=llm_settings_for_quote.temperature,
    )
    if not generated_quote:
        logger.error("Failed to generate quote text from prompt.")
        return None
    return _clamp(generated_quote)
