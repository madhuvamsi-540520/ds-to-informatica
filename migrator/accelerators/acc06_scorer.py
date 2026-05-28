"""ACC-06: Job Complexity Scorer (rule-based with optional Claude enhancement).

Scores each job by formula. Jobs scoring 30+ flagged for optional Claude review.
Scoring: 1pt/stage, 5pt/custom operator, 3pt/BASIC routine, 2pt/sequence job.
"""

import json
import os
import yaml
from pathlib import Path
from migrator.core.dsx_parser import DSXExport, DSXJob

_CONFIG_PATH = Path(__file__).parent.parent.parent / "config.yaml"


def _load_scoring_config() -> dict:
    with open(_CONFIG_PATH) as f:
        return yaml.safe_load(f).get("scoring", {})


def score_job(job: DSXJob, cfg: dict) -> dict:
    stage_count = len(job.stages)
    custom_op_count = sum(1 for s in job.stages if s.has_custom_operator)
    basic_routine_count = sum(len(s.basic_routines) for s in job.stages)
    is_sequence = 1 if job.job_type == "SEQUENCE_JOB" else 0

    score = (
        stage_count * cfg.get("points_per_stage", 1) +
        custom_op_count * cfg.get("points_per_custom_operator", 5) +
        basic_routine_count * cfg.get("points_per_basic_routine", 3) +
        is_sequence * cfg.get("points_per_sequence_job", 2)
    )

    complex_threshold = cfg.get("complex_threshold", 30)
    high_threshold = cfg.get("high_complexity_threshold", 50)

    if score >= high_threshold:
        complexity = "HIGH"
    elif score >= complex_threshold:
        complexity = "COMPLEX"
    elif score >= 10:
        complexity = "MEDIUM"
    else:
        complexity = "SIMPLE"

    return {
        "job_name": job.name,
        "job_type": job.job_type,
        "stage_count": stage_count,
        "custom_operator_count": custom_op_count,
        "basic_routine_count": basic_routine_count,
        "score": score,
        "complexity": complexity,
        "requires_claude_review": score >= complex_threshold,
        "has_basic_routines": basic_routine_count > 0,
        "has_custom_operators": custom_op_count > 0
    }


def score_all(export: DSXExport, output_dir: str = "output/acc06_scoring") -> list[dict]:
    """Score all jobs. Returns list of scoring results."""
    cfg = _load_scoring_config()
    os.makedirs(output_dir, exist_ok=True)
    results = [score_job(job, cfg) for job in export.jobs]

    out_file = os.path.join(output_dir, "complexity_scores.json")
    with open(out_file, "w") as f:
        json.dump(results, f, indent=2)

    return results
