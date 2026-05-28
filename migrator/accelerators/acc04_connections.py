"""ACC-04: Connection Migration Mapper (rule-based).

Maps DataStage connection definitions to IDMC REST API JSON payloads.
"""

import json
import os
from migrator.core.dsx_parser import DSXExport

_CONNECTOR_MAP = {
    "DB2": "DB2",
    "Oracle": "Oracle",
    "ODBC": "ODBC",
    "SQLServer": "SqlServer",
    "Teradata": "Teradata",
    "Snowflake": "Snowflake",
    "BigQuery": "GoogleBigQuery",
    "FlatFile": "FlatFile",
    "SFTP": "SFTP",
    "S3": "AmazonS3"
}


def migrate(export: DSXExport, output_dir: str = "output/acc04_connections") -> list[dict]:
    """Convert all connections to IDMC format. Returns list of payloads."""
    os.makedirs(output_dir, exist_ok=True)
    results = []

    for conn in export.connections:
        payload = _build_payload(conn)
        results.append(payload)
        out_file = os.path.join(output_dir, f"{conn['name']}.json")
        with open(out_file, "w") as f:
            json.dump(payload, f, indent=2)

    return results


def _build_payload(conn: dict) -> dict:
    conn_type = _CONNECTOR_MAP.get(conn.get("type", ""), "Generic")
    return {
        "type": "Connection",
        "connectorType": conn_type,
        "name": conn["name"],
        "description": "Migrated from IBM DataStage",
        "properties": {
            "host": conn.get("host", ""),
            "port": conn.get("port", ""),
            "database": conn.get("database", ""),
            "username": conn.get("username", ""),
            "password": "@{CONN_PASSWORD}"
        }
    }
