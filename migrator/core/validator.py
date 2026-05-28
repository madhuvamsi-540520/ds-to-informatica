"""Input/output validation enforcing spec Section 7.6 constraints."""

from datetime import datetime


class InputValidationError(Exception):
    def __init__(self, field: str, message: str):
        self.field = field
        super().__init__(f"Input validation failed on '{field}': {message}")


class OutputValidationError(Exception):
    def __init__(self, message: str):
        super().__init__(f"Output validation failed: {message}")


def validate_job_ids_unique(job_ids: list[str]):
    if len(job_ids) != len(set(job_ids)):
        raise InputValidationError("job_id", "Duplicate job_ids in batch")


def validate_basic_code(code: str):
    if not code or not code.strip():
        raise InputValidationError("basic_code", "must be non-empty")
    if len(code) > 1000:
        raise InputValidationError("basic_code", f"exceeds max length 1000 (got {len(code)})")


def validate_cpp_code(code: str):
    if not code or not code.strip():
        raise InputValidationError("cpp_source_code", "must be non-empty")
    lines = code.strip().splitlines()
    if len(lines) < 5:
        raise InputValidationError("cpp_source_code", "must be at least 5 lines")


def validate_mapping_spec(spec: dict):
    if not spec:
        raise InputValidationError("mapping_spec", "must be non-empty JSON/YAML")


def validate_job_graph(jobs: list) -> list[str]:
    """Check for circular dependencies. Returns cycle path if found."""
    graph = {j.job_id: j.downstream_jobs for j in jobs}
    visited = set()
    rec_stack = set()

    def dfs(node, path):
        visited.add(node)
        rec_stack.add(node)
        for neighbor in graph.get(node, []):
            if neighbor not in visited:
                cycle = dfs(neighbor, path + [neighbor])
                if cycle:
                    return cycle
            elif neighbor in rec_stack:
                return path + [neighbor]
        rec_stack.discard(node)
        return []

    for job in jobs:
        if job.job_id not in visited:
            cycle = dfs(job.job_id, [job.job_id])
            if cycle:
                return cycle
    return []


def validate_confidence(confidence: int):
    if not (0 <= confidence <= 100):
        raise OutputValidationError(f"confidence_level must be 0-100, got {confidence}")


def validate_acc02_output(output: dict, confidence_threshold: int = 80):
    validate_confidence(output.get("confidence_level", 0))
    if output.get("confidence_level", 0) < confidence_threshold:
        if not output.get("requires_human_review"):
            raise OutputValidationError("requires_human_review must be True when confidence < threshold")


def validate_acc09_output(output: dict):
    issues = output.get("issues_found", [])
    summary = output.get("summary", {})
    total = summary.get("total_issues", 0)
    if len(issues) != total:
        raise OutputValidationError(
            f"issues_found count ({len(issues)}) does not match summary.total_issues ({total})"
        )
    for issue in issues:
        if issue.get("severity") not in ("CRITICAL", "HIGH", "MEDIUM", "LOW"):
            raise OutputValidationError(f"Invalid severity: {issue.get('severity')}")


def validate_acc10_output(output: dict, input_job_ids: set[str]):
    waves = output.get("migration_wave_plan", [])
    all_wave_jobs = []
    for wave in waves:
        all_wave_jobs.extend(wave.get("jobs", []))

    if set(all_wave_jobs) != input_job_ids:
        missing = input_job_ids - set(all_wave_jobs)
        extra = set(all_wave_jobs) - input_job_ids
        raise OutputValidationError(
            f"Wave plan job mismatch. Missing: {missing}, Extra: {extra}"
        )

    seen = set()
    for job in all_wave_jobs:
        if job in seen:
            raise OutputValidationError(f"Job '{job}' appears in more than one wave")
        seen.add(job)
