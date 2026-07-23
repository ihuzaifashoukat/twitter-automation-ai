import json
from typing import Optional, Dict, Any, List, Tuple


def build_structured_json_prompt(
    task_instruction: str,
    schema: Dict[str, Any],
    additional_instructions: Optional[str] = None,
    require_markdown_fences: bool = False,
    few_shots: Optional[List[Tuple[str, Dict[str, Any]]]] = None,
    hard_character_limit: Optional[int] = None,
) -> str:
    """
    Build a strict prompt instructing the model to output ONLY valid JSON
    that follows the provided schema.
    """
    schema_str = json.dumps(schema, ensure_ascii=False, indent=2)
    fence_note = (
        "Wrap the JSON in a single fenced code block using ```json."
        if require_markdown_fences
        else "Return ONLY raw JSON with no extra text and no markdown fences."
    )
    constraints = [
        "Follow the schema exactly: no extra keys, no missing keys where required.",
        "Use null for unknown values; never invent facts.",
        "Respect field types strictly (string/number/boolean/object/array).",
        "Use only allowed enum values if applicable.",
        "No trailing commas; no comments; valid UTF-8 JSON only.",
    ]
    if hard_character_limit:
        constraints.append(
            f"Ensure any free-text fields respect a hard {hard_character_limit} characters limit."
        )

    parts = [
        "You are an expert content+data assistant that returns machine-parseable JSON only.",
        fence_note,
        "Output policy:",
        "- " + "\n- ".join(constraints),
        "Task:",
        task_instruction.strip(),
        "\nJSON Schema (shape and keys to follow):",
        schema_str,
    ]
    if few_shots:
        parts.append("\nExamples (follow format strictly):")
        for i, (inp, out) in enumerate(few_shots, start=1):
            try:
                out_str = json.dumps(out, ensure_ascii=False)
            except Exception:
                out_str = str(out)
            parts.append(
                f"Example {i} - Input:\n{inp.strip()}\nExample {i} - Output JSON:\n{out_str}"
            )
    if additional_instructions:
        parts.append("\nAdditional instructions:\n" + additional_instructions.strip())
    return "\n".join(parts)

