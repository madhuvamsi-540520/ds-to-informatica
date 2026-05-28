"""ACC-02-AI: BASIC Routine to Expression Translator (hybrid).

Lookup table for common functions; Claude API for complex/multi-line logic.
"""

import json
import re
import os
from datetime import datetime
from pathlib import Path
from migrator.core.claude_client import ClaudeClient
from migrator.core.validator import validate_basic_code, validate_acc02_output
from migrator.core.models import Acc02Input, Acc02Output, ApiCallMetadata, FunctionMapping

_BASIC_FN_PATH = Path(__file__).parent.parent / "data" / "basic_functions.json"
_PROMPT_TEMPLATE = """You are an ETL migration specialist fluent in DataStage BASIC and Informatica expression languages.

Convert this DataStage BASIC Transformer expression to Informatica CDI expression language.

BASIC Expression:
---
{basic_code}
---

Column Context:
- Input columns: {input_columns}
- Output columns: {output_columns}

Translation Rules:
1. Use Informatica built-in functions only (no custom Java unless necessary)
2. Handle NULLs safely (use IIF + ISNULL)
3. Preserve exact business logic
4. Provide assumptions if you make any

Output format (STRICT — no extra text):
TRANSLATED EXPRESSION:
[expression here]

ASSUMPTIONS:
[list assumptions or write NONE]

REVIEW NOTES:
[flag anything needing engineer check or write NONE]

CONFIDENCE: [0-100]"""


def _load_basic_map() -> dict:
    with open(_BASIC_FN_PATH) as f:
        return json.load(f)


def _try_lookup(basic_code: str, fn_map: dict) -> tuple[str | None, list[FunctionMapping]]:
    """Try to translate using lookup table. Returns (translated, mappings) or (None, [])."""
    code = basic_code.strip()
    mappings = []

    # Match single function call: FuncName(args)
    match = re.match(r"^(\w+)\((.+)\)$", code, re.DOTALL)
    if not match:
        return None, []

    fn_name = match.group(1)
    if fn_name not in fn_map:
        return None, []

    template = fn_map[fn_name]
    args = [a.strip() for a in match.group(2).split(",")]

    try:
        translated = template.format(*args)
        mappings.append(FunctionMapping(
            basic_function=fn_name,
            idmc_equivalent=template,
            confidence=100
        ))
        return translated, mappings
    except (IndexError, KeyError):
        return None, []


def _parse_claude_response(text: str) -> dict:
    result = {"translated": None, "assumptions": [], "warnings": [], "confidence": 70}

    lines = text.strip().splitlines()
    section = None
    buffer = []

    for line in lines:
        if line.startswith("TRANSLATED EXPRESSION:"):
            section = "translated"
        elif line.startswith("ASSUMPTIONS:"):
            if section == "translated" and buffer:
                result["translated"] = "\n".join(buffer).strip()
            buffer = []
            section = "assumptions"
        elif line.startswith("REVIEW NOTES:"):
            if section == "assumptions":
                result["assumptions"] = [l for l in buffer if l.strip() and l.strip() != "NONE"]
            buffer = []
            section = "notes"
        elif line.startswith("CONFIDENCE:"):
            if section == "notes":
                result["warnings"] = [l for l in buffer if l.strip() and l.strip() != "NONE"]
            try:
                result["confidence"] = int(re.search(r"\d+", line).group())
            except Exception:
                pass
            section = None
        elif section:
            buffer.append(line)

    if section == "translated" and buffer:
        result["translated"] = "\n".join(buffer).strip()

    return result


def translate(request: Acc02Input, client: ClaudeClient | None = None) -> Acc02Output:
    """Translate a BASIC expression to Informatica. Uses lookup first, Claude if needed."""
    validate_basic_code(request.basic_code)

    fn_map = _load_basic_map()
    lookup_result, mappings = _try_lookup(request.basic_code, fn_map)

    if lookup_result:
        return Acc02Output(
            job_id=request.job_id,
            translated_expression=lookup_result,
            complexity_classification="SIMPLE",
            confidence_level=100,
            requires_human_review=False,
            function_mappings=mappings,
            estimated_review_time_minutes=0
        )

    # Complex/unmatched — call Claude
    if client is None:
        client = ClaudeClient()

    input_cols = [c.name for c in request.column_context.get("input_columns", [])]
    output_cols = [c.name for c in request.column_context.get("output_columns", [])]

    prompt = _PROMPT_TEMPLATE.format(
        basic_code=request.basic_code,
        input_columns=", ".join(input_cols) or "unknown",
        output_columns=", ".join(output_cols) or "unknown"
    )

    api_result = client.call(prompt, "ACC-02-AI", "basic_translation")
    parsed = _parse_claude_response(api_result["content"])

    confidence = parsed["confidence"]
    requires_review = confidence < 80 or bool(parsed["assumptions"])

    validate_acc02_output({
        "confidence_level": confidence,
        "requires_human_review": requires_review
    })

    return Acc02Output(
        job_id=request.job_id,
        translated_expression=parsed["translated"],
        complexity_classification=request.complexity_level,
        confidence_level=confidence,
        requires_human_review=requires_review,
        assumptions_detected=parsed["assumptions"],
        warnings=parsed["warnings"],
        estimated_review_time_minutes=15 if requires_review else 0,
        api_call_metadata=ApiCallMetadata(
            model=api_result["model"],
            tokens_input=api_result["tokens_input"],
            tokens_output=api_result["tokens_output"],
            cost_usd=api_result["cost_usd"],
            latency_seconds=api_result["latency_seconds"]
        )
    )


def translate_batch(requests: list[Acc02Input], output_dir: str = "output/acc02_basic") -> list[dict]:
    """Translate a batch of BASIC expressions."""
    os.makedirs(output_dir, exist_ok=True)
    client = ClaudeClient()
    results = []

    for req in requests:
        try:
            output = translate(req, client)
            result = output.model_dump()
        except Exception as e:
            result = {
                "job_id": req.job_id,
                "error": str(e),
                "requires_human_review": True
            }

        results.append(result)
        out_file = os.path.join(output_dir, f"{req.job_id}.json")
        with open(out_file, "w") as f:
            json.dump(result, f, indent=2, default=str)

    return results
