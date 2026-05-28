"""ACC-10-AI: Job Dependency & Impact Analysis (Claude API primary).

Builds job graph, detects cycles, then Claude generates wave plan + rollback strategy.
"""

import json
import os
import re
from migrator.core.claude_client import ClaudeClient
from migrator.core.validator import validate_job_graph, validate_acc10_output
from migrator.core.models import (
    Acc10Input, Acc10Output, MigrationWave, CriticalPathAnalysis,
    HiddenDependency, RollbackStrategy, RiskAssessment, ApiCallMetadata
)

_PROMPT_TEMPLATE = """You are an ETL architecture strategist. Analyze this job dependency graph and recommend a migration strategy.

Job Dependency Graph:
{job_graph}

Business Context:
- Load window: {window_start}:00 to {window_end}:00
- Affected reports: {reports_count}
- SLA: {sla_minutes} minutes

Migration Constraints:
- Max parallel jobs: {max_parallel}
- Max wave size: {max_wave_size}
- Pilot job count target: {pilot_count}

Provide your analysis in this STRICT format:
WAVE_PLAN:
[format each wave as: WAVE_ID | WAVE_NAME | JOB_IDS(comma-separated) | EST_MINUTES | CRITICAL_PATH_MINUTES | SLA_ACHIEVABLE(true/false) | RISK_LEVEL | ROLLBACK_TRIGGER]

CRITICAL_PATH:
[comma-separated job_ids on critical path]

CRITICAL_PATH_MINUTES: [integer]

HIDDEN_DEPENDENCIES:
[format each as: JOB_A | JOB_B | TYPE | SEVERITY | NOTES]
[or write NONE]

ROLLBACK_STEPS:
[numbered steps]

PARALLEL_RUN_RECOMMENDED: [true/false]
DATA_RECONCILIATION_REQUIRED: [true/false]
SWITCH_BACK_SLA_MINUTES: [integer]
RISK_SCORE: [0-100]
SINGLE_POINTS_OF_FAILURE: [comma-separated job_ids or NONE]"""


def _build_graph_text(jobs) -> str:
    lines = []
    for job in jobs:
        upstream = ", ".join(job.upstream_jobs) or "none"
        downstream = ", ".join(job.downstream_jobs) or "none"
        flags = []
        if job.has_custom_operators:
            flags.append("custom_op")
        if job.has_basic_routines:
            flags.append("basic_routine")
        flag_str = f" [{', '.join(flags)}]" if flags else ""
        lines.append(
            f"  {job.job_id} ({job.job_name}){flag_str}: "
            f"upstream=[{upstream}] downstream=[{downstream}] "
            f"~{job.execution_time_minutes}min criticality={job.business_criticality}"
        )
    return "\n".join(lines)


def _parse_response(text: str, input_jobs: list) -> dict:
    result = {
        "waves": [], "critical_path": [], "critical_path_minutes": 0,
        "hidden_deps": [], "rollback_steps": [],
        "parallel_run": False, "data_recon": False,
        "switch_back_sla": 60, "risk_score": 50, "spof": []
    }

    section = None
    buffer = []

    for line in text.strip().splitlines():
        line = line.strip()
        if not line:
            continue

        if line == "WAVE_PLAN:":
            section = "waves"
        elif line == "CRITICAL_PATH:":
            section = "critical_path"
        elif line.startswith("CRITICAL_PATH_MINUTES:"):
            try:
                result["critical_path_minutes"] = int(re.search(r"\d+", line).group())
            except Exception:
                pass
        elif line == "HIDDEN_DEPENDENCIES:":
            section = "hidden_deps"
        elif line == "ROLLBACK_STEPS:":
            section = "rollback"
        elif line.startswith("PARALLEL_RUN_RECOMMENDED:"):
            result["parallel_run"] = "true" in line.lower()
        elif line.startswith("DATA_RECONCILIATION_REQUIRED:"):
            result["data_recon"] = "true" in line.lower()
        elif line.startswith("SWITCH_BACK_SLA_MINUTES:"):
            try:
                result["switch_back_sla"] = int(re.search(r"\d+", line).group())
            except Exception:
                pass
        elif line.startswith("RISK_SCORE:"):
            try:
                result["risk_score"] = int(re.search(r"\d+", line).group())
            except Exception:
                pass
        elif line.startswith("SINGLE_POINTS_OF_FAILURE:"):
            val = line.split(":", 1)[1].strip()
            result["spof"] = [j.strip() for j in val.split(",") if j.strip() != "NONE"]
        elif section:
            if section == "waves" and "|" in line:
                parts = [p.strip() for p in line.split("|")]
                if len(parts) >= 8:
                    result["waves"].append({
                        "wave_id": int(parts[0]) if parts[0].isdigit() else len(result["waves"]),
                        "wave_name": parts[1],
                        "jobs": [j.strip() for j in parts[2].split(",") if j.strip()],
                        "estimated_execution_time_minutes": int(parts[3]) if parts[3].isdigit() else 0,
                        "critical_path_minutes": int(parts[4]) if parts[4].isdigit() else 0,
                        "sla_achievable": parts[5].lower() == "true",
                        "risk_level": parts[6],
                        "rollback_trigger": parts[7]
                    })
            elif section == "critical_path" and line != "NONE":
                result["critical_path"] = [j.strip() for j in line.split(",")]
                section = None
            elif section == "hidden_deps" and line != "NONE" and "|" in line:
                parts = [p.strip() for p in line.split("|")]
                if len(parts) >= 5:
                    result["hidden_deps"].append({
                        "job_a": parts[0], "job_b": parts[1],
                        "dependency_type": parts[2], "severity": parts[3], "notes": parts[4]
                    })
            elif section == "rollback" and line != "NONE":
                result["rollback_steps"].append(re.sub(r"^\d+\.\s*", "", line))

    return result


