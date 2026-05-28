"""ACC-09-AI: Anti-Pattern Detection & Design Review (Claude API primary).

Static pre-checks + Claude semantic review of IDMC mapping specs.
"""

import json
import os
import re
from migrator.core.claude_client import ClaudeClient
from migrator.core.validator import validate_mapping_spec, validate_acc09_output
from migrator.core.models import (
    Acc09Input, Acc09Output, Issue, BestPractice, CriticalQuestion, ReviewSummary, ApiCallMetadata
)

_PROMPT_TEMPLATE = """You are an Informatica IDMC design architect reviewing a mapping for best practices.

Audit this mapping design for issues, anti-patterns, and optimization opportunities.

Mapping Specification:
---
{mapping_spec}
---

Context:
- Load volume: {load_volume} rows
- SLA: {sla} minutes
- Source system: {source_name} ({source_type}, {source_cols} columns)
- Target system: {target_name} ({target_type}, {target_cols} columns)

Review Criteria (prioritized):
1. CRITICAL: Hard-coded values, security risks, data loss
2. HIGH: Performance issues, missing error handling, SLA risk
3. MEDIUM: Design improvements, idiomatic patterns
4. LOW: Code style, documentation

Output format (STRICT):
ISSUES:
[format each as: ISSUE_ID | SEVERITY | CATEGORY | DESCRIPTION | IMPACT | COMPONENT | FIX | FIX_COMPLEXITY]
[or write NONE]

BEST PRACTICES:
[format each as: CATEGORY | RECOMMENDATION | CURRENT | SUGGESTED]
[or write NONE]

QUESTIONS:
[format each as: QUESTION | CONTEXT]
[or write NONE]

SLA_IMPACT: [e.g., "+10% latency" or "Within SLA"]
CONFIDENCE: [0-100]"""

_HARDCODED_PATTERNS = [
    (r"'[A-Z0-9_]{5,}'", "Hard-coded string value detected — consider parameterizing"),
    (r"\b\d{4}-\d{2}-\d{2}\b", "Hard-coded date detected — use parameter or SYSDATE"),
    (r"password\s*=\s*['\"][^'\"]+['\"]", "Hard-coded password detected — CRITICAL security risk"),
]


def _static_checks(mapping_spec: dict) -> list[dict]:
    """Run deterministic checks before calling Claude."""
    spec_str = json.dumps(mapping_spec)
    issues = []
    for i, (pattern, message) in enumerate(_HARDCODED_PATTERNS):
        if re.search(pattern, spec_str, re.IGNORECASE):
            severity = "CRITICAL" if "password" in message.lower() else "MEDIUM"
            issues.append({
                "issue_id": f"STATIC-{i+1:03d}",
                "severity": severity,
                "category": "HARD_CODED_VALUE",
                "description": message,
                "impact": "Reduces portability and may cause security issues",
                "affected_component": "mapping_spec",
                "suggested_fix": "Replace with parameterized value",
                "fix_complexity": "TRIVIAL"
            })
    return issues


def _parse_response(text: str) -> dict:
    result = {"issues": [], "best_practices": [], "questions": [], "sla_impact": "Unknown", "confidence": 75}
    section = None

    for line in text.strip().splitlines():
        line = line.strip()
        if not line:
            continue
        if line == "ISSUES:":
            section = "issues"
        elif line == "BEST PRACTICES:":
            section = "best_practices"
        elif line == "QUESTIONS:":
            section = "questions"
        elif line.startswith("SLA_IMPACT:"):
            result["sla_impact"] = line.split(":", 1)[1].strip()
            section = None
        elif line.startswith("CONFIDENCE:"):
            try:
                result["confidence"] = int(re.search(r"\d+", line).group())
            except Exception:
                pass
            section = None
        elif section and line != "NONE":
            parts = [p.strip() for p in line.split("|")]
            if section == "issues" and len(parts) >= 8:
                result["issues"].append({
                    "issue_id": parts[0], "severity": parts[1], "category": parts[2],
                    "description": parts[3], "impact": parts[4], "affected_component": parts[5],
                    "suggested_fix": parts[6], "fix_complexity": parts[7]
                })
            elif section == "best_practices" and len(parts) >= 4:
                result["best_practices"].append({
                    "category": parts[0], "recommendation": parts[1],
                    "current_approach": parts[2], "suggested_approach": parts[3]
                })
            elif section == "questions" and len(parts) >= 2:
                result["questions"].append({"question": parts[0], "context": parts[1]})

    return result


def review(request: Acc09Input, client: ClaudeClient | None = None) -> Acc09Output:
    """Run static + Claude design review on a mapping spec."""
    validate_mapping_spec(request.mapping_spec)

    static_issues = _static_checks(request.mapping_spec)

    if client is None:
        client = ClaudeClient()

    prompt = _PROMPT_TEMPLATE.format(
        mapping_spec=json.dumps(request.mapping_spec, indent=2),
        load_volume=request.load_volume_rows,
        sla=request.sla_minutes,
        source_name=request.source_system.name,
        source_type=request.source_system.type,
        source_cols=request.source_system.column_count,
        target_name=request.target_system.name,
        target_type=request.target_system.type,
        target_cols=request.target_system.column_count
    )

    api_result = client.call(prompt, "ACC-09-AI", "design_analysis")
    parsed = _parse_response(api_result["content"])

    all_issues = static_issues + parsed["issues"]
    critical = sum(1 for i in all_issues if i.get("severity") == "CRITICAL")
    high = sum(1 for i in all_issues if i.get("severity") == "HIGH")

    validate_acc09_output({
        "issues_found": all_issues,
        "summary": {"total_issues": len(all_issues)}
    })

    return Acc09Output(
        job_id=request.job_id,
        issues_found=[Issue(**i) for i in all_issues],
        best_practices_found=[BestPractice(**b) for b in parsed["best_practices"]],
        critical_questions=[CriticalQuestion(**q) for q in parsed["questions"]],
        summary=ReviewSummary(
            total_issues=len(all_issues),
            critical_count=critical,
            high_count=high,
            estimated_sla_impact=parsed["sla_impact"],
            confidence_level=parsed["confidence"]
        ),
        api_call_metadata=ApiCallMetadata(
            model=api_result["model"],
            tokens_input=api_result["tokens_input"],
            tokens_output=api_result["tokens_output"],
            cost_usd=api_result["cost_usd"],
            latency_seconds=api_result["latency_seconds"]
        )
    )


def review_batch(requests: list[Acc09Input], output_dir: str = "output/acc09_review") -> list[dict]:
    os.makedirs(output_dir, exist_ok=True)
    client = ClaudeClient()
    results = []

    for req in requests:
        try:
            output = review(req, client)
            result = output.model_dump()
        except Exception as e:
            result = {"job_id": req.job_id, "error": str(e)}

        results.append(result)
        with open(os.path.join(output_dir, f"{req.job_id}.json"), "w") as f:
            json.dump(result, f, indent=2, default=str)

    return results
