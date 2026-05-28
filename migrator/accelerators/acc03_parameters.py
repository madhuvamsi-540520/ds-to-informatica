"""ACC-03: Parameter Set Migration Template (rule-based).

Converts DataStage parameter sets to IDMC REST API JSON payloads.
"""

import json
import os
from migrator.core.dsx_parser import DSXExport

_TYPE_MAP = {
    "String": "string",
    "Integer": "integer",
    "Float": "double",
    "Decimal": "decimal",
    "Date": "string",
    "Encrypted": "string",
    "PathName": "string",
    "ListValue": "string"
}


def migrate(export: DSXExport, output_dir: str = "output/acc03_parameters") -> list[dict]:
    """Convert all parameter sets to IDMC format. Returns list of payloads."""
    os.makedirs(output_dir, exist_ok=True)
    results = []

    for ps in export.parameter_sets:
        payload = _build_payload(ps)
        results.append(payload)
        out_file = os.path.join(output_dir, f"{ps['name']}.json")
        with open(out_file, "w") as f:
            json.dump(payload, f, indent=2)

    return results


def _build_payload(ps: dict) -> dict:
    params = []
    for p in ps.get("parameters", []):
        params.append({
            "name": p["name"],
            "dataType": _TYPE_MAP.get(p["type"], "string"),
            "defaultValue": p["default"],
            "isEncrypted": p["encrypted"],
            "description": f"Migrated from DataStage parameter set {ps['name']}"
        })

    return {
        "type": "ParameterSet",
        "name": ps["name"],
        "description": f"Migrated from IBM DataStage",
        "parameters": params
    }