def analyze(request: Acc10Input, client: ClaudeClient | None = None) -> Acc10Output:
    """Analyze job dependencies and generate migration wave plan."""
    if len(request.job_dependency_graph) < 5:
        raise ValueError("Job graph must contain ≥5 jobs for meaningful analysis")

    cycle = validate_job_graph(request.job_dependency_graph)
    if cycle:
        raise ValueError(f"Circular dependency detected: {' → '.join(cycle)}")

    if client is None:
        client = ClaudeClient()

    graph_text = _build_graph_text(request.job_dependency_graph)
    bc = request.business_context
    mc = request.migration_constraints

    prompt = _PROMPT_TEMPLATE.format(
        job_graph=graph_text,
        window_start=bc.load_window_start_hour,
        window_end=bc.load_window_end_hour,
        reports_count=bc.affected_reports_count,
        sla_minutes=bc.sla_minutes,
        max_parallel=mc.max_parallel_jobs,
        max_wave_size=mc.max_wave_size,
        pilot_count=mc.pilot_job_count
    )

    api_result = client.call(prompt, "ACC-10-AI", "dependency_analysis")
    parsed = _parse_response(api_result["content"], request.job_dependency_graph)

    input_job_ids = {j.job_id for j in request.job_dependency_graph}
    validate_acc10_output({"migration_wave_plan": parsed["waves"]}, input_job_ids)

    return Acc10Output(
        project_id=request.project_id,
        migration_wave_plan=[MigrationWave(**w) for w in parsed["waves"]],
        critical_path_analysis=CriticalPathAnalysis(
            critical_path_jobs=parsed["critical_path"],
            total_critical_path_minutes=parsed["critical_path_minutes"]
        ),
        hidden_dependencies=[HiddenDependency(**d) for d in parsed["hidden_deps"]],
        rollback_strategy=RollbackStrategy(
            parallel_run_recommended=parsed["parallel_run"],
            shadow_traffic_recommended=False,
            switch_back_sla_minutes=parsed["switch_back_sla"],
            data_reconciliation_required=parsed["data_recon"],
            detailed_steps=parsed["rollback_steps"] or ["Manual rollback required — contact architect"]
        ),
        risk_assessment=RiskAssessment(
            total_risk_score=parsed["risk_score"],
            single_points_of_failure=parsed["spof"]
        ),
        api_call_metadata=ApiCallMetadata(
            model=api_result["model"],
            tokens_input=api_result["tokens_input"],
            tokens_output=api_result["tokens_output"],
            cost_usd=api_result["cost_usd"],
            latency_seconds=api_result["latency_seconds"]
        )
    )


def analyze_and_save(request: Acc10Input, output_dir: str = "output/acc10_dependency") -> dict:
    os.makedirs(output_dir, exist_ok=True)
    output = analyze(request)
    result = output.model_dump()
    out_file = os.path.join(output_dir, f"{request.project_id}_wave_plan.json")
    with open(out_file, "w") as f:
        json.dump(result, f, indent=2, default=str)
    return result
