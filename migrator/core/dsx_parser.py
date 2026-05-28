"""Parse IBM DataStage DSX XML export files into Python objects."""

from dataclasses import dataclass, field
from lxml import etree


@dataclass
class DSXStage:
    name: str
    stage_type: str
    properties: dict = field(default_factory=dict)
    basic_routines: list[str] = field(default_factory=list)
    has_custom_operator: bool = False


@dataclass
class DSXJob:
    name: str
    job_type: str  # PARALLEL_JOB | SEQUENCE_JOB | SERVER_JOB
    stages: list[DSXStage] = field(default_factory=list)
    parameters: list[dict] = field(default_factory=list)
    connections: list[dict] = field(default_factory=list)
    upstream_jobs: list[str] = field(default_factory=list)
    downstream_jobs: list[str] = field(default_factory=list)


@dataclass
class DSXExport:
    jobs: list[DSXJob] = field(default_factory=list)
    parameter_sets: list[dict] = field(default_factory=list)
    connections: list[dict] = field(default_factory=list)
    routines: list[dict] = field(default_factory=list)


def parse(dsx_path: str) -> DSXExport:
    """Parse a DataStage DSX export file."""
    try:
        tree = etree.parse(dsx_path)
    except Exception as e:
        raise ValueError(f"Cannot parse DSX file '{dsx_path}': {e}")

    root = tree.getroot()
    export = DSXExport()

    for job_el in root.iter("Job"):
        job = _parse_job(job_el)
        export.jobs.append(job)

    for ps_el in root.iter("ParameterSet"):
        export.parameter_sets.append(_parse_parameter_set(ps_el))

    for conn_el in root.iter("Connection"):
        export.connections.append(_parse_connection(conn_el))

    for rt_el in root.iter("Routine"):
        export.routines.append({
            "name": rt_el.get("identifier", ""),
            "code": rt_el.findtext("SourceCode", default="")
        })

    return export


def _parse_job(job_el) -> DSXJob:
    name = job_el.get("identifier", "UnknownJob")
    job_type = _detect_job_type(job_el)
    job = DSXJob(name=name, job_type=job_type)

    for stage_el in job_el.iter("Stage"):
        stage = _parse_stage(stage_el)
        job.stages.append(stage)

    for param_el in job_el.iter("Parameter"):
        job.parameters.append({
            "name": param_el.get("identifier", ""),
            "type": param_el.get("parameterType", "String"),
            "default": param_el.get("default", ""),
            "encrypted": param_el.get("encrypted", "0") == "1"
        })

    # Extract upstream/downstream from Sequence Job activity links
    for link_el in job_el.iter("JobActivity"):
        ref = link_el.get("jobName", "")
        if ref:
            job.downstream_jobs.append(ref)

    return job


def _parse_stage(stage_el) -> DSXStage:
    name = stage_el.get("identifier", "UnknownStage")
    stage_type = stage_el.get("stageType", "Unknown")
    is_custom = stage_type in ("CustomStage", "BuildStage", "PluginStage")

    routines = []
    for expr_el in stage_el.iter("Expression"):
        code = (expr_el.text or "").strip()
        if code:
            routines.append(code)

    return DSXStage(
        name=name,
        stage_type=stage_type,
        has_custom_operator=is_custom,
        basic_routines=routines
    )


def _detect_job_type(job_el) -> str:
    job_type_attr = job_el.get("jobType", "")
    if "Parallel" in job_type_attr:
        return "PARALLEL_JOB"
    if "Sequence" in job_type_attr:
        return "SEQUENCE_JOB"
    return "SERVER_JOB"


def _parse_parameter_set(ps_el) -> dict:
    return {
        "name": ps_el.get("identifier", ""),
        "parameters": [
            {
                "name": p.get("identifier", ""),
                "type": p.get("parameterType", "String"),
                "default": p.get("default", ""),
                "encrypted": p.get("encrypted", "0") == "1"
            }
            for p in ps_el.iter("Parameter")
        ]
    }


def _parse_connection(conn_el) -> dict:
    return {
        "name": conn_el.get("identifier", ""),
        "type": conn_el.get("connectionType", ""),
        "host": conn_el.get("host", ""),
        "port": conn_el.get("port", ""),
        "database": conn_el.get("database", ""),
        "username": conn_el.get("username", "")
    }
