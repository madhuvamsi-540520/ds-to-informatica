"""ACC-01: Stage-to-Transformation Classifier (rule-based).

Parses DSX export, maps every stage type to its IDMC equivalent.
Output: CSV with columns Stage Name | DS Type | IDMC Equivalent | Equivalency | Action
"""

import csv
import json
import os
from pathlib import Path
from migrator.core.dsx_parser import DSXExport

_MAPPING_PATH = Path(__file__).parent.parent / "data" / "stage_mapping.json"


def load_stage_mapping() -> dict:
    with open(_MAPPING_PATH) as f:
        return json.load(f)


def classify(export: DSXExport, output_path: str = "output/acc01_classification.csv") -> list[dict]:
    """Classify all stages in the DSX export. Returns list of classification rows."""
    mapping = load_stage_mapping()
    rows = []

    for job in export.jobs:
        for stage in job.stages:
            mapped = mapping.get(stage.stage_type, {
                "idmc_equivalent": "Unknown — Manual Review Required",
                "equivalency": "Manual",
                "action": "Review"
            })
            rows.append({
                "job_name": job.name,
                "stage_name": stage.name,
                "ds_type": stage.stage_type,
                "idmc_equivalent": mapped["idmc_equivalent"],
                "equivalency": mapped["equivalency"],
                "action": mapped["action"],
                "has_basic_routines": bool(stage.basic_routines),
                "has_custom_operator": stage.has_custom_operator
            })

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys() if rows else [])
        writer.writeheader()
        writer.writerows(rows)

    return rows


def get_job_flags(rows: list[dict]) -> dict[str, dict]:
    """Return per-job flags for use by Phase 2 accelerators."""
    flags: dict[str, dict] = {}
    for row in rows:
        job = row["job_name"]
        if job not in flags:
            flags[job] = {
                "has_basic_routines": False,
                "has_custom_operator": False,
                "manual_stages": []
            }
        if row["has_basic_routines"]:
            flags[job]["has_basic_routines"] = True
        if row["has_custom_operator"]:
            flags[job]["has_custom_operator"] = True
        if row["action"] == "Review":
            flags[job]["manual_stages"].append(row["stage_name"])
    return flags
