# IBM DataStage → Informatica IDMC CDI
## Migration Matrix & Rule-Based Accelerator Reference

> **Classification:** SI Internal — ETL Migration Engineering  
> **Audience:** ETL Engineers, Solution Architects, QA  
> **Purpose:** Base migration mapping reference. Defines stage equivalencies, connection patterns, naming rules, BASIC function lookups, and the five rule-based accelerators (ACC-01, ACC-03, ACC-04, ACC-06, ACC-07).  
> **Extended by:** `ibm-infa-etl-migration-ai-spec.md` (AI-augmented accelerators ACC-02, ACC-05, ACC-08, ACC-09, ACC-10)  
> **Last Updated:** 2026-05-31

---

## Table of Contents

1. [Purpose & Scope](#1-purpose--scope)
2. [Migration Approach Overview](#2-migration-approach-overview)
3. [Stage-to-Transformation Mapping Matrix](#3-stage-to-transformation-mapping-matrix)
4. [Equivalency Classification Guide](#4-equivalency-classification-guide)
5. [Connection Migration Patterns](#5-connection-migration-patterns)
6. [Parameter Set Migration Patterns](#6-parameter-set-migration-patterns)
7. [Rule-Based Accelerators](#7-rule-based-accelerators)
   - [6.1 ACC-01, ACC-03, ACC-04, ACC-07](#61-acc-01-acc-03-acc-04-acc-07)
   - [6.2 ACC-06](#62-acc-06-job-complexity-scorer)
8. [BASIC Function Lookup Table](#8-basic-function-lookup-table)
9. [Naming Convention Rules](#9-naming-convention-rules)
10. [Migration Effort Estimation Guide](#10-migration-effort-estimation-guide)

---

## 1. Purpose & Scope

This document is the **base migration matrix** for IBM DataStage → Informatica IDMC CDI migrations. It covers:

- Every known DataStage stage type and its IDMC equivalent
- Connection and parameter migration patterns
- Naming convention transformation rules
- The five **rule-based accelerators** (no AI required) that automate the mechanical parts of migration

**What this document does NOT cover:** AI-augmented accelerators (BASIC translation, C++ rewriting, design review, dependency analysis). Those are defined in `ibm-infa-etl-migration-ai-spec.md`.

**How to use this document:**
1. Start with Section 3 — check every DataStage stage type in your estate against the mapping matrix.
2. Use Section 4 to understand what "Direct / Partial / Manual" means for your migration plan.
3. Run the accelerators in Section 7 to automate the mechanical work.
4. If your estate has BASIC routines, C++ operators, or complex Sequence Jobs, proceed to the AI spec.

---

## 2. Migration Approach Overview

### Rule-Based vs AI Decision

| Work Type | Approach | Accelerator | Cost |
|---|---|---|---|
| Stage type classification | Rule-Based | ACC-01 | $0 |
| Parameter set conversion | Rule-Based | ACC-03 | $0 |
| Connection migration | Rule-Based | ACC-04 | $0 |
| Naming convention application | Rule-Based | ACC-07 | $0 |
| Job complexity scoring | Rule-Based | ACC-06 | $0 |
| BASIC expression translation | Hybrid (Rule + AI) | ACC-02 | ~$0.002/call |
| Sequence Job → Taskflow | Hybrid (Rule + AI) | ACC-05 | ~$0.005/call |
| C++ operator rewriting | AI (Claude API) | ACC-08 | ~$0.04/call |
| Anti-pattern design review | AI (Claude API) | ACC-09 | ~$0.03/call |
| Dependency & impact analysis | AI (Claude API) | ACC-10 | ~$0.04/call |

**The 80/20 principle:** For a typical 500-job estate, 80% of jobs are handled entirely by rule-based accelerators at zero AI cost. Only the remaining 20% (complex BASIC logic, C++ operators, high-complexity jobs) require Claude API calls.

### Execution Order

```
Phase 1 (Rule-Based, run in parallel — no dependencies):
  ACC-01 → Stage classification CSV
  ACC-03 → Parameter JSON files
  ACC-04 → Connection JSON files
  ACC-06 → Complexity score JSON
  ACC-07 → Naming inventory CSV

Phase 2 (Hybrid/AI — depends on Phase 1 output):
  ACC-02, ACC-05, ACC-08, ACC-09

Phase 3 (AI — depends on Phase 1 + 2):
  ACC-10 → Migration wave plan
```

---

## 3. Stage-to-Transformation Mapping Matrix

This is the master lookup table used by ACC-01. Every DataStage stage type maps to an IDMC equivalent.

**Equivalency key:** Direct = 1:1 migration | Partial = needs manual config tuning | Manual = full rewrite required

### 3.1 Source / Target Connectors

| DataStage Stage Type | IDMC Equivalent | Equivalency | Action | Notes |
|---|---|---|---|---|
| Sequential File | Flat File Connector | Direct | Map | Format config carries over |
| Parallel Dataset | Flat File Connector | Direct | Map | Partition strategy may need review |
| DB2 Connector | DB2 Connector (IDMC) | Direct | Map | Driver version check required |
| Oracle Connector | Oracle Connector (IDMC) | Direct | Map | Wallet/TNS config may differ |
| ODBC Connector | ODBC Connector (IDMC) | Direct | Map | DSN config needed in IDMC agent |
| SQL Server Connector | SQL Server Connector (IDMC) | Direct | Map | Auth mode check (Windows vs SQL) |
| Teradata Connector | Teradata Connector (IDMC) | Direct | Map | FastExport/FastLoad mode review |
| Snowflake Connector | Snowflake Connector (IDMC) | Direct | Map | OAuth token vs key-pair auth |
| BigQuery Connector | Google BigQuery Connector (IDMC) | Direct | Map | Service account key required |
| Complex Flat File | Complex File Connector | Partial | Review | Record format parsing may need config |

### 3.2 Transformation Stages

| DataStage Stage Type | IDMC Equivalent | Equivalency | Action | Notes |
|---|---|---|---|---|
| Transformer | Expression Transformation | Direct | Map | BASIC expressions → see ACC-02 |
| Aggregator | Aggregator Transformation | Direct | Map | Group-by and aggregate functions map directly |
| Sort | Sorter Transformation | Direct | Map | Sort key order preserved |
| Join | Joiner Transformation | Direct | Map | Join type (inner/outer) preserved |
| Merge | Joiner Transformation | Partial | Review | Merge conditions may need manual config |
| Lookup | Lookup Transformation | Direct | Map | Cached vs uncached strategy to review |
| Filter | Filter Transformation | Direct | Map | Filter condition syntax translates directly |
| Funnel | Union Transformation | Direct | Map | Input ordering preserved |
| Copy | Router Transformation | Partial | Review | Multiple output routing logic needs verification |
| Remove Duplicates | Sorter (distinct) | Partial | Review | Enable "Distinct" on Sorter; sort key required |
| Modify | Expression Transformation | Direct | Map | Field rename / cast → Expression Transformation |
| Peek | Expression Transformation (debug) | Partial | Review | Debug-only; consider removing in IDMC |
| Sample | Filter Transformation | Partial | Review | Sampling logic must be re-expressed as filter |
| Surrogate Key | Sequence Generator | Direct | Map | Start value and increment preserved |
| Switch | Router Transformation | Direct | Map | Condition groups map to Router groups |
| Slowly Changing Dimension | SCD Transformation | Direct | Map | SCD Type 1/2/3 selection required |
| Change Capture | CDC Connector | Partial | Review | CDC mode (log-based vs trigger) may differ |
| Head | Filter Transformation | Partial | Review | Row-limit logic must be re-expressed |
| Tail | Filter Transformation | Partial | Review | Last-N-rows logic must be re-expressed |

### 3.3 Container / Reuse Stages

| DataStage Stage Type | IDMC Equivalent | Equivalency | Action | Notes |
|---|---|---|---|---|
| Shared Container | Mapplet | Direct | Map | Promote to reusable Mapplet in IDMC |
| Local Container | Reusable Transformation | Direct | Map | Inline reuse; can remain inline in IDMC |

### 3.4 XML Stages

| DataStage Stage Type | IDMC Equivalent | Equivalency | Action | Notes |
|---|---|---|---|---|
| XML Input | XML Parser Transformation | Partial | Review | XPath expressions need manual validation |
| XML Output | XML Generator Transformation | Partial | Review | Output namespace config may differ |

### 3.5 Custom / Advanced Stages

| DataStage Stage Type | IDMC Equivalent | Equivalency | Action | Notes |
|---|---|---|---|---|
| Custom Stage | Java Transformation | Manual | Rewrite | C++ source → Java rewrite via ACC-08 |

### 3.6 Sequence Job Activity Types (Taskflow)

| DataStage Activity Type | IDMC Taskflow Equivalent | Equivalency | Action |
|---|---|---|---|
| JobActivity | Mapping Task | Direct | Map |
| RoutineActivity | Command Task | Direct | Map |
| NotificationActivity | Notification Task | Direct | Map |
| ExecCommandActivity | Command Task | Direct | Map |
| TerminatorActivity | End Task | Direct | Map |

---

## 4. Equivalency Classification Guide

### Direct (Green — Migrate)

The DataStage stage has a 1:1 IDMC equivalent. ACC-01 generates the IDMC spec automatically. Engineer review is minimal — verify configuration properties carried over correctly.

**Expected effort:** 15–30 minutes per job containing only Direct stages.

### Partial (Yellow — Review)

The DataStage stage has an IDMC equivalent, but there is a meaningful difference in behavior, configuration, or capability that requires manual verification. The stage cannot be blindly migrated.

**Common partial cases:**
- `Copy` → `Router`: DataStage Copy fans out to multiple outputs unconditionally; IDMC Router uses conditional groups — engineer must define the routing condition.
- `Merge` → `Joiner`: DataStage Merge has specific sorted-input behavior; IDMC Joiner may need pre-sort configured.
- `Remove Duplicates` → `Sorter (distinct)`: Must enable distinct flag and specify correct sort key.
- `Change Capture` → `CDC Connector`: CDC mode (log-based vs trigger-based) is infrastructure-dependent.

**Expected effort:** 1–4 hours per job containing Partial stages, depending on complexity.

### Manual (Red — Rewrite)

No rule-based migration path exists. The DataStage stage requires a full functional rewrite in IDMC.

**Manual cases:**
- `Custom Stage` (C++ custom operators) → Java Transformation: Use ACC-08 (AI-assisted) for complex operators; manual rewrite for simple ones (<50 lines).

**Expected effort:** 1–5 days per custom operator, depending on algorithm complexity.

---

## 5. Connection Migration Patterns

Used by ACC-04. Every DataStage connection type maps to an IDMC connection object.

### Connection Type Mapping

| DataStage Connection Type | IDMC Connection Type | Auth Notes |
|---|---|---|
| OracleConnector | Oracle V2 | TNS name or host/port/SID; wallet optional |
| DB2Connector | IBM DB2 | JDBC URL; driver jar required on Secure Agent |
| SQLServerConnector | Microsoft SQL Server | Windows auth or SQL auth (use SQL auth for IDMC) |
| ODBCConnector | Generic ODBC | DSN must be configured on Secure Agent host |
| TeradataConnector | Teradata | Logon mechanism (TD2 or LDAP); FastLoad/FastExport requires additional config |
| SnowflakeConnector | Snowflake | Key-pair auth recommended over password for production |
| BigQueryConnector | Google BigQuery | Service account JSON key; dataset location must match |
| FlatFileConnector | Flat File | No credentials; path must be accessible from Secure Agent |

### Connection JSON Output Format (ACC-04)

ACC-04 produces one JSON file per connection, ready for IDMC REST API import:

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

Sensitive values are templated as `<<PARAM_NAME>>`. The engineer fills in actual values during IDMC import. This ensures no credentials are stored in the migration output artifacts.

### Connection Migration Checklist

For each migrated connection, verify:
- [ ] Connection type is available in the target IDMC org
- [ ] Secure Agent has required drivers/JARs installed
- [ ] Network connectivity from Secure Agent host to database host
- [ ] Credentials are injected via IDMC Parameter Manager (not hard-coded)
- [ ] Connection test passes in IDMC before running any mapping

---

## 6. Parameter Set Migration Patterns

Used by ACC-03. DataStage Parameter Sets map directly to IDMC Parameter Sets.

### Parameter Type Mapping

| DataStage Parameter Type | IDMC Parameter Type | Notes |
|---|---|---|
| String | String | Direct mapping |
| Integer | Integer | Direct mapping |
| Float | Decimal | Precision may differ; verify scale |
| Encrypted | Encrypted | Re-encrypt in IDMC; do not carry over DataStage-encrypted value |
| Pathname | String | Path separator may differ (Windows vs Linux Secure Agent) |
| List | String | Comma-separated string in IDMC |
| Date | String | IDMC uses string-typed parameters with date format convention |

### Parameter JSON Output Format (ACC-03)

```json
{
  "name": "PS_Database_Config",
  "parameters": [
    { "name": "DB_HOST",     "type": "String",    "default": "prod-db.internal", "encrypted": false },
    { "name": "DB_PORT",     "type": "String",    "default": "1521",             "encrypted": false },
    { "name": "DB_NAME",     "type": "String",    "default": "PROD",             "encrypted": false },
    { "name": "DB_USER",     "type": "String",    "default": "",                 "encrypted": false },
    { "name": "DB_PASSWORD", "type": "String",    "default": "",                 "encrypted": true  }
  ]
}
```

### Parameter Migration Rules

1. **Encrypted parameters**: Always set `encrypted: true` in IDMC. Never carry over the DataStage-encrypted value — it uses a different key. Re-enter the actual value in IDMC Parameter Manager.
2. **Pathname parameters**: If the Secure Agent runs on a different OS than the DataStage engine, verify path separators.
3. **Default values**: ACC-03 carries over defaults as-is. Review any defaults that contain environment-specific values (hostnames, paths).

---

## 7. Rule-Based Accelerators

### 6.1 ACC-01, ACC-03, ACC-04, ACC-07

#### ACC-01: Stage-to-Transformation Classifier

**Status:** Rule-Based (no AI)  
**File:** `migrator/accelerators/acc01_classifier.py`  
**Lookup table:** `migrator/data/stage_mapping.json`

**What it does:** Parses every job in the DSX export. For each stage, looks up the stage type in the mapping matrix (Section 3) and outputs a classification row.

**Output:** `output/acc01_classification.csv`

| Column | Description |
|---|---|
| `job_name` | DataStage job name |
| `stage_name` | Stage name within the job |
| `ds_type` | DataStage stage type |
| `idmc_equivalent` | IDMC equivalent from mapping table |
| `equivalency` | Direct / Partial / Manual |
| `action` | Map / Review / Rewrite |
| `has_basic_routines` | true if stage has BASIC expressions |
| `has_custom_operator` | true if stage is a Custom Stage |

**Also produces:** Per-job flags dict used by Phase 2 accelerators to route jobs to ACC-02 (BASIC) or ACC-08 (C++).

**Run:**
```bash
python -m migrator acc01 --dsx path/to/export.dsx
```

---

#### ACC-03: Parameter Set Migration Template

**Status:** Rule-Based (no AI)  
**File:** `migrator/accelerators/acc03_parameters.py`

**What it does:** Extracts all `<ParameterSet>` elements from the DSX export and converts them to IDMC-compatible JSON parameter files.

**Output:** One JSON file per parameter set in `output/acc03_parameters/`

**Key rule:** Encrypted parameters are flagged but never carry over the DataStage-encrypted value. The output JSON sets `encrypted: true` with an empty default — engineer must re-enter the value in IDMC.

---

#### ACC-04: Connection Migration Mapper

**Status:** Rule-Based (no AI)  
**File:** `migrator/accelerators/acc04_connections.py`

**What it does:** Extracts all `<Connection>` elements from the DSX export and converts them to IDMC REST API JSON payloads.

**Output:** One JSON file per connection in `output/acc04_connections/`

**Key rule:** All credential values are replaced with `<<PARAM_NAME>>` placeholders. No secrets travel in the output artifacts.

---

#### ACC-07: Naming Convention Transformer

**Status:** Rule-Based (no AI)  
**File:** `migrator/accelerators/acc07_naming.py`  
**Rules file:** `migrator/data/naming_rules.json`

**What it does:** Applies the naming convention rules (Section 9) to all job names, stage names, parameter names, and connection names. Produces an old → new name inventory.

**Output:** `output/acc07_naming/naming_inventory.csv`

| Column | Example |
|---|---|
| `object_type` | job |
| `original_name` | JOB_Load_Customer_STG |
| `new_name` | m_load_customer_stg |
| `changed` | true |
| `rule_applied` | remove_prefix:JOB_, add_prefix:m_, snake_case |

**Run:**
```bash
python -m migrator run --dsx path/to/export.dsx --output ./output/
```

---

### 6.2 ACC-06: Job Complexity Scorer

**Status:** Rule-Based (no AI). Claude review optional for jobs scoring ≥ 30.  
**File:** `migrator/accelerators/acc06_scorer.py`

**What it does:** Assigns a numeric complexity score to each job using a fixed formula. Score determines which jobs get routed to AI accelerators.

**Scoring Formula:**

```
Score = (stage_count × 1)
      + (custom_operator_count × 5)
      + (basic_routine_count × 3)
      + (is_sequence_job × 2)
```

**Thresholds:**

| Score Range | Classification | Action |
|---|---|---|
| 0 – 14 | LOW | Rule-based only; no AI needed |
| 15 – 29 | MEDIUM | Rule-based + human spot-check |
| 30 – 49 | HIGH | Route to ACC-09 design review |
| 50+ | VERY HIGH | Route to ACC-09; flag for senior architect review |

**requires_claude_review flag:** Set to `true` for any job scoring ≥ 30. This flag is consumed by ACC-09.

**Output:** `output/acc06_scoring/complexity_scores.json`

```json
[
  {
    "job_name": "Load_Customer_Fact",
    "stage_count": 12,
    "custom_operator_count": 1,
    "basic_routine_count": 4,
    "is_sequence_job": false,
    "score": 29,
    "classification": "MEDIUM",
    "requires_claude_review": false
  }
]
```

**Optional Claude enhancement:** For jobs scoring 30+, Claude can optionally review the DSX and flag hidden complexity not captured by the formula (e.g., undocumented downstream dependencies, implicit shared state). This is triggered manually and not part of the automated pipeline.

**Run:**
```bash
python -m migrator acc06 --dsx path/to/export.dsx
```

---

## 8. BASIC Function Lookup Table

Used by ACC-02 (hybrid BASIC translator). Before calling Claude, ACC-02 checks if the entire BASIC expression can be resolved using this table. If yes — no API call is made and confidence is 100%.

Format: `BASIC function name → Informatica expression template`. Arguments are positional: `{0}` = first argument, `{1}` = second, etc.

### String Functions

| BASIC Function | Informatica Expression | Notes |
|---|---|---|
| `Trim(x)` | `LTRIM(RTRIM({0}))` | Trims both leading and trailing spaces |
| `LTrim(x)` | `LTRIM({0})` | Leading spaces only |
| `RTrim(x)` | `RTRIM({0})` | Trailing spaces only |
| `Upcase(x)` | `UPPER({0})` | |
| `Upper(x)` | `UPPER({0})` | Alias for Upcase |
| `Downcase(x)` | `LOWER({0})` | |
| `Lower(x)` | `LOWER({0})` | Alias for Downcase |
| `Len(x)` | `LENGTH({0})` | |
| `Left(x, n)` | `SUBSTR({0}, 1, {1})` | |
| `Right(x, n)` | `SUBSTR({0}, LENGTH({0}) - {1} + 1, {1})` | |
| `Mid(x, start, len)` | `SUBSTR({0}, {1}, {2})` | |
| `Change(x, old, new)` | `REPLACESTR(0, {0}, {1}, {2})` | Replace all occurrences |
| `Index(x, substr)` | `INSTR({0}, {1})` | Returns 0 if not found (IDMC) vs 0 in BASIC |
| `Concat(x, y)` | `CONCAT({0}, {1})` | |
| `Space(n)` | `RPAD('', {0})` | Generate n spaces |
| `Pad(x, n, char)` | `RPAD({0}, {1}, {2})` | Right-pad |

### NULL Handling Functions

| BASIC Function | Informatica Expression | Notes |
|---|---|---|
| `IsNull(x)` | `ISNULL({0})` | Returns boolean |
| `IsNotNull(x)` | `NOT ISNULL({0})` | |
| `NullToZero(x)` | `IIF(ISNULL({0}), 0, {0})` | Safe numeric default |
| `NullToValue(x, val)` | `IIF(ISNULL({0}), {1}, {0})` | Safe generic default |

### Type Conversion Functions

| BASIC Function | Informatica Expression | Notes |
|---|---|---|
| `Str(x)` | `TO_CHAR({0})` | Numeric → string |
| `Num(x)` | `TO_INTEGER({0})` | String → integer |
| `Float(x)` | `TO_FLOAT({0})` | String → float |
| `Decimal(x)` | `TO_DECIMAL({0})` | String → decimal |
| `Date(x, fmt)` | `TO_DATE({0}, {1})` | String → date; format must be Informatica-compatible |
| `DateToChar(x, fmt)` | `TO_CHAR({0}, {1})` | Date → string |

### Date Functions

| BASIC Function | Informatica Expression | Notes |
|---|---|---|
| `DateDiff(end, start, unit)` | `DATEDIFF({2}, {1}, {0})` | **Argument order is reversed in IDMC** |
| `DateAdd(date, n, unit)` | `ADD_TO_DATE({0}, {2}, {1})` | |
| `Today()` | `SYSDATE` | No arguments in IDMC |
| `SystemDate()` | `SYSDATE` | Alias for Today() |

### Math Functions

| BASIC Function | Informatica Expression | Notes |
|---|---|---|
| `Abs(x)` | `ABS({0})` | |
| `Mod(x, y)` | `MOD({0}, {1})` | |
| `Round(x, n)` | `ROUND({0}, {1})` | |
| `Sqrt(x)` | `SQRT({0})` | |

### Important Notes on the Lookup Table

1. **DateDiff argument order:** DataStage `DateDiff(End_Date, Start_Date, 'D')` becomes IDMC `DATEDIFF('DD', Start_Date, End_Date)`. The end/start order is swapped. ACC-02 handles this automatically.
2. **Index vs INSTR:** DataStage `Index` returns 0 if not found. IDMC `INSTR` also returns 0. Behavior matches.
3. **Functions NOT in lookup table:** Any BASIC function not listed here falls through to the Claude API path in ACC-02. Common examples: `CalcHash`, `Apply_Discount`, `FormatPhone`, business-specific custom routines.

---

## 9. Naming Convention Rules

Used by ACC-07. Rules are defined in `migrator/data/naming_rules.json`.

### Prefix Rules

| Object Type | Remove Prefixes | Add Prefix | Example (Before → After) |
|---|---|---|---|
| Jobs (Parallel) | `JOB_`, `DS_`, `STG_` | `m_` | `JOB_Load_Customer` → `m_Load_Customer` |
| Sequence Jobs / Workflows | `SEQ_`, `JOB_SEQ_` | `wf_` | `SEQ_Nightly_Load` → `wf_Nightly_Load` |
| Routines / Expressions | `RT_`, `ROUTINE_` | `exp_` | `RT_CalcDiscount` → `exp_CalcDiscount` |
| Parameter Sets | `PS_`, `PSET_` | `pm_` | `PS_DB_Config` → `pm_DB_Config` |
| Connections | `CONN_`, `CON_` | `conn_` | `CONN_Oracle_Prod` → `conn_Oracle_Prod` |

### Case Convention

All IDMC object names use **snake_case**:
- Spaces → `_`
- Hyphens → `_`
- Dots → `_`

### Layer Keyword Mapping

DataStage often uses layer keywords in job names that should be normalised to standard IDMC layer abbreviations:

| DataStage Keyword | IDMC Standard |
|---|---|
| `STG`, `STAGE`, `STAGING` | `stg` |
| `ODS` | `ods` |
| `DW`, `DWH` | `dw` |
| `MART` | `mart` |
| `RPT`, `REPORT` | `rpt` |

**Example:** `JOB_STAGING_Customer_Load` → `m_stg_Customer_Load`

### Override Policy

If a client has their own IDMC naming standard that differs from the above, update `migrator/data/naming_rules.json` before running ACC-07. The rules file is the single source of truth — do not hard-code naming rules in the accelerator code.

---

## 10. Migration Effort Estimation Guide

Use this table to estimate migration effort for a given estate before beginning work.

### Per-Job Effort by Equivalency Mix

| Job Profile | Typical Stage Mix | Estimated Effort |
|---|---|---|
| Simple flat-file job | All Direct stages, no BASIC | 2–4 hours |
| Standard DB job | All Direct stages, simple BASIC expressions | 4–8 hours |
| Complex transformation job | Mix of Direct + Partial, multiple BASIC | 1–2 days |
| Job with custom operator | Contains Custom Stage (C++) | 3–5 days |
| Sequence Job (simple) | Linear chain, no conditional logic | 2–4 hours |
| Sequence Job (complex) | Multi-branch, conditional, parallel paths | 1–2 days |

### Estate-Level Estimation Formula

```
Total effort (days) =
    (Direct-only jobs × 0.5 day)
  + (Partial-stage jobs × 1.5 days)
  + (BASIC-routine jobs × 1 day)
  + (Custom operator jobs × 4 days)
  + (Sequence jobs × 0.5–2 days)
  + AI review overhead (40–60 hours for 500-job estate)
```

### Complexity Score → Effort Mapping

| ACC-06 Score | Classification | Effort Estimate |
|---|---|---|
| 0 – 14 | LOW | 2–4 hours |
| 15 – 29 | MEDIUM | 4–8 hours |
| 30 – 49 | HIGH | 1–2 days |
| 50+ | VERY HIGH | 3–5 days |

### Typical 500-Job Estate Breakdown

Based on real-world DataStage estates:

| Category | % of Jobs | Count | Total Effort |
|---|---|---|---|
| Simple (Direct only, no BASIC) | 40% | 200 | 100 days |
| Standard (Direct + simple BASIC) | 30% | 150 | 150 days |
| Complex (Partial stages + BASIC) | 20% | 100 | 150 days |
| Custom Operator (C++) | 2% | 10 | 40 days |
| Sequence Jobs | 8% | 40 | 40 days |
| **Total** | 100% | **500** | **~480 days (~24 FTE-months)** |

> **With automation (all 10 accelerators):** Estimated effort reduction of 60–70%, bringing total to approximately **150–190 person-days** for a 500-job estate.

---

## Appendix: Connection Migration Quick Reference

| If DataStage uses... | IDMC needs... | Pre-requisite |
|---|---|---|
| Oracle TNS names | Oracle V2 Connector + host/port/SID | Secure Agent must reach DB host |
| DB2 JDBC | IBM DB2 Connector + JDBC URL | DB2 JDBC driver jar on Secure Agent |
| Teradata FastExport | Teradata Connector | Teradata JDBC + TPT utilities |
| Snowflake OAuth | Snowflake Connector | OAuth app registered in Snowflake account |
| BigQuery service account | BigQuery Connector | Service account JSON key with BigQuery Data Editor role |
| ODBC DSN | Generic ODBC Connector | DSN configured on Secure Agent OS |

---

*This document covers the rule-based foundation of the migration. For AI-augmented accelerators (BASIC translation, C++ rewriting, design review, dependency analysis), see `ibm-infa-etl-migration-ai-spec.md`.*
