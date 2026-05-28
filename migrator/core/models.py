"""Pydantic models for all accelerator input/output schemas (spec Section 7.1)."""

from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, Field
import uuid


class ColumnDef(BaseModel):
    name: str
    type: str
    length: Optional[int] = None
    precision: Optional[int] = None
    format: Optional[str] = None


class ApiCallMetadata(BaseModel):
    model: str
    tokens_input: int
    tokens_output: int
    cost_usd: float
    latency_seconds: float


# ── ACC-02-AI ─────────────────────────────────────────────────────────────────

class Acc02Input(BaseModel):
    accelerator_id: str = "ACC-02-AI"
    job_id: str
    basic_code: str = Field(..., min_length=1, max_length=1000)
    column_context: dict[str, list[ColumnDef]]
    complexity_level: str = Field(..., pattern="^(SIMPLE|MEDIUM|COMPLEX)$")
    assumptions: list[str] = []
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class FunctionMapping(BaseModel):
    basic_function: str
    idmc_equivalent: str
    confidence: int = Field(..., ge=0, le=100)


class Acc02Output(BaseModel):
    accelerator_id: str = "ACC-02-AI"
    job_id: str
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    translated_expression: Optional[str] = None
    complexity_classification: str
    confidence_level: int = Field(..., ge=0, le=100)
    requires_human_review: bool
    assumptions_detected: list[str] = []
    function_mappings: list[FunctionMapping] = []
    warnings: list[str] = []
    estimated_review_time_minutes: int = 0
    api_call_metadata: Optional[ApiCallMetadata] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ── ACC-08-AI ─────────────────────────────────────────────────────────────────

class CppColumn(BaseModel):
    column_name: str
    cpp_type: str


class Acc08Constraints(BaseModel):
    may_use_file_io: bool = False
    may_use_network: bool = False
    target_java_version: str = Field("11", pattern="^(8|11|17|21)$")


class Acc08Input(BaseModel):
    accelerator_id: str = "ACC-08-AI"
    job_id: str
    operator_name: str
    cpp_source_code: str
    input_schema: list[CppColumn]
    output_schema: list[CppColumn]
    functional_specification: str
    edge_cases: list[str] = []
    external_dependencies: list[str] = []
    constraints: Acc08Constraints = Field(default_factory=Acc08Constraints)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class UnsupportedFeature(BaseModel):
    feature: str
    reason: str
    workaround: str


class JavaDependency(BaseModel):
    library: str
    version: str
    required: bool


class SuggestedTestCase(BaseModel):
    test_name: str
    input: dict[str, Any]
    expected_output: dict[str, Any]
    notes: str


class ReviewChecklistItem(BaseModel):
    item: str
    status: str  # REQUIRED | RECOMMENDED | OPTIONAL


class Acc08Output(BaseModel):
    accelerator_id: str = "ACC-08-AI"
    job_id: str
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    java_source_code: Optional[str] = None
    confidence_level: int = Field(..., ge=0, le=100)
    requires_human_review: bool
    unsupported_cpp_features: list[UnsupportedFeature] = []
    external_java_dependencies: list[JavaDependency] = []
    test_cases_suggested: list[SuggestedTestCase] = []
    warnings: list[str] = []
    review_checklist: list[ReviewChecklistItem] = []
    api_call_metadata: Optional[ApiCallMetadata] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ── ACC-09-AI ─────────────────────────────────────────────────────────────────

class SystemInfo(BaseModel):
    name: str
    type: str  # RDBMS | FLAT_FILE | CLOUD_API
    column_count: int


class Acc09Input(BaseModel):
    accelerator_id: str = "ACC-09-AI"
    job_id: str
    mapping_spec: dict[str, Any]
    load_volume_rows: int = Field(..., gt=0)
    sla_minutes: int = Field(..., gt=0)
    source_system: SystemInfo
    target_system: SystemInfo
    review_focus: list[str] = ["CRITICAL", "PERFORMANCE", "DESIGN", "SECURITY"]
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class Issue(BaseModel):
    issue_id: str
    severity: str  # CRITICAL | HIGH | MEDIUM | LOW
    category: str
    description: str
    impact: str
    affected_component: str
    suggested_fix: str
    fix_complexity: str  # TRIVIAL | SIMPLE | MEDIUM | COMPLEX


class BestPractice(BaseModel):
    category: str
    recommendation: str
    current_approach: str
    suggested_approach: str


class CriticalQuestion(BaseModel):
    question: str
    context: str


class ReviewSummary(BaseModel):
    total_issues: int
    critical_count: int
    high_count: int
    estimated_sla_impact: str
    confidence_level: int = Field(..., ge=0, le=100)


class Acc09Output(BaseModel):
    accelerator_id: str = "ACC-09-AI"
    job_id: str
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    issues_found: list[Issue] = []
    best_practices_found: list[BestPractice] = []
    critical_questions: list[CriticalQuestion] = []
    summary: ReviewSummary
    api_call_metadata: Optional[ApiCallMetadata] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ── ACC-10-AI ─────────────────────────────────────────────────────────────────

class JobNode(BaseModel):
    job_id: str
    job_name: str
    downstream_jobs: list[str] = []
    upstream_jobs: list[str] = []
    execution_time_minutes: int
    job_type: str  # PARALLEL_JOB | SEQUENCE_JOB | SERVER_JOB
    has_custom_operators: bool = False
    has_basic_routines: bool = False
    business_criticality: str  # CRITICAL | HIGH | MEDIUM | LOW


class BusinessContext(BaseModel):
    load_window_start_hour: int = Field(..., ge=0, le=23)
    load_window_end_hour: int = Field(..., ge=0, le=23)
    affected_reports_count: int
    sla_minutes: int


class MigrationConstraints(BaseModel):
    max_parallel_jobs: int
    max_wave_size: int
    pilot_job_count: int


class Acc10Input(BaseModel):
    accelerator_id: str = "ACC-10-AI"
    project_id: str
    job_dependency_graph: list[JobNode]
    business_context: BusinessContext
    migration_constraints: MigrationConstraints
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class MigrationWave(BaseModel):
    wave_id: int
    wave_name: str
    jobs: list[str]
    total_jobs: int
    estimated_execution_time_minutes: int
    critical_path_minutes: int
    sla_achievable: bool
    risk_level: str
    rollback_trigger: str


class OptimizationOpportunity(BaseModel):
    opportunity: str
    time_saving_minutes: int


class CriticalPathAnalysis(BaseModel):
    critical_path_jobs: list[str]
    total_critical_path_minutes: int
    optimization_opportunities: list[OptimizationOpportunity] = []


class HiddenDependency(BaseModel):
    job_a: str
    job_b: str
    dependency_type: str
    severity: str
    notes: str


class RollbackStrategy(BaseModel):
    parallel_run_recommended: bool
    shadow_traffic_recommended: bool
    switch_back_sla_minutes: int
    data_reconciliation_required: bool
    detailed_steps: list[str]


class RiskAssessment(BaseModel):
    total_risk_score: int = Field(..., ge=0, le=100)
    single_points_of_failure: list[str] = []
    mitigation_strategies: list[str] = []


class Acc10Output(BaseModel):
    accelerator_id: str = "ACC-10-AI"
    project_id: str
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    migration_wave_plan: list[MigrationWave]
    critical_path_analysis: CriticalPathAnalysis
    hidden_dependencies: list[HiddenDependency] = []
    rollback_strategy: RollbackStrategy
    risk_assessment: RiskAssessment
    api_call_metadata: Optional[ApiCallMetadata] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
