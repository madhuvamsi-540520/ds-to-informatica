# IBM DataStage → Informatica IDMC CDI Migration Platform
## End-to-End Technical Reference

> **Document Type:** Team Technical Reference  
> **Audience:** Engineers, Architects, QA, Product  
> **Status:** Backend complete. UI layer under development.  
> **Last Updated:** 2026-05-31  
> **Repository:** `ds_to_iformatica/`

---

## Table of Contents

1. [What This Platform Does](#1-what-this-platform-does)
2. [System Architecture Overview](#2-system-architecture-overview)
3. [Repository Structure](#3-repository-structure)
4. [What Is Already Built](#4-what-is-already-built)
5. [UI Layer — Status & Design](#5-ui-layer--status--design)
6. [The Ten Accelerators — Reference](#6-the-ten-accelerators--reference)
7. [Data Flow: End to End](#7-data-flow-end-to-end)
8. [Core Subsystems](#8-core-subsystems)
9. [Input / Output Contracts](#9-input--output-contracts)
10. [Error Handling & Circuit Breakers](#10-error-handling--circuit-breakers)
11. [Configuration Reference](#11-configuration-reference)
12. [Testing Strategy](#12-testing-strategy)
13. [Development Roadmap](#13-development-roadmap)
14. [Deployment & Operations](#14-deployment--operations)
15. [Cost Model](#15-cost-model)
16. [Human Review Process](#16-human-review-process)
17. [Quick-Start for New Engineers](#17-quick-start-for-new-engineers)
18. [Success Metrics & KPIs](#18-success-metrics--kpis)

**Appendices**
- [Appendix A: Accelerator Execution Order](#appendix-a-accelerator-execution-order-phase-dependencies)
- [Appendix B: Prompt Templates Reference](#appendix-b-prompt-templates-reference)
- [Appendix C: Acceptance Criteria per Accelerator](#appendix-c-acceptance-criteria-per-accelerator)
- [Appendix D: SDD Pre-Deployment Checklist](#appendix-d-sdd-pre-deployment-checklist)
- [Appendix E: Complete Workflow Example](#appendix-e-complete-workflow-example-500-job-estate)
- [Appendix F: Glossary](#appendix-f-glossary)

---

## 1. What This Platform Does

This platform automates migration of ETL jobs from **IBM DataStage** to **Informatica IDMC CDI**. DataStage exports a binary-ish XML format called DSX. IDMC uses REST API payloads and YAML/JSON mapping specifications.

The migration is inherently non-trivial because:

- DataStage BASIC routines (used inside Transformer stages) have no direct IDMC equivalent; they must be rewritten as Informatica expression-language expressions.
- DataStage custom stages written in C++ must be re-implemented as Java Transformations in IDMC.
- Sequence Jobs (DataStage's orchestration layer) must be converted to IDMC Taskflows, with dependencies re-evaluated.
- Job dependency graphs are often large (hundreds of jobs), and migration must be wave-planned to avoid breaking production runs.

**The platform solves this with a hybrid strategy:**

- **80% of work is rule-based** — deterministic Python scripts that read DSX XML and produce IDMC-ready outputs. No AI, zero cost, 100% reliable.
- **20% requires semantic understanding** — BASIC logic, C++ rewriting, design review, dependency impact. For this, the platform calls the Claude API.

The output is a set of structured artifacts (CSVs, JSONs, connection configs, Java code, migration wave plans) that an engineer imports into Informatica IDMC.

---

## 2. System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        User Interface (Web)                          │
│                   [Upload DSX] → [Trigger Migration]                 │
│                         → [Download Results]                         │
│          Status: Templated UI exists; backend integration pending    │
└────────────────────────────┬────────────────────────────────────────┘
                             │  HTTP / multipart upload
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      Migration Backend (Python)                      │
│                                                                      │
│  ┌─────────────────┐    ┌──────────────────┐    ┌────────────────┐  │
│  │  DSX Parser     │───▶│  Rule-Based      │───▶│  Claude API    │  │
│  │  (lxml XML)     │    │  Accelerators    │    │  Accelerators  │  │
│  │  dsx_parser.py  │    │  (ACC-01,03,04,  │    │  (ACC-02,05,   │  │
│  └─────────────────┘    │   06,07)         │    │   08,09,10)    │  │
│                         └──────────────────┘    └────────────────┘  │
│                                  │                      │            │
│                                  ▼                      ▼            │
│                         ┌─────────────────────────────────────────┐ │
│                         │           Output Directory              │ │
│                         │  acc01_classification.csv               │ │
│                         │  acc02_basic/<job_id>.json              │ │
│                         │  acc03_parameters/<ps_name>.json        │ │
│                         │  acc04_connections/<conn_name>.json     │ │
│                         │  acc06_scoring/complexity_scores.json   │ │
│                         │  acc07_naming/naming_inventory.csv      │ │
│                         │  acc08_cpp/<job_id>.json                │ │
│                         │  acc09_review/<job_id>.json             │ │
│                         │  acc10_dependency/wave_plan.json        │ │
│                         └─────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
                             │
                             ▼
                  ┌──────────────────────┐
                  │  Anthropic Claude    │
                  │  claude-sonnet-4-6   │
                  │  (API key required)  │
                  └──────────────────────┘
```

**Key design principle:** Every accelerator produces a `requires_human_review` flag. Output is never auto-deployed. Engineers review flagged outputs before any IDMC import.

---

## 3. Repository Structure

```
ds_to_iformatica/
│
├── migrator/                        # Main Python package
│   ├── __init__.py
│   ├── __main__.py                  # CLI entrypoint: python -m migrator <cmd>
│   │
│   ├── core/                        # Shared infrastructure
│   │   ├── claude_client.py         # Anthropic API wrapper (rate limiting, cost tracking, retries)
│   │   ├── dsx_parser.py            # Parses DataStage DSX XML → Python objects
│   │   ├── models.py                # Pydantic models for all input/output schemas
│   │   └── validator.py             # Pre-call and post-call validation
│   │
│   ├── accelerators/                # One file per accelerator
│   │   ├── acc01_classifier.py      # Stage type → IDMC equivalent (rule-based)
│   │   ├── acc02_basic.py           # BASIC → Informatica expression (hybrid)
│   │   ├── acc03_parameters.py      # Parameter sets → IDMC JSON (rule-based)
│   │   ├── acc04_connections.py     # Connections → IDMC payloads (rule-based)
│   │   ├── acc05_taskflow.py        # Sequence Job → Taskflow (hybrid)
│   │   ├── acc06_scorer.py          # Job complexity scoring (rule-based)
│   │   ├── acc07_naming.py          # Naming convention transformation (rule-based)
│   │   ├── acc08_cpp.py             # C++ operator → Java rewrite (Claude API)
│   │   ├── acc09_review.py          # Anti-pattern & design review (Claude API)
│   │   └── acc10_dependency.py      # Dependency & impact analysis (Claude API)
│   │
│   └── data/                        # Lookup tables (static reference data)
│       ├── stage_mapping.json       # DataStage stage type → IDMC equivalent
│       ├── basic_functions.json     # BASIC function → Informatica function
│       └── naming_rules.json        # Naming convention rules
│
├── tests/
│   ├── fixtures/
│   │   └── sample.dsx               # Sample DSX XML for tests
│   ├── test_acc01.py
│   ├── test_acc02_ai.py
│   └── test_acc06.py
│
├── output/                          # Generated outputs (gitignored in prod)
│   ├── acc01_classification.csv
│   ├── acc03_parameters/
│   ├── acc04_connections/
│   ├── acc06_scoring/
│   └── acc07_naming/
│
├── config.yaml                      # Model name, rate limits, cost thresholds, scoring weights
├── requirements.txt                 # Python dependencies
├── CLAUDE.md                        # Claude Code agent guidance
└── TECHNICAL_REFERENCE.md          # This document
```

---

## 4. What Is Already Built

### Backend — Complete

As of the latest commit (`536c472`), the full backend is implemented:

| Component | File | Status |
|---|---|---|
| DSX XML Parser | `core/dsx_parser.py` | Done |
| Pydantic Models (all schemas) | `core/models.py` | Done |
| Claude API Client | `core/claude_client.py` | Done |
| Input/Output Validator | `core/validator.py` | Done |
| ACC-01 Stage Classifier | `accelerators/acc01_classifier.py` | Done |
| ACC-02 BASIC Translator | `accelerators/acc02_basic.py` | Done |
| ACC-03 Parameter Migrator | `accelerators/acc03_parameters.py` | Done |
| ACC-04 Connection Mapper | `accelerators/acc04_connections.py` | Done |
| ACC-05 Taskflow Optimizer | `accelerators/acc05_taskflow.py` | Done |
| ACC-06 Complexity Scorer | `accelerators/acc06_scorer.py` | Done |
| ACC-07 Naming Transformer | `accelerators/acc07_naming.py` | Done |
| ACC-08 C++ Rewriter | `accelerators/acc08_cpp.py` | Done |
| ACC-09 Design Review | `accelerators/acc09_review.py` | Done |
| ACC-10 Dependency Analysis | `accelerators/acc10_dependency.py` | Done |
| CLI Entrypoint | `__main__.py` | Done (Phase 1 commands wired) |
| Stage Mapping Lookup Table | `data/stage_mapping.json` | Done |
| BASIC Function Lookup Table | `data/basic_functions.json` | Done |
| Naming Rules | `data/naming_rules.json` | Done |
| Tests (ACC-01, 02, 06) | `tests/` | Done (partial coverage) |

### What the CLI Can Do Today

```bash
# Run all Phase 1 rule-based accelerators against a DSX export
python -m migrator run --dsx path/to/export.dsx --output ./output/

# Classify stages only
python -m migrator acc01 --dsx path/to/export.dsx

# Score job complexity only
python -m migrator acc06 --dsx path/to/export.dsx
```

Phase 2 and Phase 3 accelerators (ACC-02, 05, 08, 09, 10) are fully implemented as Python functions and can be called programmatically. They are not yet wired into the CLI `run` command — that is a known gap.

### Existing Output Artifacts (from sample run)

```
output/acc01_classification.csv          # Stage classification for all jobs
output/acc03_parameters/PS_Database_Config.json
output/acc04_connections/CONN_Source_Oracle.json
output/acc04_connections/CONN_Target_Snowflake.json
output/acc06_scoring/complexity_scores.json
output/acc07_naming/naming_inventory.csv
```

---

## 5. UI Layer — Status & Design

### Current Status

A **match-templated UI has been built separately**. It provides:
- File upload form for DSX export file(s)
- Trigger to kick off migration pipeline
- Download area to retrieve migrated output artifacts

The UI backend integration — connecting the file upload to `python -m migrator run` and returning the output bundle — is **pending development** (see [Section 13 — Roadmap](#13-development-roadmap)).

### UI User Journey

```
1. User opens browser → navigates to migration tool URL
       │
       ▼
2. User uploads DSX export file (drag-and-drop or file picker)
   [Optional] User selects which accelerators to run
       │
       ▼
3. System processes:
   Phase 1 (rule-based, fast ~<30s):
     - Stage classification
     - Parameter migration
     - Connection mapping
     - Naming transformation
     - Complexity scoring
   Phase 2 (Claude API, ~1–5 min):
     - BASIC translation (for jobs with BASIC routines)
     - Taskflow optimization (for Sequence Jobs)
     - C++ rewriting (for custom operators)
     - Design review (for complex jobs)
   Phase 3 (Claude API, ~30s):
     - Dependency analysis + wave plan
       │
       ▼
4. User sees live progress updates (Phase 1 done, Phase 2 in progress...)
       │
       ▼
5. User downloads output ZIP containing:
   - acc01_classification.csv
   - acc02_basic/*.json
   - acc03_parameters/*.json
   - acc04_connections/*.json
   - acc06_scoring/complexity_scores.json
   - acc07_naming/naming_inventory.csv
   - acc08_cpp/*.json  (if C++ operators present)
   - acc09_review/*.json  (if complex jobs present)
   - acc10_dependency/wave_plan.json
   - migration_summary.html  (human-readable dashboard)
       │
       ▼
6. Engineer reviews flagged items (requires_human_review = true)
   and imports approved artifacts into IDMC.
```

### UI Integration Requirements

The UI must integrate with the migration backend through the following interface:

**Upload endpoint:**
```
POST /api/migrate
Content-Type: multipart/form-data

Fields:
  dsx_file: <file>                    # Required — DSX export XML
  accelerators: ["all" | list]        # Optional — default: all
  anthropic_api_key: <string>         # Optional — can also be env var
  project_id: <string>                # Optional — used in ACC-10 output

Response:
  202 Accepted
  { "job_id": "uuid", "status_url": "/api/jobs/{job_id}" }
```

**Status endpoint:**
```
GET /api/jobs/{job_id}

Response:
  { 
    "job_id": "uuid",
    "status": "pending | running | phase1_complete | phase2_complete | done | failed",
    "progress": { "phase1": true, "phase2": false, "phase3": false },
    "phase1_summary": { "jobs": 45, "stages": 312, "complex_jobs": 12 },
    "download_url": "/api/jobs/{job_id}/output"   (present when done)
  }
```

**Download endpoint:**
```
GET /api/jobs/{job_id}/output
Response: application/zip  (all output artifacts bundled)
```

---

## 6. The Ten Accelerators — Reference

### Decision: Rule-Based vs Claude API

| ACC | Name | Approach | Trigger Condition |
|---|---|---|---|
| **ACC-01** | Stage Classifier | Rule-Based | Always runs first |
| **ACC-02** | BASIC Translator | Hybrid | Job has BASIC routines |
| **ACC-03** | Parameter Migrator | Rule-Based | Always |
| **ACC-04** | Connection Mapper | Rule-Based | Always |
| **ACC-05** | Taskflow Optimizer | Hybrid | Job type = SEQUENCE_JOB |
| **ACC-06** | Complexity Scorer | Rule-Based | Always |
| **ACC-07** | Naming Transformer | Rule-Based | Always |
| **ACC-08** | C++ Rewriter | Claude API | Job has custom operator |
| **ACC-09** | Design Review | Claude API | Complexity score ≥ 30 OR has translations |
| **ACC-10** | Dependency Analysis | Claude API | Estate ≥ 5 jobs |

---

### ACC-01: Stage-to-Transformation Classifier

**What it does:** Reads every stage from every job in the DSX export. Looks up the DataStage stage type in `data/stage_mapping.json` to find the IDMC equivalent, equivalency level (Direct / Partial / Manual), and the recommended action.

**Why rule-based:** Every DataStage stage type has exactly one IDMC equivalent. No ambiguity.

**Input:** `DSXExport` object (from parser)  
**Output:** `output/acc01_classification.csv`  

| Column | Example |
|---|---|
| `job_name` | Load_Customer_Staging |
| `stage_name` | Src_OracleConnector |
| `ds_type` | OracleConnectorPX |
| `idmc_equivalent` | Oracle V2 Connector |
| `equivalency` | Direct |
| `action` | Migrate |
| `has_basic_routines` | false |
| `has_custom_operator` | false |

**Also outputs** per-job flags (used by Phase 2 to route jobs):
```python
{ "Load_Customer_Staging": { "has_basic_routines": True, "has_custom_operator": False, "manual_stages": [] } }
```

---

### ACC-02: BASIC Routine to Expression Translator

**What it does:** Converts DataStage BASIC transformer expressions to Informatica CDI expression language. Uses a lookup table for common functions; calls Claude for multi-line or custom logic.

**Hybrid routing logic:**
```
Is expression a single known function call (e.g., Trim(x), Upcase(x))?
  YES → Use lookup table → confidence 100, no review needed
  NO  → Call Claude API → confidence varies, review if < 80
```

**Input:** `Acc02Input` (job_id, basic_code, column_context, complexity_level)  
**Output:** `Acc02Output` (translated_expression, confidence_level, requires_human_review, assumptions_detected)

**Common function mappings:**

| BASIC Function | Informatica Equivalent |
|---|---|
| `Trim(x)` | `LTRIM(RTRIM(x))` |
| `Upcase(x)` | `UPPER(x)` |
| `Downcase(x)` | `LOWER(x)` |
| `Len(x)` | `LENGTH(x)` |
| `IsNull(x)` | `ISNULL(x)` |
| `Left(x,n)` | `SUBSTR(x,1,n)` |
| `Right(x,n)` | `SUBSTR(x,LENGTH(x)-n+1,n)` |
| `Change(x,a,b)` | `REPLACESTR(0,x,a,b)` |

**Claude handles:** Multi-line conditionals, custom business functions (`Apply_Discount`, `CalcHash`), expressions with record-level context.

**Example — Claude path:**
```
Input BASIC:
  If Credit_Limit > 50000 Then
      Apply_Discount(Base_Price, 0.15)
  Else If Credit_Limit > 10000 Then
      Apply_Discount(Base_Price, 0.05)
  Else Base_Price

Claude output:
  IIF(Credit_Limit > 50000, Base_Price * 0.85,
      IIF(Credit_Limit > 10000, Base_Price * 0.95, Base_Price))
  Assumptions: Apply_Discount(price, rate) = price * (1 - rate)
```

---

### ACC-03: Parameter Set Migration

**What it does:** Extracts DataStage parameter sets from DSX and converts them to IDMC-compatible JSON parameter files, suitable for import via IDMC REST API.

**Why rule-based:** Parameter structure (name, type, default, encrypted flag) maps directly.

**Output per parameter set:** `output/acc03_parameters/<ParameterSetName>.json`

```json
{
  "name": "PS_Database_Config",
  "parameters": [
    { "name": "DB_HOST", "type": "String", "default": "prod-db.internal", "encrypted": false },
    { "name": "DB_PASSWORD", "type": "String", "default": "", "encrypted": true }
  ]
}
```

---

### ACC-04: Connection Migration Mapper

**What it does:** Extracts DataStage connection definitions from DSX and converts them to IDMC REST API JSON payloads for the Connection object.

**Output per connection:** `output/acc04_connections/<ConnectionName>.json`

```json
{
  "name": "CONN_Source_Oracle",
  "type": "ORACLE",
  "host": "<<DB_HOST>>",
  "port": "1521",
  "database": "PROD",
  "username": "<<DB_USER>>"
}
```

Sensitive values are templated as `<<PARAM_NAME>>` — engineer fills in actuals during IDMC import.

---

### ACC-05: Sequence Job → Taskflow Optimizer

**What it does:** Converts DataStage Sequence Jobs to IDMC Taskflow structure. Rule-based phase handles the structural conversion (Job Activity → Mapping Task, Routine Activity → Command Task). Claude phase optionally optimizes the execution order — identifies parallelism opportunities, flags missing error handling.

**Output:** Taskflow spec JSON + Claude recommendations (if triggered).

---

### ACC-06: Job Complexity Scorer

**What it does:** Assigns a numeric complexity score to each job using a fixed formula:

```
Score = (stages × 1) + (custom_operators × 5) + (basic_routines × 3) + (sequence_job × 2)

Thresholds:
  < 15  → LOW
  15–29 → MEDIUM
  30–49 → HIGH
  50+   → VERY HIGH (requires_claude_review = true)
```

**Output:** `output/acc06_scoring/complexity_scores.json` — drives which jobs get routed to ACC-08, ACC-09.

---

### ACC-07: Naming Convention Transformer

**What it does:** Applies naming convention rules from `data/naming_rules.json` to all job names, stage names, and parameter names. Produces an old-name → new-name inventory.

**Output:** `output/acc07_naming/naming_inventory.csv`

| `original_name` | `new_name` | `changed` | `rule_applied` |
|---|---|---|---|
| load_cust_stg | LOAD_CUST_STG | true | uppercase_job_names |
| Source_Oracle | SRC_Oracle_V2 | true | prefix_standardize |

---

### ACC-08: Custom C++ Operator Code Rewriter

**What it does:** Translates DataStage custom operators (written in C++) to Java code for IDMC Java Transformation. This is fully Claude-driven — no rule-based equivalent exists.

**Input:** C++ source code + input/output schema + functional specification  
**Output:** Complete Java class + unsupported features list + test cases + review checklist

**IDMC constraints applied:**
- No file I/O (flagged if present)
- No network calls (flagged if present)
- Java 11+ target
- Thread-safe required

**When NOT to use:** Operator < 50 lines (manual rewrite is faster); operator uses DataStage-specific APIs with no Java equivalent.

---

### ACC-09: Anti-Pattern Detection & Design Review

**What it does:** Reviews generated IDMC mapping specs for issues. First pass is rule-based (hard-coded values, missing error handling, unmatched joins). Second pass sends the spec to Claude for semantic review.

**Severity levels:**

| Severity | Meaning | Deployment gate |
|---|---|---|
| CRITICAL | Security risk, data loss, hard-coded credentials | Blocks deployment |
| HIGH | Missing error handling, SLA risk | Requires review within 24h |
| MEDIUM | Performance issue, design smell | Requires review within 48h |
| LOW | Style, documentation | FYI; proceed if confident |

**Triggered for:** Any job with complexity score ≥ 30, any job with C++ translations, any job with multiple BASIC translations.

---

### ACC-10: Job Dependency & Impact Analysis

**What it does:** Ingests the full job dependency graph and uses Claude to produce a migration wave plan, critical path analysis, hidden dependency detection, and rollback strategy.

**Output structure:**
```json
{
  "migration_wave_plan": [
    { "wave_id": 0, "wave_name": "Pilot: High Confidence Jobs", "jobs": [...], "sla_achievable": true },
    { "wave_id": 1, "wave_name": "Wave 1: Core Staging Layer", "jobs": [...] }
  ],
  "critical_path_analysis": { "critical_path_jobs": [...], "optimization_opportunities": [...] },
  "hidden_dependencies": [...],
  "rollback_strategy": { "parallel_run_recommended": true, "detailed_steps": [...] }
}
```

**Guard:** Circular dependency detection runs before Claude call. If a cycle exists (A → B → C → A), the accelerator raises `CircularDependencyError` and halts. The cycle must be resolved in DataStage first.

---

## 7. Data Flow: End to End

```
┌──────────────────┐
│  DataStage DSX   │  (XML export, contains jobs, stages, parameters, connections, routines)
│  export.dsx      │
└────────┬─────────┘
         │
         ▼ dsx_parser.py
┌──────────────────┐
│  DSXExport obj   │  (Python dataclasses: jobs[], parameter_sets[], connections[], routines[])
└────────┬─────────┘
         │
    ─────┼──────────────────────────────────────────────────────────
    │    │  PHASE 1 — Rule-Based (all run in parallel, no dependencies)
    │    ├──▶ ACC-01 ─────────▶ acc01_classification.csv
    │    ├──▶ ACC-03 ─────────▶ acc03_parameters/*.json
    │    ├──▶ ACC-04 ─────────▶ acc04_connections/*.json
    │    ├──▶ ACC-06 ─────────▶ acc06_scoring/complexity_scores.json
    │    └──▶ ACC-07 ─────────▶ acc07_naming/naming_inventory.csv
    │
    │  PHASE 2 — Hybrid/Claude (depends on ACC-01 job flags)
    │    ├──▶ ACC-02 (if BASIC_ROUTINE_FLAG) ─▶ acc02_basic/*.json
    │    ├──▶ ACC-05 (if SEQUENCE_JOB)       ─▶ acc05_taskflow/*.json
    │    ├──▶ ACC-08 (if CUSTOM_OP_FLAG)     ─▶ acc08_cpp/*.json
    │    └──▶ ACC-09 (after ACC-02 + ACC-08) ─▶ acc09_review/*.json
    │
    │  PHASE 3 — Strategic Analysis (once, after Phase 1 + 2)
    │    └──▶ ACC-10 ─────────────────────────▶ acc10_dependency/wave_plan.json
    │
    ▼
┌──────────────────────────────────────────┐
│  Human Review Layer                       │
│  - All requires_human_review=true items  │
│  - Critical issues from ACC-09           │
│  - Wave plan sign-off from ACC-10        │
└────────────────────┬─────────────────────┘
                     │
                     ▼
             IDMC REST API Import
```

---

## 8. Core Subsystems

### 8.1 DSX Parser (`core/dsx_parser.py`)

Parses DataStage DSX XML using `lxml`. Produces three dataclass types:

- `DSXStage` — name, stage_type, basic_routines[], has_custom_operator
- `DSXJob` — name, job_type (PARALLEL_JOB | SEQUENCE_JOB | SERVER_JOB), stages[], parameters[], upstream_jobs[], downstream_jobs[]
- `DSXExport` — jobs[], parameter_sets[], connections[], routines[]

Job type detection is heuristic: checks the `jobType` attribute on the Job element for "Parallel" or "Sequence" keywords.

BASIC routines are extracted from `<Expression>` child elements of each stage. Custom operators are detected when `stageType` is `CustomStage`, `BuildStage`, or `PluginStage`.

### 8.2 Claude Client (`core/claude_client.py`)

Single shared wrapper for all Claude API calls. Responsibilities:

**Rate limiting:** Tracks request timestamps in a rolling 60-second window. If `requests_per_minute` is reached, sleeps until the window clears.

**Cost tracking:** Calculates cost per call as `(tokens_in × $3 + tokens_out × $15) / 1,000,000`. If cost exceeds the per-accelerator circuit breaker threshold (from `config.yaml`), raises `CostThresholdError` — the call is NOT made.

**Retries:** On `RateLimitError` (429) or `APITimeoutError` (504), retries with exponential backoff (`60 × 2^n` seconds). Max 3 retries.

**Temperature:** Reads from `config.yaml` per task type — 0.0 for code translation (ACC-02, ACC-08), 0.2 for analysis (ACC-09, ACC-10).

**Model:** Reads `claude.model` from `config.yaml`. Currently `claude-sonnet-4-6`.

### 8.3 Validator (`core/validator.py`)

Called before and after every Claude API call to enforce the contracts in the spec (Section 7.1 and 7.6).

- **Pre-call:** Validates `basic_code` length, `job_id` uniqueness, enum values, schema completeness.
- **Post-call:** Validates that `translated_expression` is syntactically plausible, `confidence_level` is 0–100, `requires_human_review` is set correctly, cost is within threshold.

Raises typed exceptions: `InputValidationError`, `OutputValidationError`, `CostThresholdError`.

### 8.4 Models (`core/models.py`)

Pydantic v2 models for all 10 accelerators' input and output schemas. Enforces field constraints at instantiation time (e.g., `basic_code: str = Field(..., min_length=1, max_length=1000)`).

Key models:
- `Acc02Input` / `Acc02Output` — BASIC translation
- `Acc08Input` / `Acc08Output` — C++ rewriting
- `Acc09Input` / `Acc09Output` — Design review
- `Acc10Input` / `Acc10Output` — Dependency analysis
- `ApiCallMetadata` — Embedded in all Claude-touching outputs (model, tokens, cost, latency)

---

## 9. Input / Output Contracts

### ACC-02 (BASIC Translator)

**Input:**
```json
{
  "accelerator_id": "ACC-02-AI",
  "job_id": "JOB_001",
  "basic_code": "Trim(Upcase(Customer_Name))",
  "column_context": {
    "input_columns": [{ "name": "Customer_Name", "type": "VARCHAR", "length": 100 }],
    "output_columns": [{ "name": "Customer_Name_Clean", "type": "VARCHAR", "length": 100 }]
  },
  "complexity_level": "SIMPLE",
  "timestamp": "2026-05-31T10:00:00Z"
}
```

**Output:**
```json
{
  "accelerator_id": "ACC-02-AI",
  "job_id": "JOB_001",
  "request_id": "uuid",
  "translated_expression": "UPPER(LTRIM(RTRIM(Customer_Name)))",
  "complexity_classification": "SIMPLE",
  "confidence_level": 100,
  "requires_human_review": false,
  "assumptions_detected": [],
  "function_mappings": [
    { "basic_function": "Upcase", "idmc_equivalent": "UPPER({})", "confidence": 100 },
    { "basic_function": "Trim",   "idmc_equivalent": "LTRIM(RTRIM({}))", "confidence": 100 }
  ],
  "warnings": [],
  "estimated_review_time_minutes": 0,
  "api_call_metadata": null,
  "timestamp": "2026-05-31T10:00:01Z"
}
```

### ACC-10 (Wave Plan)

**Input:** Full job graph (see `Acc10Input` model in `core/models.py`)  
**Output includes:**
- `migration_wave_plan[]` — ordered list of waves with job lists, SLA achievability, rollback triggers
- `critical_path_analysis` — jobs on critical path, optimization opportunities
- `hidden_dependencies[]` — implicit couplings Claude identified
- `rollback_strategy` — parallel run recommendation, step-by-step rollback instructions
- `risk_assessment` — total risk score, single points of failure, mitigations

Full JSON schema in `core/models.py:Acc10Output`.

---

## 10. Error Handling & Circuit Breakers

| Error | HTTP Code | Retry | Notes |
|---|---|---|---|
| Invalid input schema | 400 | No | Client must fix |
| API rate limit (429) | 429 | Yes — exponential backoff | Max 3 retries |
| API timeout (504) | 504 | Yes — 30s wait | Max 2 retries |
| Model unavailable (503) | 503 | Yes — 5 min wait | Fallback model if available |
| Cost threshold exceeded | 402 | No | Circuit breaker; requires approval |
| Token limit exceeded | 400 | No | Must reduce input |
| Circular dependency (ACC-10) | 400 | No | Manual intervention in DataStage |
| Claude output invalid | 500 | Once — 10s wait | Logged for investigation |

**Cost circuit breakers (from `config.yaml`):**

| Accelerator | Max cost per call |
|---|---|
| ACC-02 | $0.10 |
| ACC-08 | $0.15 |
| ACC-09 | $0.20 |
| ACC-10 | $0.15 |

If a call would exceed these limits, `CostThresholdError` is raised and the call is not made. The accelerator returns `requires_human_review: true` with the error context.

---

## 11. Configuration Reference

File: `config.yaml`

```yaml
claude:
  model: claude-sonnet-4-6          # Anthropic model ID
  temperature:
    code_translation: 0.0           # ACC-02, ACC-08 — deterministic
    design_analysis: 0.2            # ACC-09, ACC-10 — light creativity
  max_tokens:
    basic_translation: 1024
    cpp_rewriting: 2048
    design_review: 2048
    dependency_analysis: 2048
  rate_limit:
    requests_per_minute: 10
    batch_delay_seconds: 60
  retries: 3
  timeout_seconds: 60

cost_circuit_breaker:
  acc02: 0.10                       # Per-call $ ceiling
  acc08: 0.15
  acc09: 0.20
  acc10: 0.15

confidence_threshold: 80            # Below this → requires_human_review = true

scoring:
  points_per_stage: 1
  points_per_custom_operator: 5
  points_per_basic_routine: 3
  points_per_sequence_job: 2
  complex_threshold: 30             # Score ≥ 30 → HIGH; triggers ACC-09
  high_complexity_threshold: 50     # Score ≥ 50 → VERY HIGH

output_dir: output
```

**Environment variables:**
```bash
ANTHROPIC_API_KEY=sk-ant-...        # Required for any Claude-API accelerators
```

> **Model name note:** The original spec (`ibm-infa-etl-migration-ai-spec.md`) references `claude-3-5-sonnet-20241022` in its prompt examples and cost tables. The actual deployed model is `claude-sonnet-4-6` (set in `config.yaml`). All cost estimates and temperature settings in this document reflect the live config. The spec's model references are outdated and should be read as illustrative only.

---

## 12. Testing Strategy

### Current Test Coverage

| Test File | What It Covers |
|---|---|
| `tests/test_acc01.py` | Stage classification, CSV output, unknown stage types |
| `tests/test_acc02_ai.py` | Lookup table hits, Claude mock paths, confidence thresholds |
| `tests/test_acc06.py` | Scoring formula, threshold boundaries, requires_claude_review flag |

### Running Tests

```bash
# All tests
pytest tests/

# Single accelerator
pytest tests/test_acc01.py -v
pytest tests/test_acc02_ai.py -v

# With coverage
pytest tests/ --cov=migrator --cov-report=term-missing
```

### Test Patterns

**Rule-based accelerators** use `tests/fixtures/sample.dsx` (real DSX XML) for integration-style tests. No mocking needed.

**Claude API accelerators** mock `ClaudeClient.call()` using `pytest-mock`. Tests validate that the correct prompt is constructed and that the response parser handles all output sections (TRANSLATED EXPRESSION, ASSUMPTIONS, CONFIDENCE).

### Tests Still Needed

Tests are missing for:
- ACC-03 (parameter migration)
- ACC-04 (connection mapping)
- ACC-05 (taskflow optimizer)
- ACC-07 (naming transformer)
- ACC-08 (C++ rewriter) — needs fixture C++ operator
- ACC-09 (design review) — needs fixture mapping YAML
- ACC-10 (dependency analysis) — needs fixture job graph JSON
- `core/validator.py` — pre/post call validation edge cases
- `core/dsx_parser.py` — malformed XML, missing attributes

### Test Case Matrix (from spec — 10 cases per AI accelerator)

See `ibm-infa-etl-migration-ai-spec.md` Section 7.2 for the full matrix. Key edge cases to cover for each AI accelerator:

- Empty / too-large input (validation error)
- Unsupported function (graceful degradation, review flag)
- Circular dependency in graph (hard error, no API call)
- Low confidence (<50) — should block auto-deploy
- Cost threshold exceeded — should not make the call

---

## 13. Development Roadmap

> **Phasing terminology note:** The original spec (Section 5.1) also uses "Phase 1–4" to describe the *accelerator rollout order* during a live migration project (e.g., "Week 1–2: deploy rule-based accelerators"). That is a different concept from the development phases below. To avoid confusion: phases below = **development work remaining**; spec's phases = **how to run the tool on a client engagement**.

### Phase 1: Backend Polish (Current Sprint)

| Task | Owner | Status |
|---|---|---|
| Wire ACC-02, 05, 08, 09, 10 into `python -m migrator run` CLI | BE | Pending |
| Add `--api-key` flag to CLI (or read from env) | BE | Pending |
| Add `--phase` flag to run only Phase 1, or Phase 1+2, etc. | BE | Pending |
| Add missing tests for ACC-03, 04, 05, 07, 08, 09, 10 | BE/QA | Pending |
| Add `migration_summary.json` output (totals, flags, cost) | BE | Pending |
| Validate `stage_mapping.json` covers all known DataStage stage types | Data | Pending |
| Expand `basic_functions.json` with remaining BASIC functions | Data | Pending |

### Phase 2: UI Integration

| Task | Owner | Status |
|---|---|---|
| Stand up API server (FastAPI recommended) | BE | Pending |
| Implement `POST /api/migrate` — accept DSX upload, start async job | BE | Pending |
| Implement `GET /api/jobs/{job_id}` — status polling | BE | Pending |
| Implement `GET /api/jobs/{job_id}/output` — ZIP download | BE | Pending |
| Connect templated UI upload form to `POST /api/migrate` | FE | Pending |
| Add SSE or WebSocket for live progress updates in UI | FE | Pending |
| Add review dashboard in UI — list flagged items with approve/reject | FE | Pending |
| Generate `migration_summary.html` in output bundle | BE | Pending |

### Phase 3: Production Hardening

| Task | Owner | Status |
|---|---|---|
| Persist jobs to database (SQLite for single-node; Postgres for scale) | BE | Pending |
| Add authentication to API (API key or SSO) | BE | Pending |
| Add background task queue (Celery + Redis, or simple thread pool) | BE | Pending |
| Add structured logging (JSON logs with job_id, accelerator, cost) | BE | Pending |
| Add Prometheus metrics (request count, latency, cost per accelerator) | BE | Pending |
| Add output cleanup (auto-delete old job outputs after N days) | BE | Pending |
| Add IDMC REST API integration — auto-import approved artifacts | BE | Stretch |

### Phase 4: Pilot Migration (Field Use)

| Task | Owner | Status |
|---|---|---|
| Run tool against pilot customer DSX (5–10 jobs) | Eng + PM | Pending |
| Validate ACC-01 output against manual review | QA | Pending |
| Validate ACC-02 output — QA BASIC translations | QA | Pending |
| Collect Claude API cost actuals — compare to $0.004/job estimate | PM | Pending |
| Iterate on prompt templates based on review findings | Eng | Pending |
| Document lessons learned | PM | Pending |

---

## 14. Deployment & Operations

### Local Development

```bash
# Clone and install
git clone <repo>
cd ds_to_iformatica
pip install -r requirements.txt

# Set API key
export ANTHROPIC_API_KEY=sk-ant-...

# Run against sample DSX
python -m migrator run --dsx tests/fixtures/sample.dsx --output ./output/
```

### Recommended Stack for API Deployment

```
FastAPI (Python 3.11+)
  └── Background tasks: asyncio or Celery
  └── Storage: local disk (dev) / S3 / GCS (prod)
  └── Database: SQLite (dev) / Postgres (prod)
  └── Auth: API key header

Docker (single container for dev, compose for prod)
  migrator:latest
  └── CMD: uvicorn migrator.api:app --host 0.0.0.0 --port 8000
```

### Environment Variables Required

```bash
ANTHROPIC_API_KEY=sk-ant-...       # Required
OUTPUT_DIR=/tmp/migrator-output    # Optional; default: ./output
LOG_LEVEL=INFO                     # Optional; default: INFO
MAX_UPLOAD_SIZE_MB=100             # Optional; default: 50
```

### Resource Estimates

| Resource | Small Estate (<50 jobs) | Large Estate (500 jobs) |
|---|---|---|
| CPU | < 1 core | 2–4 cores |
| Memory | < 512 MB | 1–2 GB |
| Disk | < 100 MB output | < 1 GB output |
| API calls to Claude | 0–20 | 50–200 |
| Wall time | < 5 min | 30–60 min |
| Cost | < $0.50 | < $15 |

---

## 15. Cost Model

**Claude API pricing (current as of 2026-05):**
- Input tokens: $3 per million
- Output tokens: $15 per million

**Per-job cost estimates:**

| Accelerator | Avg input tokens | Avg output tokens | Cost/call |
|---|---|---|---|
| ACC-02 (BASIC translation) | 500 | 300 | $0.002 |
| ACC-08 (C++ rewriting) | 3,000 | 2,000 | $0.039 |
| ACC-09 (design review) | 2,000 | 1,500 | $0.029 |
| ACC-10 (dependency analysis) | 1,500 | 2,000 | $0.035 |

**500-job estate estimate (80/20 hybrid):**

| Component | Jobs affected | Cost |
|---|---|---|
| Rule-based (ACC-01, 03, 04, 06, 07) | 500 | $0.00 |
| BASIC translation (50% of jobs) | 250 | $0.50 |
| C++ rewriting (10% of jobs) | 50 | $1.95 |
| Design review (30% of jobs) | 150 | $4.35 |
| Dependency analysis (once) | 1 | $0.07 |
| **Total** | | **~$6.87** |

This is well within the spec's $15 ceiling. The cost circuit breakers in `config.yaml` prevent runaway spend on any single call.

---

## 16. Human Review Process

All Claude API outputs carry a `requires_human_review` flag. The system never auto-deploys to IDMC.

### Review Triage

| Flag | Condition | Review SLA | Reviewer |
|---|---|---|---|
| `requires_human_review = false` | Confidence ≥ 80, no assumptions | None | Auto-approve |
| `requires_human_review = true` | Confidence < 80 OR assumptions detected | 24 hours | Mid-level engineer |
| ACC-09 CRITICAL issue | Hard-coded credentials, data loss risk | 4 hours | Senior architect |
| ACC-09 HIGH issue | Missing error handling, SLA risk | 24 hours | Mid-level engineer |

### Review Checklist

For each flagged output, the reviewing engineer should verify:

```
[ ] Logic is correct — matches DataStage intent
[ ] Syntax is valid — expression parses in IDMC
[ ] No assumptions conflict with actual data context
[ ] Performance impact is acceptable
[ ] Error handling is complete
[ ] Output matches input schema
[ ] Sensitive values are parametrized (not hard-coded)

Approved by: [Name]  |  Date: [YYYY-MM-DD]
```

---

## 17. Quick-Start for New Engineers

### "I just joined, how do I run this locally?"

```bash
# 1. Set up Python environment
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2. Set your Anthropic API key (only needed for AI accelerators)
export ANTHROPIC_API_KEY=sk-ant-...

# 3. Run Phase 1 on sample data
python -m migrator run --dsx tests/fixtures/sample.dsx --output ./output/

# 4. Check outputs
ls -la output/
cat output/acc01_classification.csv
cat output/acc06_scoring/complexity_scores.json

# 5. Run tests
pytest tests/ -v
```

### "How do I add a new BASIC function to the lookup table?"

Edit `migrator/data/basic_functions.json`. Format: `"BasicFunctionName": "IDMC_TEMPLATE({0}, ...)"`. Use `{0}`, `{1}`, ... as positional argument placeholders (Python `.format()` syntax). Add a test case to `tests/test_acc02_ai.py`.

### "How do I add a new DataStage stage type to the mapping?"

Edit `migrator/data/stage_mapping.json`. Each entry:
```json
"StageTypeName": {
  "idmc_equivalent": "IDMC Connector or Transformation Name",
  "equivalency": "Direct | Partial | Manual",
  "action": "Migrate | Review | Rewrite"
}
```

### "How do I call an AI accelerator from Python?"

```python
from migrator.accelerators.acc02_basic import translate
from migrator.core.models import Acc02Input, ColumnDef

result = translate(Acc02Input(
    job_id="JOB_001",
    basic_code="Trim(Upcase(Customer_Name))",
    column_context={
        "input_columns": [ColumnDef(name="Customer_Name", type="VARCHAR", length=100)],
        "output_columns": [ColumnDef(name="Customer_Name_Clean", type="VARCHAR", length=100)]
    },
    complexity_level="SIMPLE"
))

print(result.translated_expression)   # UPPER(LTRIM(RTRIM(Customer_Name)))
print(result.requires_human_review)   # False
```

### "What's the next thing to work on?"

1. Wire ACC-02 through ACC-10 into the `python -m migrator run` command (they're implemented, just not connected in `__main__.py`).
2. Add the missing tests (ACC-03 through ACC-10).
3. Build the API server so the UI can talk to the backend.

See [Section 13 — Development Roadmap](#13-development-roadmap) for the full prioritized list.

---

## 18. Success Metrics & KPIs

Track these KPIs at the end of each migration engagement to measure platform effectiveness. These are the formal targets from the spec.

| Metric | Target | What it means if missed |
|---|---|---|
| **Rule-Based Coverage** | ≥ 80% of jobs handled without AI | More Claude calls = higher cost and review burden |
| **Claude Translation Accuracy** | ≥ 85% pass QA on first try | Low accuracy means prompt tuning is needed |
| **Cost per Job** | < $0.05 | Hybrid approach should keep 500-job estate under $25 total |
| **Human Review Time** | < 2 hours per 10 complex jobs | Higher means Claude output quality is too low |
| **Wave Execution Time vs DataStage** | < 20% longer in IDMC | IDMC design is inefficient; revisit ACC-09 recommendations |
| **Production SLA Met** | 100% | Zero unplanned failures due to migration error |

**How to track:** After each engagement, run a retrospective against these numbers. If accuracy falls below 85%, review and iterate on the prompt templates (see Appendix C).

---

## Appendix A: Accelerator Execution Order (Phase Dependencies)

```
PHASE 1 — Parallel, no dependencies
  ACC-01  ACC-03  ACC-04  ACC-06  ACC-07
     │
     │  (Phase 1 completes; job flags available)
     ▼
PHASE 2 — Parallel, depend on ACC-01 flags
  ACC-02 (if BASIC_FLAG)
  ACC-05 (if SEQUENCE_FLAG)
  ACC-08 (if CUSTOM_OP_FLAG)
  ACC-09 (after ACC-02 and ACC-08 for same job)
     │
     │  (Phase 2 completes; translations + reviews available)
     ▼
PHASE 3 — Single call, depends on all prior phases
  ACC-10

     │
     ▼
PHASE 4 — Human review + IDMC import (per wave)
  Wave 0 → Wave 1 → Wave N
```

**Hard stops that block execution:**
- Circular dependency in job graph → ACC-10 halts (resolve in DataStage first)
- CRITICAL issue from ACC-09 → blocks wave deployment until resolved
- Confidence < 50 on ACC-02 output → auto-deploy blocked; senior engineer review required

---

## Appendix B: Prompt Templates Reference

These are the exact prompts used inside each AI accelerator. Engineers debugging output quality or writing new test cases should start here. Each prompt is also embedded in the relevant accelerator Python file.

### ACC-02: BASIC Routine Translation

```
You are an ETL migration specialist fluent in DataStage BASIC and Informatica expression languages.

Convert this DataStage BASIC Transformer expression to Informatica CDI expression language.

BASIC Expression:
---
{basic_code}
---

Column Context:
- Input columns: {input_columns}
- Output columns: {output_columns}

Translation Rules:
1. Use Informatica built-in functions only (no custom Java unless necessary)
2. Handle NULLs safely (use IIF + ISNULL)
3. Preserve exact business logic
4. Provide assumptions if you make any

Output format (STRICT — no extra text):
TRANSLATED EXPRESSION:
[expression here]

ASSUMPTIONS:
[list assumptions or write NONE]

REVIEW NOTES:
[flag anything needing engineer check or write NONE]

CONFIDENCE: [0-100]
```

**Temperature:** 0.0 (deterministic)  
**Max tokens:** 1024  
**File:** `migrator/accelerators/acc02_basic.py`

---

### ACC-05: Sequence Job → Taskflow Optimizer

```
You are an ETL orchestration specialist. Review this Taskflow execution plan and suggest optimizations.

Current Taskflow (sequential):
{task_list_with_times}

Constraints:
{dependency_constraints}

Questions:
1. Which tasks can run in parallel?
2. What is the critical path?
3. Are there missing error recovery steps?
4. Should we add checkpoints?

Respond in structured format: Optimized Order, Parallelism, Error Handling Gaps.
```

**Temperature:** 0.2  
**Max tokens:** 2048  
**File:** `migrator/accelerators/acc05_taskflow.py`

---

### ACC-08: C++ Operator → Java Rewriter

```
You are a bilingual Java/C++ developer specializing in data transformation algorithms.

Convert this C++ DataStage custom operator to Java for Informatica CDI Java Transformation.

C++ Operator Source:
---
{cpp_source_code}
---

Functional Specification:
- Purpose: {functional_specification}
- Input schema: {input_schema}
- Output schema: {output_schema}
- Known edge cases: {edge_cases}

Constraints:
1. Target: Java {target_java_version}+
2. Must run in IDMC containerized environment (no file I/O, limited network)
3. Should use Informatica Java API if available
4. Thread-safe preferred (may process in parallel)

Output format:
JAVA CODE:
[Complete, runnable Java class]

ASSUMPTIONS:
[Any assumptions about input data or environment]

UNSUPPORTED FEATURES:
[List any C++ features that don't have direct Java equivalents; recommend workarounds]

EXTERNAL DEPENDENCIES:
[List any external libraries; flag if unavailable in IDMC runtime]
```

**Temperature:** 0.0 (deterministic)  
**Max tokens:** 2048  
**File:** `migrator/accelerators/acc08_cpp.py`

---

### ACC-09: Anti-Pattern Detection & Design Review

```
You are an Informatica IDMC design architect reviewing a mapping for best practices.

Audit this mapping design for issues, anti-patterns, and optimization opportunities.

Mapping Specification:
---
{mapping_spec}
---

Context:
- Load volume: {load_volume_rows} rows
- SLA: {sla_minutes} minutes
- Source system: {source_system}
- Target system: {target_system}

Review Criteria (prioritized):
1. CRITICAL: Hard-coded values, security risks, data loss
2. HIGH: Performance issues, missing error handling, SLA risk
3. MEDIUM: Design improvements, idiomatic patterns
4. LOW: Code style, documentation

Output format:
ISSUES FOUND:
- [Severity: CRITICAL/HIGH/MEDIUM/LOW]
  Description: [What is wrong]
  Impact: [Why it matters]
  Suggested Fix: [Code snippet or approach]

BEST PRACTICES:
- [Recommendation]

QUESTIONS FOR ENGINEER:
- [Clarification needed]

CONFIDENCE LEVEL: [0-100]
```

**Temperature:** 0.2  
**Max tokens:** 2048  
**File:** `migrator/accelerators/acc09_review.py`

---

### ACC-10: Job Dependency & Impact Analysis

```
You are an ETL architecture strategist. Analyze this job dependency graph and recommend a migration strategy.

Job Dependency Graph:
{job_dependency_graph}

Business Context:
- Load window: {load_window_start}:00 – {load_window_end}:00
- Affected reports: {affected_reports_count}
- SLA: {sla_minutes} minutes

Migration Constraints:
- Max parallel jobs: {max_parallel_jobs}
- Max wave size: {max_wave_size}
- Pilot target: {pilot_job_count} jobs

Questions:
1. What is the recommended migration wave order?
2. Which jobs should be migrated first to de-risk later waves?
3. What is the critical path? Will we meet SLA?
4. What rollback/runback strategy is needed?
5. Are there hidden dependencies not visible in the job graph?

Respond with:
- Recommended Wave Plan (Pilot: [jobs], Wave 1: [jobs], Wave 2: [jobs])
- Risk Assessment (critical path, SLA impact, failure scenarios)
- Rollback Strategy (parallel run, shadow traffic, switch plan)
- Hidden Dependencies (if any)
```

**Temperature:** 0.2  
**Max tokens:** 2048  
**File:** `migrator/accelerators/acc10_dependency.py`

---

## Appendix C: Acceptance Criteria per Accelerator

Use these checklists during QA review of each accelerator's output. An output is only approved for IDMC import when all applicable boxes are checked.

### ACC-02: BASIC Translator

**Functional:**
- [ ] Translated expression is syntactically valid Informatica (parseable)
- [ ] Business logic matches BASIC intent
- [ ] All input columns appear in output (no drops)
- [ ] Data type conversions are handled

**Quality:**
- [ ] Confidence score ≥ 80, OR `requires_human_review = true`
- [ ] All assumptions are explicitly listed
- [ ] Warnings are clear and actionable

**Performance:**
- [ ] API latency ≤ 10 seconds
- [ ] Cost ≤ $0.10 per call

**Compliance:**
- [ ] No sensitive data (passwords, keys) in output
- [ ] Output is idiomatic Informatica (not literal translation)

---

### ACC-08: C++ Operator Rewriter

**Functional:**
- [ ] Java code is syntactically valid and compilable (Java 11+)
- [ ] Input schema is fully honored (all parameters used)
- [ ] Output schema is fully produced (all columns generated)
- [ ] Edge cases (nulls, type coercion) are handled safely

**Security:**
- [ ] No hardcoded credentials in Java code
- [ ] File I/O and network calls are flagged if present
- [ ] All external dependencies are declared

**Quality:**
- [ ] Confidence score ≥ 85, OR explicit review flag
- [ ] Unsupported C++ features are clearly listed with workarounds

**Performance:**
- [ ] API latency ≤ 15 seconds
- [ ] Cost ≤ $0.15 per call

---

### ACC-09: Design Review

**Functional:**
- [ ] All issues found are legitimate (no false positives)
- [ ] Each issue has severity, description, impact, and fix
- [ ] No duplicate issues reported

**Actionability:**
- [ ] Every issue has a suggested fix
- [ ] Fix complexity is rated (TRIVIAL / SIMPLE / MEDIUM / COMPLEX)
- [ ] Fixes are implementable by a mid-level engineer

**Performance:**
- [ ] API latency ≤ 15 seconds
- [ ] Cost ≤ $0.20 per call

---

### ACC-10: Dependency Analysis

**Functional:**
- [ ] Wave plan respects all job dependencies (no forward dependencies violated)
- [ ] Critical path is calculated correctly
- [ ] Circular dependencies are detected and error raised
- [ ] Hidden dependencies are identified (if any)

**Actionability:**
- [ ] Wave plan is executable (engineer can follow it step by step)
- [ ] Rollback strategy has step-by-step instructions
- [ ] Go/No-Go criteria per wave are clear

**Performance:**
- [ ] API latency ≤ 20 seconds
- [ ] Cost ≤ $0.15 per call

---

## Appendix D: SDD Pre-Deployment Checklist

Use this before deploying the platform to a new client engagement.

### Pre-Deployment

**Infrastructure:**
- [ ] Anthropic API key created and secured in secrets manager (not in `config.yaml`)
- [ ] Model availability verified (`claude-sonnet-4-6`)
- [ ] Rate limiting policy confirmed (10 req/min, batch delays)
- [ ] Cost budget approved (expected: < $15 for 500-job estate)

**Testing:**
- [ ] All existing tests pass (`pytest tests/`)
- [ ] Sample DSX run completes without errors
- [ ] At least 5–10 representative jobs tested through AI accelerators
- [ ] Human review checklist templates distributed to review engineers

**Process:**
- [ ] Review SLAs documented (CRITICAL: 4h, HIGH: 24h, INFO: 48h)
- [ ] Escalation path defined (who approves CRITICAL issues)
- [ ] Rollback plan documented (how to revert a wave if IDMC import fails)

### Deployment Readiness Gates

- [ ] Phase 1 output validated against manual review (ACC-01 classification correct)
- [ ] Pilot wave (Wave 0) completed successfully and signed off
- [ ] Row counts post-migration match source ± 0.1%
- [ ] All CRITICAL issues from ACC-09 resolved before Wave 1

---

## Appendix E: Complete Workflow Example (500-Job Estate)

**Scenario:** Client has 500 DataStage jobs. 40 jobs have BASIC routines. 8 jobs have C++ custom operators.

| Week | Activity | Accelerators | Cost |
|---|---|---|---|
| **Week 1** | Run all rule-based accelerators. Extract DSX → classify all stages. Score all 500 jobs. Identify 40 BASIC + 8 C++ jobs. | ACC-01, 03, 04, 06, 07 | $0.00 |
| **Week 2** | Batch 40 BASIC jobs into 4 groups. Send each group to Claude. Assign review engineers. QA 24–48 hours. | ACC-02 | ~$0.08 |
| **Week 3** | Send 8 C++ operators to Claude. Engineers review and refine Java code. | ACC-08 | ~$0.48 |
| **Week 4** | Design review for 120 flagged jobs (30% of estate + all complex jobs). Engineers action recommendations. | ACC-09 | ~$1.20 |
| **Week 5** | Run dependency analysis once across full job graph. Generate wave plan. | ACC-10 | ~$0.07 |
| **Week 5+** | Execute Pilot (Wave 0): 20 highest-confidence jobs. Validate. Sign off. Proceed to Wave 1–N. | Human review | $0.00 |

**Totals:**
- AI cost: ~$1.83 for 500 jobs (**$0.004 per job**)
- Human review effort: ~60 hours (12h BASIC, 16h C++, 24h design, 8h dependency)
- Ready for pilot after Week 5

**This is the target benchmark for all future engagements.**

---

## Appendix F: Glossary

| Term | Meaning |
|---|---|
| DSX | DataStage Export XML — the file format produced by DataStage Designer when exporting jobs |
| IDMC | Informatica Intelligent Data Management Cloud |
| CDI | Cloud Data Integration — the ETL/mapping component of IDMC |
| Stage | A processing component in a DataStage parallel job (source, target, transformer, filter, etc.) |
| Sequence Job | DataStage's orchestration job type — defines execution order and conditional logic |
| Taskflow | IDMC's equivalent of a Sequence Job |
| BASIC | DataStage's built-in scripting language used inside Transformer stages for field expressions |
| Accelerator | A purpose-built script that automates one specific aspect of the migration |
| Wave | A batch of jobs migrated together in the same deployment window |
| Pilot (Wave 0) | The first small batch — used to validate the process before committing to full migration |
| Equivalency | How closely the IDMC equivalent matches the DataStage original: Direct (1:1), Partial (manual tuning needed), Manual (full rewrite) |
| ACC-XX | Accelerator code from the specification; each maps to one Python file in `accelerators/` |

---

*End of document.*
