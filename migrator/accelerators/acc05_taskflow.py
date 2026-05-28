"""ACC-05-AI: Sequence Job to Taskflow Optimizer (hybrid).

Rules convert structure; Claude optimizes parallelism and error handling.
"""

import json
import os
from migrator.core.claude_client import ClaudeClient
from migrator.core.dsx_parser import DSXJob, DSXExport
from migrator.core.models import ApiCallMetadata

_PROMPT_TEMPLATE = """You are an ETL orchestration specialist. Review this Taskflow execution plan and suggest optimizations.

Current Taskflow (sequential):
{task_list}

Job Dependencies:
{dependencies}

Questions:
1. Which tasks can run in parallel?
2. What is the critical path?
3. Are there missing error recovery steps?
4. Should we add checkpoints?

Respond in this STRICT format:
OPTIMIZED ORDER:
[list tasks in recommended order, mark parallel groups with (PARALLEL)]

CRITICAL PATH:
[list critical path tasks]

ERROR HANDLING GAPS:
[list gaps or write NONE]

PARALLELISM OPPORTUNITIES:
[list what can run in parallel or write NONE]

CONFIDENCE: [0-100]"""


def _build_taskflow(job: DSXJob) -> dict:
    """Rule-based: convert Sequence Job structure to base Taskflow."""
    tasks = []
    for i, stage in enumerate(job.stages):
        task_type = "MappingTask"
        if "Routine" in stage.stage_type:
            task_type = "CommandTask"
        elif "Notification" in stage.stage_type:
            task_type = "NotificationTask"

        tasks.append({
            "sequence": i + 1,
            "name": stage.name,
            "type": task_type,
            "on_success": "continue",
            "on_failure": "stop"
        })

    return {
        "taskflow_name": job.name,
        "source_job": job.name,
        "tasks": tasks,
        "execution": "sequential"
    }


def optimize(job: DSXJob, client: ClaudeClient | None = None) -> dict:
    """Convert a Sequence Job to optimized Taskflow."""
    base_taskflow = _build_taskflow(job)

    if len(job.stages) < 3:
        # Simple job — no Claude optimization needed
        return {
            "job_name": job.name,
            "taskflow": base_taskflow,
            "optimized": False,
            "claude_review": None
        }

    if client is None:
        client = ClaudeClient()

    task_list = "\n".join(
        f"{i+1}. {s.name} ({s.stage_type})"
        for i, s in enumerate(job.stages)
    )
    deps = "\n".join(
        f"  - {job.name} → {d}" for d in job.downstream_jobs
    ) or "  None specified"

    prompt = _PROMPT_TEMPLATE.format(task_list=task_list, dependencies=deps)
    api_result = client.call(prompt, "ACC-05-AI", "design_analysis")

    return {
        "job_name": job.name,
        "taskflow": base_taskflow,
        "optimized": True,
        "claude_review": api_result["content"],
        "api_call_metadata": {
            "model": api_result["model"],
            "tokens_input": api_result["tokens_input"],
            "tokens_output": api_result["tokens_output"],
            "cost_usd": api_result["cost_usd"],
            "latency_seconds": api_result["latency_seconds"]
        }
    }


def optimize_all(export: DSXExport, output_dir: str = "output/acc05_taskflow") -> list[dict]:
    """Optimize all Sequence Jobs in the export."""
    os.makedirs(output_dir, exist_ok=True)
    client = ClaudeClient()
    results = []

    for job in export.jobs:
        if job.job_type != "SEQUENCE_JOB":
            continue
        result = optimize(job, client)
        results.append(result)
        out_file = os.path.join(output_dir, f"{job.name}.json")
        with open(out_file, "w") as f:
            json.dump(result, f, indent=2, default=str)

    return results
