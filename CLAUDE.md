# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Purpose

This is a Python toolkit that automates migration of ETL jobs from **IBM DataStage** to **Informatica IDMC CDI**. It uses a hybrid strategy: deterministic rule-based scripts for mechanical translations, and Claude API calls for tasks requiring semantic understanding (BASIC code translation, C++ rewriting, design review, dependency analysis).

The full specification is at: `~/ibm-infa-etl-migration-ai-spec.md`

---

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run all rule-based accelerators against a DSX export
python -m migrator run --dsx path/to/export.dsx --output ./output/

# Run a single accelerator
python -m migrator acc01 --dsx path/to/export.dsx
python -m migrator acc02 --job-id JOB_001 --basic-code "Trim(Upcase(Name))"
python -m migrator acc10 --project-id PROJ_001

# Run tests
pytest tests/

# Run tests for a single accelerator
pytest tests/test_acc01.py
pytest tests/test_acc02_ai.py -v

# Lint
ruff check .
```

---

## Architecture

### Directory Structure

```
ds_to_iformatica/
├── migrator/
│   ├── __init__.py
│   ├── __main__.py          # CLI entrypoint (argparse)
│   ├── core/
│   │   ├── claude_client.py # Shared Anthropic API wrapper (rate limiting, cost tracking, retries)
│   │   ├── validator.py     # Input/output schema validation (pre-call and post-call)
│   │   ├── dsx_parser.py    # Parse DataStage DSX XML exports
│   │   └── models.py        # Pydantic models for all input/output schemas
│   ├── accelerators/
│   │   ├── acc01_classifier.py   # Stage-to-Transformation Classifier (rule-based)
│   │   ├── acc02_basic.py        # BASIC → Informatica Expression Translator (hybrid)
│   │   ├── acc03_parameters.py   # Parameter Set Migration (rule-based)
│   │   ├── acc04_connections.py  # Connection Migration Mapper (rule-based)
│   │   ├── acc05_taskflow.py     # Sequence Job → Taskflow Optimizer (hybrid)
│   │   ├── acc06_scorer.py       # Job Complexity Scorer (rule-based + optional Claude)
│   │   ├── acc07_naming.py       # Naming Convention Transformer (rule-based)
│   │   ├── acc08_cpp.py          # C++ Operator → Java Rewriter (Claude API)
│   │   ├── acc09_review.py       # Anti-Pattern Detection & Design Review (Claude API)
│   │   └── acc10_dependency.py   # Job Dependency & Impact Analysis (Claude API)
│   └── data/
│       ├── stage_mapping.json    # DataStage stage type → IDMC equivalent lookup table
│       ├── basic_functions.json  # BASIC function → Informatica function lookup table
│       └── naming_rules.json     # Naming convention transformation rules
├── tests/
│   ├── fixtures/                 # Sample DSX files, BASIC snippets, C++ operators
│   └── test_acc*.py              # One test file per accelerator
├── output/                       # Default output directory (gitignored)
├── config.yaml                   # Model name, rate limits, cost thresholds, review SLAs
└── requirements.txt
```

### Key Design Decisions

**Hybrid routing (ACC-02, ACC-05, ACC-06):** Rule-based lookup table runs first. Claude API is called only when the lookup table has no match OR the input is multi-line / complex logic. This is enforced in each accelerator's `translate()` method.

**Claude client (`core/claude_client.py`):** All Claude API calls go through this single wrapper. It handles:
- Rate limiting (10 req/min, configurable)
- Per-call cost tracking against circuit breaker thresholds (per-accelerator max in `config.yaml`)
- Exponential backoff on 429/504 (max 3 retries)
- Temperature per accelerator (0.0 for code translation, 0.2 for design/analysis)

**Validation (`core/validator.py`):** Every accelerator calls `validate_input()` before and `validate_output()` after the Claude call. These enforce the schemas in spec Section 7.1 and the constraint tables in Section 7.6. Violations raise typed exceptions (`InputValidationError`, `OutputValidationError`, `CostThresholdError`).

**Execution phases (as defined in spec Section 7.5):**
- Phase 1 (ACC-01, 03, 04, 06, 07): Run in parallel; no dependencies
- Phase 2 (ACC-02, 05, 08, 09): Depend on ACC-01 classification output
- Phase 3 (ACC-10): Depends on full Phase 1 + Phase 2 outputs
- Phase 4: Human review loop (wave-by-wave deployment)

**Output format:** Every accelerator writes JSON to `./output/<acc_id>/<job_id>.json` matching the output schemas in spec Section 7.1. The `requires_human_review` flag gates auto-deployment.

### Claude API Configuration (config.yaml)

```yaml
model: claude-sonnet-4-6          # Update from spec's claude-3-5-sonnet-20241022
temperature:
  code_translation: 0.0           # ACC-02, ACC-08
  design_analysis: 0.2            # ACC-09, ACC-10
max_tokens:
  basic_translation: 1024
  cpp_rewriting: 2048
  design_review: 2048
  dependency_analysis: 2048
rate_limit:
  requests_per_minute: 10
  batch_delay_seconds: 60
cost_circuit_breaker:             # Per-call thresholds from spec Section 7.6
  acc02: 0.10
  acc08: 0.15
  acc09: 0.20
  acc10: 0.15
confidence_threshold: 80          # Below this → requires_human_review = true
```

### Lookup Tables (`data/`)

`basic_functions.json` maps common DataStage BASIC functions to Informatica equivalents (e.g., `Trim` → `LTRIM(RTRIM(...))`, `Upcase` → `UPPER(...)`, `IsNull` → `ISNULL(...)`). ACC-02 consults this before calling Claude. If the entire expression resolves via lookup, no API call is made.

`stage_mapping.json` maps every known DataStage stage type to its IDMC equivalent and equivalency level (Direct/Partial/Manual). Used by ACC-01.

### Error Handling

All accelerators return structured error responses (never raise unhandled exceptions to the caller). The error contract matches the global error table in spec Section 7.4: HTTP-style codes (400, 402, 429, 503, 504) with typed `error` fields and `retry_after_seconds` where applicable.
