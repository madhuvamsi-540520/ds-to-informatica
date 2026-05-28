"""ACC-08-AI: Custom C++ Operator to Java Rewriter (Claude API primary).

Translates DataStage C++ custom operators to Java for IDMC Java Transformation.
"""

import json
import os
from migrator.core.claude_client import ClaudeClient
from migrator.core.validator import validate_cpp_code
from migrator.core.models import Acc08Input, Acc08Output, ApiCallMetadata, UnsupportedFeature

_PROMPT_TEMPLATE = """You are a bilingual Java/C++ developer specializing in data transformation algorithms.

Convert this C++ DataStage custom operator to Java for Informatica CDI Java Transformation.

C++ Operator Source:
---
{cpp_code}
---

Operator Name: {operator_name}
Functional Specification: {spec}
Input Schema: {input_schema}
Output Schema: {output_schema}
Edge Cases: {edge_cases}

Constraints:
- Target: Java {java_version}+
- Must run in IDMC containerized environment (no file I/O unless flagged, limited network)
- Thread-safe preferred
- Handle nulls safely

Output format (STRICT):
JAVA CODE:
[complete Java class here]

ASSUMPTIONS:
[list or write NONE]

UNSUPPORTED FEATURES:
[format: FEATURE | REASON | WORKAROUND — or write NONE]

EXTERNAL DEPENDENCIES:
[format: LIBRARY | VERSION | REQUIRED(true/false) — or write NONE]

CONFIDENCE: [0-100]"""


def _parse_response(text: str, job_id: str) -> dict:
    result = {
        "java_source_code": None,
        "assumptions": [],
        "unsupported_features": [],
        "dependencies": [],
        "confidence": 70
    }

    section = None
    buffer = []

    for line in text.strip().splitlines():
        if line.startswith("JAVA CODE:"):
            section = "java"
        elif line.startswith("ASSUMPTIONS:"):
            if section == "java":
                result["java_source_code"] = "\n".join(buffer).strip()
            buffer = []
            section = "assumptions"
        elif line.startswith("UNSUPPORTED FEATURES:"):
            result["assumptions"] = [l for l in buffer if l.strip() and l.strip() != "NONE"]
            buffer = []
            section = "unsupported"
        elif line.startswith("EXTERNAL DEPENDENCIES:"):
            for raw in buffer:
                parts = [p.strip() for p in raw.split("|")]
                if len(parts) == 3 and parts[0] != "NONE":
                    result["unsupported_features"].append({
                        "feature": parts[0], "reason": parts[1], "workaround": parts[2]
                    })
            buffer = []
            section = "deps"
        elif line.startswith("CONFIDENCE:"):
            for raw in buffer:
                parts = [p.strip() for p in raw.split("|")]
                if len(parts) == 3 and parts[0] != "NONE":
                    result["dependencies"].append({
                        "library": parts[0],
                        "version": parts[1],
                        "required": parts[2].lower() == "true"
                    })
            try:
                import re
                result["confidence"] = int(re.search(r"\d+", line).group())
            except Exception:
                pass
            section = None
        elif section:
            buffer.append(line)

    if section == "java" and buffer:
        result["java_source_code"] = "\n".join(buffer).strip()

    return result


def rewrite(request: Acc08Input, client: ClaudeClient | None = None) -> Acc08Output:
    """Rewrite C++ operator to Java."""
    validate_cpp_code(request.cpp_source_code)

    if client is None:
        client = ClaudeClient()

    input_schema = ", ".join(f"{c.column_name}:{c.cpp_type}" for c in request.input_schema)
    output_schema = ", ".join(f"{c.column_name}:{c.cpp_type}" for c in request.output_schema)

    prompt = _PROMPT_TEMPLATE.format(
        cpp_code=request.cpp_source_code,
        operator_name=request.operator_name,
        spec=request.functional_specification,
        input_schema=input_schema,
        output_schema=output_schema,
        edge_cases=", ".join(request.edge_cases) or "None specified",
        java_version=request.constraints.target_java_version
    )

    api_result = client.call(prompt, "ACC-08-AI", "cpp_rewriting")
    parsed = _parse_response(api_result["content"], request.job_id)

    # Flag file I/O if constraint forbids it
    has_file_io = any(kw in request.cpp_source_code for kw in ("fopen", "fread", "fwrite", "ifstream"))
    if has_file_io and not request.constraints.may_use_file_io:
        parsed["unsupported_features"].append({
            "feature": "File I/O",
            "reason": "Forbidden by constraint: may_use_file_io=false",
            "workaround": "Use IDMC File Connector instead"
        })

    confidence = parsed["confidence"]
    requires_review = confidence < 85 or bool(parsed["unsupported_features"])

    return Acc08Output(
        job_id=request.job_id,
        java_source_code=parsed["java_source_code"],
        confidence_level=confidence,
        requires_human_review=requires_review,
        unsupported_cpp_features=[UnsupportedFeature(**f) for f in parsed["unsupported_features"]],
        warnings=parsed["assumptions"],
        api_call_metadata=ApiCallMetadata(
            model=api_result["model"],
            tokens_input=api_result["tokens_input"],
            tokens_output=api_result["tokens_output"],
            cost_usd=api_result["cost_usd"],
            latency_seconds=api_result["latency_seconds"]
        )
    )


def rewrite_batch(requests: list[Acc08Input], output_dir: str = "output/acc08_cpp") -> list[dict]:
    os.makedirs(output_dir, exist_ok=True)
    client = ClaudeClient()
    results = []

    for req in requests:
        try:
            output = rewrite(req, client)
            result = output.model_dump()
        except Exception as e:
            result = {"job_id": req.job_id, "error": str(e), "requires_human_review": True}

        results.append(result)
        with open(os.path.join(output_dir, f"{req.job_id}.json"), "w") as f:
            json.dump(result, f, indent=2, default=str)

    return results
