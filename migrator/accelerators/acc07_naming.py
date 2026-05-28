"""ACC-07: Naming Convention Transformer (rule-based).

Applies naming rules to DataStage job/stage names → IDMC conventions.
Output: old-name → new-name inventory CSV.
"""

import csv
import json
import os
import re
from pathlib import Path
from migrator.core.dsx_parser import DSXExport

_RULES_PATH = Path(__file__).parent.parent / "data" / "naming_rules.json"


def _load_rules() -> dict:
    with open(_RULES_PATH) as f:
        return json.load(f)


def transform_name(name: str, entity_type: str, rules: dict) -> str:
    result = name

    # Apply replacements (spaces, dashes → underscores)
    for old, new in rules.get("replacements", {}).items():
        result = result.replace(old, new)

    # Remove known DS prefixes
    prefix_rules = rules.get("prefixes", {}).get(entity_type, {})
    for prefix in prefix_rules.get("remove", []):
        if result.upper().startswith(prefix.upper()):
            result = result[len(prefix):]

    # Apply layer mapping
    for ds_layer, idmc_layer in rules.get("layer_mapping", {}).items():
        result = re.sub(rf"(?i)\b{ds_layer}\b", idmc_layer, result)

    # Add IDMC prefix
    add_prefix = prefix_rules.get("add", "")
    if add_prefix and not result.startswith(add_prefix):
        result = add_prefix + result

    # Apply snake_case if configured
    if rules.get("case") == "snake_case":
        result = re.sub(r"(?<=[a-z])(?=[A-Z])", "_", result).lower()
        result = re.sub(r"_+", "_", result)

    return result


def transform_all(export: DSXExport, output_dir: str = "output/acc07_naming") -> list[dict]:
    """Transform all names. Returns old→new inventory."""
    rules = _load_rules()
    os.makedirs(output_dir, exist_ok=True)
    rows = []

    for job in export.jobs:
        entity_type = "sequence" if job.job_type == "SEQUENCE_JOB" else "job"
        new_name = transform_name(job.name, entity_type, rules)
        rows.append({
            "entity_type": entity_type,
            "old_name": job.name,
            "new_name": new_name,
            "changed": job.name != new_name
        })

        for stage in job.stages:
            new_stage = transform_name(stage.name, "job", rules)
            rows.append({
                "entity_type": "stage",
                "old_name": stage.name,
                "new_name": new_stage,
                "changed": stage.name != new_stage
            })

    out_file = os.path.join(output_dir, "naming_inventory.csv")
    with open(out_file, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["entity_type", "old_name", "new_name", "changed"])
        writer.writeheader()
        writer.writerows(rows)

    return rows
