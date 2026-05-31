# IBM DataStage → Informatica IDMC CDI
## AI-Augmented Migration Specification
### Hybrid Rule-Based + Claude API Strategy

---

> **Classification:** SI Internal — AI-Assisted Migration Engineering  
> **Audience:** Solution Architects, Senior ETL Engineers, Automation Developers  
> **Purpose:** Integration strategy for Claude API in ETL migration automation. Defines where AI adds value and where rule-based automation is sufficient.  
> **Last Updated:** 2026-05-26

---

## Executive Summary

This specification extends the base migration matrix (./ibm-infa-etl-migration-matix.md) with strategic Claude API integration. **AI is used only where rule-based automation cannot reliably produce 100% correct output.** Remaining accelerators continue using rule-based approaches (Python scripts, lookup tables, templates).

**Decision Framework:**
- ✅ **Rule-Based (100% deterministic)**: Stage classification, connection mapping, parameter migration, naming conventions
- 🤖 **Claude API (semantic/creative)**: BASIC code translation, custom operator rewriting, design optimization, anti-pattern detection, impact analysis

---

## Table of Contents

1. [AI Integration Strategy](#1-ai-integration-strategy)
2. [Accelerators: Rule-Based (Keep As-Is)](#2-accelerators-rule-based-keep-as-is)
3. [Accelerators: Claude API Required](#3-accelerators-claude-api-required)
4. [Claude API Usage Patterns](#4-claude-api-usage-patterns)
5. [Implementation Guide](#5-implementation-guide)
6. [Cost & Performance Considerations](#6-cost--performance-considerations)
7. [Formal Specification Driven Development](#7-formal-specification-driven-development)
   - 7.1 [Interface Specifications](#71-interface-specifications)
   - 7.2 [Test Case Matrices](#72-test-case-matrices)
   - 7.3 [Acceptance Criteria](#73-acceptance-criteria)
   - 7.4 [Error Handling Specifications](#74-error-handling-specifications)
   - 7.5 [Dependency Graph](#75-dependency-graph)
   - 7.6 [Validation Rules & Constraints](#76-validation-rules--constraints)

---

## 1. AI Integration Strategy

### 1.1 Decision Matrix: When to Use Claude API vs Rules

| Challenge | Rule-Based | Claude API | Hybrid | Rationale |
|---|---|---|---|---|
| **Stage Type Classification** | ✅ | ❌ | - | Deterministic mapping; no ambiguity |
| **Connection String Migration** | ✅ | ❌ | - | Schema/format is fixed; rules suffice |
| **Parameter Set Conversion** | ✅ | ❌ | - | Structure is deterministic |
| **Naming Convention Application** | ✅ | ❌ | - | Template-based transformation |
| **BASIC Function Translation** | 🔶 | ✅ | 🤖 | Common functions = rules; complex logic = Claude |
| **Custom C++ Operator Rewrite** | ❌ | ✅ | 🤖 | Requires semantic understanding; no rule-based equivalent |
| **Sequence Job → Taskflow** | ✅ | 🔶 | 🤖 | Basic translation = rules; optimization = Claude |
| **Complex Expression Translation** | 🔶 | ✅ | 🤖 | Multi-line BASIC logic needs context; Claude understands intent |
| **Anti-Pattern Detection** | 🔶 | ✅ | 🤖 | Hard-coded rules miss subtle issues; Claude identifies patterns |
| **Design Review & Optimization** | ❌ | ✅ | - | Requires human-level reasoning about ETL patterns |
| **Job Dependency Impact Analysis** | 🔶 | ✅ | 🤖 | Graph analysis = rules; business impact = Claude |
| **Complexity Scoring** | ✅ | ❌ | - | Formula-based; objective metrics |

**Legend:**
- ✅ = Use rule-based (100% reliable)
- ❌ = Rule-based insufficient; use Claude API
- 🔶 = Hybrid approach (rules for simple cases, Claude for complex)
- 🤖 = Claude primary with optional human review

---

## 2. Accelerators: Rule-Based (Keep As-Is)

These accelerators continue using the original rule-based approach from the base specification. No changes required.

### ACC-01: Stage-to-Transformation Classifier
**Status:** ✅ Keep Rule-Based  
**Reason:** Deterministic mapping; every DataStage stage type has a fixed IDMC equivalent.  
**Tool:** Python script parsing DSX XML → classification CSV with equivalency matrix.  
**Output:** CSV with columns: Stage Name | DS Type | IDMC Equivalent | Equivalency | Action

---

### ACC-03: Parameter Set Migration Template
**Status:** ✅ Keep Rule-Based  
**Reason:** Structure is fixed; parameter names, types, and encryption flags map deterministically.  
**Tool:** Python script → JSON parameter file generation via IDMC REST API.  
**Output:** IDMC-compatible parameter files ready for import.

---

### ACC-04: Connection Migration Mapper
**Status:** ✅ Keep Rule-Based  
**Reason:** Connection properties are schema-based; translation is deterministic.  
**Tool:** Python script → IDMC REST API JSON payloads.  
**Output:** Batch-imported connections with host, port, credentials templates.

---

### ACC-07: Naming Convention Transformer
**Status:** ✅ Keep Rule-Based  
**Reason:** Pattern-based string replacement; conventions are fixed templates.  
**Tool:** Excel + Python macro applying find-replace rules.  
**Output:** Old-name → new-name inventory mapping.

---

### ACC-06: Job Complexity Scorer (Hybrid, Mostly Rule-Based)
**Status:** 🔶 Hybrid (Keep Rules; Claude Optional Enhancement)  
**Base:** Python script with fixed scoring weights (1 point per stage, 5 per custom operator, etc.).  
**Enhancement:** Claude can optionally review scored results and flag jobs with hidden complexity not captured by the formula (e.g., "This looks like a data lineage job with undocumented downstream dependencies").  
**When to Use Claude:** After rule-based score is generated, for jobs scoring 30+; Claude reviews DSX to identify hidden risks.

---

## 3. Accelerators: Claude API Required

These accelerators have ambiguity or domain-specific logic that rules cannot handle reliably. Claude API is essential.

---

### ACC-02-AI: BASIC Routine to Expression Translator (AI-Augmented)

**Purpose:** Convert DataStage BASIC code to Informatica expressions. Uses rules for common functions; Claude API for complex logic.

**Approach:**

1. **Rules-Based Phase** (Python script):
   - Parse BASIC expression
   - Match against lookup table of common functions (Trim, Upcase, Len, Left, Right, etc.)
   - Output simple translations directly

2. **Claude API Phase** (for unmatched or complex expressions):
   - If lookup table match found → use rule translation
   - If no match OR multi-line logic → send to Claude API

**Claude API Prompt Template:**

```
You are an ETL migration specialist. Convert this DataStage BASIC expression to Informatica CDI expression language.

BASIC Code:
[PASTE CODE HERE]

Requirements:
- Preserve business logic exactly
- Use Informatica functions: UPPER(), LOWER(), LENGTH(), SUBSTR(), IIF(), INSTR(), TO_DATE(), DATEDIFF(), etc.
- Return ONLY the translated expression (no explanations)
- Flag any assumptions made (e.g., "assumes Load_Date is in YYYY-MM-DD format")

Example BASIC: Trim(Upcase(Customer_Name))
Example IDMC Output: UPPER(LTRIM(RTRIM(Customer_Name)))
```

**Decision Logic:**

```python
# Pseudocode
basic_expression = extract_from_stage()

if is_simple_function(basic_expression):
    # Trim, Upcase, Len, etc.
    return lookup_table_translate(basic_expression)
else:
    # Complex multi-line logic or unsupported function
    claude_response = call_claude_api(basic_expression, prompt_template)
    return {
        'translated': claude_response.translation,
        'requires_review': True,
        'assumptions': claude_response.assumptions
    }
```

**When Rule-Based is Sufficient:**
- Single-function expressions: `Trim(x)`, `Upcase(x)`, `IsNull(x)`
- Simple nested: `Trim(Upcase(Customer_Name))`
- Date conversions in standard formats

**When Claude API is Required:**
- Multi-line BASIC blocks with conditional logic
- Business-specific functions or algorithmic routines
- Unclear intent or undocumented logic
- Expressions involving record-level context

**Example Workflow:**

Input BASIC:
```basic
-- Check if customer is premium; if so, apply discount
If Credit_Limit > 50000 Then
    Apply_Discount(Base_Price, 0.15)
Else If Credit_Limit > 10000 Then
    Apply_Discount(Base_Price, 0.05)
Else
    Base_Price
End If
```

Rule-Based Lookup: No match (custom function `Apply_Discount`)

Claude API Response:
```
// Assuming Apply_Discount multiplies price by (1 - discount_rate)
IIF(Credit_Limit > 50000, Base_Price * 0.85, 
    IIF(Credit_Limit > 10000, Base_Price * 0.95, Base_Price))

// Assumptions:
// 1. Apply_Discount(price, discount_rate) = price * (1 - discount_rate)
// 2. Credit_Limit is numeric
// 3. Base_Price is numeric
```

**Human Review Loop:**
- Claude flags assumptions
- Engineer verifies assumptions against DataStage job documentation
- Engineer confirms or corrects Claude output before deployment

---

### ACC-05-AI: Sequence Job → Taskflow with Logic Optimization

**Purpose:** Convert DataStage Sequence Jobs to IDMC Taskflows. Rule-based handles structure; Claude optimizes logic flow.

**Approach:**

1. **Rules-Based Phase** (Python script):
   - Parse Sequence Job DSX
   - Map Job Activity → Mapping Task
   - Map Routine Activity → Command Task
   - Map Notification Activity → Notification Task
   - Generate basic Taskflow structure

2. **Claude API Phase** (optional optimization):
   - Identify sequential bottlenecks (could run in parallel)
   - Flag missing error handling or retry logic
   - Suggest conditional branching improvements

**Claude API Prompt Template:**

```
You are an ETL orchestration specialist. Review this Taskflow execution plan and suggest optimizations.

Current Taskflow (sequential):
1. Load_Staging_Tables (20 min)
2. Transform_Core_Layer (45 min)
3. Load_Fact_Tables (30 min)
4. Load_Dimension_Tables (15 min)

Constraints:
- Load_Dimension_Tables requires Transform_Core_Layer to complete
- Load_Fact_Tables requires both Transform_Core_Layer AND Load_Dimension_Tables
- All can tolerate 5-min delays

Questions:
1. Which tasks can run in parallel?
2. What is the critical path?
3. Are there missing error recovery steps?
4. Should we add a checkpoint after Transform_Core_Layer?

Respond in structured format: Optimized Order, Parallelism, Error Handling Gaps.
```

**When Rule-Based is Sufficient:**
- Sequential job with no parallelization opportunity
- Simple on-success/on-fail chains
- No explicit dependencies beyond task order

**When Claude API is Required:**
- Complex multi-branch logic
- Implicit dependencies (not obvious from task names)
- Performance optimization advice
- Error handling strategy recommendations

---

### ACC-08-AI: Custom C++ Operator Code Rewriter

**Purpose:** Translate C++ custom operators to Java Transformation code for IDMC.

**Status:** ⚠️ **High Effort; Claude API Recommended**

**Approach:**

1. **Rules-Based Phase** (C++ source code extraction):
   - Extract custom operator source from DataStage repository
   - Identify input/output interfaces
   - Extract business logic

2. **Claude API Phase** (semantic code translation):
   - Provide C++ code + functional specification to Claude
   - Claude understands intent and produces Java equivalent
   - Engineer reviews and validates output

**Claude API Prompt Template:**

```
You are an expert in C++ and Java ETL transformations. Convert this C++ DataStage custom operator to Java for Informatica CDI.

C++ Code:
[PASTE CODE HERE]

Input Schema: [column names and types]
Output Schema: [column names and types]

Requirements:
1. Preserve all business logic exactly
2. Return valid Java code that can run in Informatica Expression / Java Transformation
3. Handle null values safely
4. Include comments explaining any assumptions
5. Flag any external library dependencies that may not be available in IDMC runtime

Assumptions to clarify:
- Are there any file I/O operations? (IDMC may not support them)
- Are there network calls? (Security implications in cloud)
- Are there database operations? (Should use IDMC connectors instead)
```

**When NOT to Use Claude:**
- Operator is simple (< 50 lines); engineer rewrites manually
- Operator depends on DataStage-specific APIs that don't exist in Java
- Operator performs system-level operations (e.g., file permissions)

**When Claude API is Essential:**
- Algorithm is complex (100+ lines)
- Business logic is undocumented
- Multiple input validation branches

---

### ACC-09-AI: Anti-Pattern Detection & Design Review

**Purpose:** Scan generated IDMC design specs and flag anti-patterns, gaps, and design smells.

**Approach:**

1. **Rules-Based Phase** (static checks):
   - Hard-coded table names (should be parameters)
   - Missing error handling
   - Unmatched field counts in joins
   - Undefined parameters

2. **Claude API Phase** (semantic pattern recognition):
   - Identify subtle design issues
   - Suggest idiomatic IDMC patterns
   - Flag potential performance problems
   - Recommend alternative approaches

**Claude API Prompt Template:**

```
You are an Informatica IDMC design reviewer. Audit this mapping design for anti-patterns and improvements.

Mapping Spec:
[PASTE MAPPING YAML/JSON HERE]

Review Checklist:
1. Are there any hard-coded values that should be parameters?
2. Is error handling complete (nulls, type mismatches, missing rows)?
3. Are there performance opportunities (pushdown, caching, partitioning)?
4. Are there data quality issues (duplicates, unexpected nulls)?
5. Is this mapping idiomatic or does it fight IDMC design conventions?
6. Are there undocumented assumptions about input data?

Respond with:
- **Issues Found** (critical/warning/info severity)
- **Suggested Fixes** (code snippet if applicable)
- **Best Practice Notes** (how IDMC recommends approaching this pattern)
```

**When to Trigger Claude Review:**
- Any generated mapping flagged as "Complex" (score 36+)
- Any mapping with Custom Operator equivalents
- Any mapping with multiple BASIC translations (high assumption risk)
- Any mapping involving slowly-changing dimensions or advanced patterns

---

### ACC-10-AI: Job Dependency & Impact Analysis

**Purpose:** Analyze DataStage job dependency graph and assess migration impact.

**Approach:**

1. **Rules-Based Phase** (graph extraction):
   - Build job → job dependency graph from Sequence Jobs
   - Extract parameter dependencies
   - Build file/dataset lineage

2. **Claude API Phase** (impact reasoning):
   - Suggest migration wave sequencing
   - Identify hidden risks (circular dependencies, implicit coupling)
   - Recommend rollback/rollforward strategy
   - Flag jobs affecting critical business processes

**Claude API Prompt Template:**

```
You are an ETL architecture strategist. Analyze this job dependency graph and recommend a migration strategy.

Job Dependency Graph:
[PASTE DEPENDENCY LIST HERE]
E.g., Load_Cust_Staging → Transform_Cust → Load_Cust_Mart → Reporting_Jobs

Current Metrics:
- Total jobs: [N]
- Critical path length: [complexity]
- Circular dependencies: [Y/N]
- Jobs with custom operators: [N]
- Jobs with BASIC routines: [N]

Business Context:
- [E.g., "Nightly load window: 10pm-6am EST"]
- [E.g., "Customer Mart feeds 50+ reports; any failure blocks morning reporting"]
- [E.g., "Load_Staging has SLA: <30min execution time"]

Questions:
1. What is the recommended migration wave order? (Pilot → Wave 1 → Wave 2)
2. Which jobs should be migrated first to de-risk later waves?
3. What is the critical path in IDMC? (Will we meet SLA?)
4. What runback/rollback strategy is needed?
5. Are there hidden dependencies not visible in the job graph?

Respond with:
- **Recommended Wave Plan** (Pilot: [jobs], Wave 1: [jobs], Wave 2: [jobs])
- **Risk Assessment** (critical path, SLA impact, failure scenarios)
- **Rollback Strategy** (parallel run, shadow traffic, switch plan)
```

**When to Use Claude API:**
- >30 jobs in the estate
- Complex dependency chains (Sequence → Sequence → Sequence)
- Business-critical jobs with tight SLAs
- Migration wave planning (deciding Go/No-Go)

---

## 4. Claude API Usage Patterns

### 4.1 API Integration Architecture

```
┌─────────────────────────────────────────────────────────────┐
│              Migration Automation Framework                   │
│                                                               │
│  ┌──────────────┐      ┌──────────────┐      ┌───────────┐  │
│  │   DSX Export │      │ Rule-Based   │      │ Claude    │  │
│  │  (DataStage) │ ───→ │ Accelerators │ ───→ │ API Calls │  │
│  │              │      │ (Python)     │      │ (optional)│  │
│  └──────────────┘      └──────────────┘      └───────────┘  │
│                               │                     │         │
│                               ├─→ ACC-01 (Stage Classification) ✅
│                               ├─→ ACC-03 (Parameters)          ✅
│                               ├─→ ACC-04 (Connections)         ✅
│                               ├─→ ACC-07 (Naming)              ✅
│                               └─→ ACC-06 (Scoring)             ✅
│                                     │
│                                     └─→ [Claude Review Optional]
│                                           (Pattern flagging)
│
│  ┌──────────────┐      ┌──────────────┐      ┌───────────┐
│  │ DSX Export   │ ───→ │ Rule-Based   │ ───→ │ Claude    │
│  │ + Routines   │      │ Initial Draft│      │ Enhancement
│  └──────────────┘      └──────────────┘      └───────────┘
│                               │                     │
│                               ├─→ ACC-02 (BASIC translation)  🔶
│                               ├─→ ACC-05 (Taskflow logic)     🔶
│                               ├─→ ACC-08 (C++ rewriting)      🤖
│                               ├─→ ACC-09 (Anti-pattern detect) 🤖
│                               └─→ ACC-10 (Dependency analysis) 🤖
│
│  ┌─────────────────────┐
│  │ IDMC Import Ready   │
│  │ (with review marks) │
│  └─────────────────────┘
```

### 4.2 Claude API Cost Estimation

**Pricing Model (Anthropic Claude 3.5 Sonnet as of May 2026):**
- Input: $3 per million tokens
- Output: $15 per million tokens

**Per-Job Cost Examples:**

| Accelerator | Input Size | Output Size | Calls per Job | Cost/Job |
|---|---|---|---|---|
| **ACC-02 (BASIC translation)** | 500 tokens (routine code) | 300 tokens | 1 | $0.02 |
| **ACC-08 (C++ operator)** | 3000 tokens (code + docs) | 2000 tokens | 1 | $0.06 |
| **ACC-09 (Design review)** | 2000 tokens (spec) | 1500 tokens | 1 | $0.05 |
| **ACC-10 (Dependency analysis)** | 1500 tokens (graph) | 2000 tokens | 1 | $0.07 |

**Estate-Level Cost (500 jobs):**
- Basic migration (ACC-02, 50% of jobs have BASIC): 250 × $0.02 = **$5.00**
- Complex operators (ACC-08, 10% of jobs): 50 × $0.06 = **$3.00**
- Design reviews (ACC-09, 30% of jobs): 150 × $0.05 = **$7.50**
- Impact analysis (ACC-10, once per project): **$0.07**
- **Total: ~$15.57 for 500-job estate**

---

### 4.3 Rate Limiting & Batch Processing

**Recommended Approach:**

```python
# Pseudocode: Batch Claude API calls to stay within rate limits

from anthropic import Anthropic

client = Anthropic()
batch_size = 10  # Process 10 jobs per batch
jobs_to_process = get_jobs_flagged_for_ai()

for i in range(0, len(jobs_to_process), batch_size):
    batch = jobs_to_process[i:i + batch_size]
    
    for job in batch:
        if job.has_basic_routines:
            response = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1024,
                messages=[
                    {
                        "role": "user",
                        "content": build_basic_translation_prompt(job)
                    }
                ]
            )
            save_claude_response(job.id, response)
        
        if job.has_custom_operators:
            response = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=2048,
                messages=[
                    {
                        "role": "user",
                        "content": build_cpp_translation_prompt(job)
                    }
                ]
            )
            save_claude_response(job.id, response)
    
    # Rate limiting: wait 60 seconds between batches
    time.sleep(60)
```

---

## 5. Implementation Guide

### 5.1 Phased Rollout Strategy

**Phase 1: Foundation (Weeks 1–2)**
- Deploy all rule-based accelerators (ACC-01, 03, 04, 07, 06)
- Run DSX analysis to generate baseline metrics
- Output: Job inventory, complexity scores, naming audit

**Phase 2: Simple AI Integration (Weeks 3–4)**
- Deploy ACC-02-AI (BASIC translation with Claude)
- Limit to jobs with <100 lines of BASIC code (safest bets)
- Output: Translated expressions ready for QA

**Phase 3: Complex AI Integration (Weeks 5–7)**
- Deploy ACC-08-AI (C++ operator rewriting)
- Deploy ACC-09-AI (design review)
- Establish human review SLA: 24 hours per Claude recommendation

**Phase 4: Strategic Analysis (Weeks 8+)**
- Deploy ACC-10-AI (dependency analysis)
- Generate migration wave plan
- Execute pilot wave with highest-confidence jobs

### 5.2 Human Review Process

**For Every Claude API Output:**

| Severity | Review SLA | Approver | Action |
|---|---|---|---|
| **Critical** | 4 hours | Senior Architect | Auto-block until approved |
| **Warning** | 24 hours | Mid-level Engineer | Flagged for review |
| **Info** | 48 hours | Any engineer | FYI; proceed if confident |

**Review Checklist Template:**

```
Claude Output Review Checklist

Job: [Job Name]
Accelerator: [ACC-XX]
Claude Response: [snippet]

[ ] Logic is correct (matches DataStage intent)
[ ] Syntax is valid (runs in IDMC)
[ ] No assumptions conflict with data context
[ ] Performance impact is acceptable
[ ] Error handling is complete
[ ] Output matches input schema

Comments:
[...]

Approved by: [Name] | Date: [YYYY-MM-DD]
```

### 5.3 Claude API Configuration

**Recommended Settings:**

```python
# Pseudo-code: Client configuration

claude_config = {
    "model": "claude-3-5-sonnet-20241022",  # Latest, best price/performance
    "max_tokens": {
        "basic_translation": 1024,
        "cpp_rewriting": 2048,
        "design_review": 2048,
        "dependency_analysis": 2048
    },
    "temperature": 0.2,  # Lower = more deterministic; higher = more creative
    "rate_limit": {
        "requests_per_minute": 10,
        "batch_delay_seconds": 60
    },
    "retries": 3,
    "timeout_seconds": 60
}
```

**Temperature Tuning:**
- **0.0 (Deterministic)**: Code translation, syntax-heavy tasks → Use for ACC-02, ACC-08
- **0.2 (Low Creativity)**: Design review, best-practice suggestions → Use for ACC-09, ACC-10
- **Do NOT use > 0.5**: Translation tasks need consistency; creativity introduces risk

---

## 6. Cost & Performance Considerations

### 6.1 Cost Optimization

**Strategy 1: Hybrid Approach**
- Use rules-based for 80% of jobs (lowest cost)
- Use Claude only for flagged complex cases (20%)
- Expected savings: 75% reduction in AI API calls vs. full-AI approach

**Strategy 2: Batch Processing**
- Group similar jobs (same stage count, same routine patterns)
- Use single Claude call to translate all similar routines
- Cost: Fixed overhead per batch, not per job

**Example:**
```
5 jobs with same "Trim + Upcase" routine
Instead of: 5 × $0.02 = $0.10
Use batch: 1 × $0.05 = $0.05 (translate once, apply 5 times)
```

### 6.2 Performance Trade-Offs

| Factor | Rule-Based | Claude API | Hybrid |
|---|---|---|---|
| **Speed** | <1s per job | 5–10s per job | Fast for simple, slower for complex |
| **Accuracy** | 95% (simple patterns) | 88% (requires review) | 98% (rules + Claude) |
| **Cost** | $0.00 | $0.06/job (avg) | $0.01/job (80/20 split) |
| **Human Review** | Minimal | High | Medium |

**Recommendation:** Start with hybrid (80/20) for 500-job estate:
- 400 jobs via rules-based: 0 cost, minimal review
- 100 complex jobs via Claude: ~$15 cost, focused review effort
- Total cost: **~$15 + 40 hours review effort**

---

## 7. Implementation Checklist

### Pre-Deployment

- [ ] Anthropic account created; API key secured in secrets manager
- [ ] Claude model availability verified (claude-3-5-sonnet-20241022)
- [ ] Rate limiting policy defined (10 req/min, batch delays)
- [ ] Human review SLAs documented
- [ ] Review checklist template created
- [ ] Sample prompts tested with 5–10 representative jobs

### Deployment

- [ ] Deploy all rule-based accelerators first (ACC-01, 03, 04, 06, 07)
- [ ] Run initial DSX analysis; generate job inventory
- [ ] Deploy Claude-integrated accelerators incrementally (ACC-02 → ACC-08 → ACC-09 → ACC-10)
- [ ] Run pilot with 20 jobs (mix of simple and complex)
- [ ] Collect metrics: translation accuracy, review time, cost

### Post-Deployment

- [ ] Monitor Claude API costs (bill should be <$50/month for typical 500-job estate)
- [ ] Track human review time (target: <1 hour per complex job)
- [ ] Gather feedback on Claude output quality
- [ ] Iterate on prompt templates based on review results
- [ ] Document lessons learned for future engagements

---

## 8. Prompt Templates Reference

### Template: BASIC Routine Translation

```
You are an ETL migration specialist fluent in DataStage BASIC and Informatica expression languages.

Convert this DataStage BASIC Transformer expression to Informatica CDI expression language.

BASIC Expression:
---
[PASTE CODE HERE]
---

Column Context:
- Input columns: [list]
- Output columns: [list]
- Known formats: [e.g., dates as 'YYYY-MM-DD']

Translation Rules:
1. Use Informatica built-in functions only (no custom Java unless necessary)
2. Handle NULLs safely (use IIF + ISNULL)
3. Preserve exact business logic
4. Provide assumptions if you make any

Output format:
TRANSLATED EXPRESSION:
[SINGLE LINE OR MULTI-LINE IF NEEDED]

ASSUMPTIONS:
[List any assumptions about data types, formats, or business logic]

REVIEW NOTES:
[Flaganything that may differ from original behavior or that an engineer should double-check]
```

### Template: C++ Operator Rewriting

```
You are a bilingual Java/C++ developer specializing in data transformation algorithms.

Convert this C++ DataStage custom operator to Java for Informatica CDI Java Transformation.

C++ Operator Source:
---
[PASTE CODE HERE]
---

Functional Specification:
- Purpose: [brief description]
- Input schema: [columns, types]
- Output schema: [columns, types]
- Known edge cases: [nulls, negative numbers, very large values]

Constraints:
1. Target: Java 11+
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

### Template: Design Review & Anti-Pattern Detection

```
You are an Informatica IDMC design architect reviewing a mapping for best practices.

Audit this mapping design for issues, anti-patterns, and optimization opportunities.

Mapping Specification (YAML/JSON):
---
[PASTE SPEC HERE]
---

Context:
- Load volume: [N rows]
- SLA: [e.g., "<5 minutes"]
- Source system: [e.g., "Oracle, 200 cols"]
- Target system: [e.g., "Snowflake"]

Review Criteria (prioritized):
1. **Critical**: Hard-coded values, security risks, data loss
2. **High**: Performance issues, missing error handling, SLA risk
3. **Medium**: Design improvements, idiomatic patterns
4. **Low**: Code style, documentation

Output format:
ISSUES FOUND:
- [Severity: CRITICAL/HIGH/MEDIUM/LOW]
  Description: [What is wrong]
  Impact: [Why it matters]
  Suggested Fix: [Code snippet or approach]

BEST PRACTICES:
- [Recommendation 1: How IDMC recommends this pattern]
- [Recommendation 2: Performance optimization opportunity]

QUESTIONS FOR ENGINEER:
- [Clarification needed on business logic or assumptions]

CONFIDENCE LEVEL: [80–100%]
```

---

## 9. Success Metrics

Track these KPIs to measure AI integration effectiveness:

| Metric | Target | Notes |
|---|---|---|
| **Rule-Based Coverage** | 80%+ jobs | Lower=more manual work |
| **Claude Translation Accuracy** | 85%+ pass QA first-try | Acceptable: may need minor tweaks |
| **Cost per Job** | <$0.05 | Hybrid approach should stay under $25 total for 500-job estate |
| **Human Review Time** | <2 hours per 10 complex jobs | Reasonable review burden |
| **Migration Wave Execution Time** | <20% longer than DataStage | IDMC should not be significantly slower |
| **Production SLA Met** | 100% | Zero unplanned failures due to migration |

---

## Appendix A: Rules-Based Accelerators Reference

See ./ibm-infa-etl-migration-matix.md sections:
- 6.1 → ACC-01, ACC-03, ACC-04, ACC-07 (unchanged)
- 6.2 → ACC-06 (unchanged; Claude review optional)

---

## Appendix B: Example: Complete Workflow

**Scenario:** Migrate a 500-job DataStage estate with 40 jobs containing BASIC routines, 8 jobs with C++ operators.

**Execution:**

1. **Week 1**: Deploy rule-based (ACC-01, 03, 04, 06, 07)
   - Extract DSX → classify all stages
   - Score all jobs for complexity
   - Identify 40 BASIC jobs + 8 C++ jobs
   - Cost: $0

2. **Week 2**: Deploy ACC-02-AI (BASIC translation)
   - Batch 40 BASIC jobs into 4 groups
   - Send each group to Claude (4 API calls × $0.02 = $0.08)
   - Assign review engineers; QA 24–48 hours
   - Cost: $0.08

3. **Week 3**: Deploy ACC-08-AI (C++ rewriting)
   - Send 8 C++ operators to Claude (8 API calls × $0.06 = $0.48)
   - Engineers review/refine Java code
   - Cost: $0.48

4. **Week 4**: Deploy ACC-09-AI (design review)
   - Review 120 jobs flagged for review (30% of 400 simple + all 20 complex)
   - Send in batches of 5 (24 batches × $0.05 = $1.20)
   - Engineers act on recommendations
   - Cost: $1.20

5. **Week 5**: Deploy ACC-10-AI (dependency analysis)
   - One call for full dependency graph ($0.07)
   - Recommend wave sequencing
   - Cost: $0.07

**Total AI Cost: $1.83**  
**Total Review Effort: ~60 hours** (12 hours BASIC, 16 hours C++, 24 hours design, 8 hours dependency)  
**Cost per Job: $0.004**  
**Status:** Ready for pilot wave migration

---

---

## 7. Formal Specification Driven Development

This section formalizes all accelerators with executable specifications, test cases, and acceptance criteria for strict SDD compliance.

---

### 7.1 Interface Specifications

#### ACC-02-AI: BASIC Routine to Expression Translator

**Interface ID:** ACC-02-AI-INTERFACE-001

**Input Schema:**

```json
{
  "accelerator_id": "ACC-02-AI",
  "job_id": "string (required, unique identifier)",
  "basic_code": "string (required, 1–1000 chars, valid DataStage BASIC)",
  "column_context": {
    "input_columns": [
      {
        "name": "string (required, column name)",
        "type": "string (DECIMAL, VARCHAR, DATE, TIMESTAMP)",
        "length": "integer (optional, for VARCHAR)",
        "precision": "integer (optional, for DECIMAL)",
        "format": "string (optional, e.g., 'YYYY-MM-DD' for dates)"
      }
    ],
    "output_columns": [
      {"name": "string", "type": "string"}
    ]
  },
  "complexity_level": "string (SIMPLE | MEDIUM | COMPLEX)",
  "assumptions": ["string array (optional, business logic notes)"],
  "timestamp": "ISO8601 (when request created)"
}
```

**Output Schema:**

```json
{
  "accelerator_id": "ACC-02-AI",
  "job_id": "string",
  "request_id": "UUID (for tracking)",
  "translated_expression": "string (valid Informatica expression syntax)",
  "complexity_classification": "string (SIMPLE | MEDIUM | COMPLEX)",
  "confidence_level": "integer (0–100, Claude self-assessment)",
  "requires_human_review": "boolean (true if confidence < 80 OR assumptions detected)",
  "assumptions_detected": ["string array (assumptions Claude made)"],
  "function_mappings": [
    {
      "basic_function": "string",
      "idmc_equivalent": "string",
      "confidence": "integer (0–100)"
    }
  ],
  "warnings": ["string array (potential issues)"],
  "estimated_review_time_minutes": "integer",
  "api_call_metadata": {
    "model": "string (e.g., 'claude-3-5-sonnet-20241022')",
    "tokens_input": "integer",
    "tokens_output": "integer",
    "cost_usd": "float",
    "latency_seconds": "float"
  },
  "timestamp": "ISO8601"
}
```

**Validation Rules (Pre-Call):**
- `basic_code` must be non-empty and ≤1000 chars
- `column_context` must include at least 1 input column
- `complexity_level` must be one of: SIMPLE | MEDIUM | COMPLEX
- `job_id` must be unique per request (no duplicates in batch)

**Validation Rules (Post-Call):**
- `translated_expression` must be syntactically valid Informatica (parseable)
- `confidence_level` must be 0–100
- `requires_human_review` must be TRUE if confidence < 80
- `api_call_metadata.cost_usd` must be ≤ $0.10 (circuit breaker if exceeded)

---

#### ACC-08-AI: Custom C++ Operator Code Rewriter

**Interface ID:** ACC-08-AI-INTERFACE-001

**Input Schema:**

```json
{
  "accelerator_id": "ACC-08-AI",
  "job_id": "string (required)",
  "operator_name": "string (required, C++ class name)",
  "cpp_source_code": "string (required, 50–5000 lines, valid C++)",
  "input_schema": [
    {
      "column_name": "string",
      "cpp_type": "string (int, double, char*, string, etc.)"
    }
  ],
  "output_schema": [
    {
      "column_name": "string",
      "cpp_type": "string"
    }
  ],
  "functional_specification": "string (what this operator does)",
  "edge_cases": ["string array (nulls, negative numbers, etc.)"],
  "external_dependencies": ["string array (libraries, system calls)"],
  "constraints": {
    "may_use_file_io": "boolean (default: false)",
    "may_use_network": "boolean (default: false)",
    "target_java_version": "string (default: '11')"
  },
  "timestamp": "ISO8601"
}
```

**Output Schema:**

```json
{
  "accelerator_id": "ACC-08-AI",
  "job_id": "string",
  "request_id": "UUID",
  "java_source_code": "string (complete, runnable Java class)",
  "confidence_level": "integer (0–100)",
  "requires_human_review": "boolean (true if confidence < 85 OR unsupported features)",
  "unsupported_cpp_features": [
    {
      "feature": "string (e.g., 'file I/O')",
      "reason": "string (why it cannot be directly translated)",
      "workaround": "string (suggested IDMC alternative)"
    }
  ],
  "external_java_dependencies": [
    {
      "library": "string",
      "version": "string",
      "required": "boolean (true if must have)"
    }
  ],
  "test_cases_suggested": [
    {
      "test_name": "string",
      "input": "object",
      "expected_output": "object",
      "notes": "string"
    }
  ],
  "warnings": ["string array"],
  "review_checklist": [
    {
      "item": "string",
      "status": "string (REQUIRED | RECOMMENDED | OPTIONAL)"
    }
  ],
  "api_call_metadata": {
    "model": "string",
    "tokens_input": "integer",
    "tokens_output": "integer",
    "cost_usd": "float",
    "latency_seconds": "float"
  },
  "timestamp": "ISO8601"
}
```

**Validation Rules (Pre-Call):**
- `cpp_source_code` must be 50–5000 lines, valid C++ syntax (basic check)
- `input_schema` and `output_schema` must each have ≥1 column
- `target_java_version` must be '8', '11', '17', or '21'

**Validation Rules (Post-Call):**
- `java_source_code` must contain a valid Java class definition
- `confidence_level` must be 0–100
- If `may_use_file_io=false` and C++ code has fopen/fread, flag in `unsupported_cpp_features`
- `api_call_metadata.cost_usd` must be ≤ $0.15

---

#### ACC-09-AI: Anti-Pattern Detection & Design Review

**Interface ID:** ACC-09-AI-INTERFACE-001

**Input Schema:**

```json
{
  "accelerator_id": "ACC-09-AI",
  "job_id": "string (required)",
  "mapping_spec": "object (YAML/JSON representation of IDMC mapping)",
  "load_volume_rows": "integer (estimated rows per run)",
  "sla_minutes": "integer (required execution time SLA)",
  "source_system": {
    "name": "string",
    "type": "string (RDBMS | FLAT_FILE | CLOUD_API)",
    "column_count": "integer"
  },
  "target_system": {
    "name": "string",
    "type": "string (RDBMS | FLAT_FILE | CLOUD_API)",
    "column_count": "integer"
  },
  "review_focus": ["string array (CRITICAL | PERFORMANCE | DESIGN | SECURITY)"],
  "timestamp": "ISO8601"
}
```

**Output Schema:**

```json
{
  "accelerator_id": "ACC-09-AI",
  "job_id": "string",
  "request_id": "UUID",
  "issues_found": [
    {
      "issue_id": "string (e.g., 'CRIT-001')",
      "severity": "string (CRITICAL | HIGH | MEDIUM | LOW)",
      "category": "string (HARD_CODED_VALUE | MISSING_ERROR_HANDLING | PERFORMANCE | SECURITY)",
      "description": "string (what is wrong)",
      "impact": "string (why it matters)",
      "affected_component": "string (mapping name, transformation name)",
      "suggested_fix": "string (code snippet or approach)",
      "fix_complexity": "string (TRIVIAL | SIMPLE | MEDIUM | COMPLEX)"
    }
  ],
  "best_practices_found": [
    {
      "category": "string (PERFORMANCE | DESIGN | MAINTAINABILITY)",
      "recommendation": "string (what IDMC recommends)",
      "current_approach": "string (what the mapping does now)",
      "suggested_approach": "string (idiomatic IDMC way)"
    }
  ],
  "critical_questions": [
    {
      "question": "string (clarification needed)",
      "context": "string (why we're asking)"
    }
  ],
  "summary": {
    "total_issues": "integer",
    "critical_count": "integer",
    "high_count": "integer",
    "estimated_sla_impact": "string (e.g., '+10% latency if issues unaddressed')",
    "confidence_level": "integer (0–100)"
  },
  "api_call_metadata": {
    "model": "string",
    "tokens_input": "integer",
    "tokens_output": "integer",
    "cost_usd": "float",
    "latency_seconds": "float"
  },
  "timestamp": "ISO8601"
}
```

**Validation Rules (Pre-Call):**
- `mapping_spec` must be non-empty and valid JSON/YAML
- `load_volume_rows` must be positive integer
- `sla_minutes` must be positive integer
- `review_focus` must contain only valid categories

**Validation Rules (Post-Call):**
- Total `issues_found` count must match `summary.critical_count + high_count + medium_count + low_count`
- All issue severities must be one of: CRITICAL | HIGH | MEDIUM | LOW
- If `confidence_level < 75`, flag for additional manual review
- `api_call_metadata.cost_usd` must be ≤ $0.20

---

#### ACC-10-AI: Job Dependency & Impact Analysis

**Interface ID:** ACC-10-AI-INTERFACE-001

**Input Schema:**

```json
{
  "accelerator_id": "ACC-10-AI",
  "project_id": "string (required, unique project identifier)",
  "job_dependency_graph": [
    {
      "job_id": "string",
      "job_name": "string",
      "downstream_jobs": ["string array of job_ids"],
      "upstream_jobs": ["string array of job_ids"],
      "execution_time_minutes": "integer (estimated)",
      "job_type": "string (PARALLEL_JOB | SEQUENCE_JOB | SERVER_JOB)",
      "has_custom_operators": "boolean",
      "has_basic_routines": "boolean",
      "business_criticality": "string (CRITICAL | HIGH | MEDIUM | LOW)"
    }
  ],
  "business_context": {
    "load_window_start_hour": "integer (0–23)",
    "load_window_end_hour": "integer (0–23)",
    "affected_reports_count": "integer",
    "sla_minutes": "integer"
  },
  "migration_constraints": {
    "max_parallel_jobs": "integer",
    "max_wave_size": "integer",
    "pilot_job_count": "integer (target for wave 0)"
  },
  "timestamp": "ISO8601"
}
```

**Output Schema:**

```json
{
  "accelerator_id": "ACC-10-AI",
  "project_id": "string",
  "request_id": "UUID",
  "migration_wave_plan": [
    {
      "wave_id": "integer (0 = pilot, 1+ = production waves)",
      "wave_name": "string (e.g., 'Pilot: High Confidence Jobs')",
      "jobs": ["string array of job_ids"],
      "total_jobs": "integer",
      "estimated_execution_time_minutes": "integer",
      "critical_path_minutes": "integer",
      "sla_achievable": "boolean (true if within business window)",
      "risk_level": "string (LOW | MEDIUM | HIGH)",
      "rollback_trigger": "string (what condition causes rollback)"
    }
  ],
  "critical_path_analysis": {
    "critical_path_jobs": ["string array of job_ids"],
    "total_critical_path_minutes": "integer",
    "optimization_opportunities": [
      {
        "opportunity": "string (can jobs X and Y run in parallel?)",
        "time_saving_minutes": "integer"
      }
    ]
  },
  "hidden_dependencies": [
    {
      "job_a": "string",
      "job_b": "string",
      "dependency_type": "string (PARAMETER | FILE | DATABASE_ROW_LEVEL)",
      "severity": "string (CRITICAL | HIGH | MEDIUM)",
      "notes": "string (why this matters)"
    }
  ],
  "rollback_strategy": {
    "parallel_run_recommended": "boolean",
    "shadow_traffic_recommended": "boolean",
    "switch_back_sla_minutes": "integer (time needed to rollback)",
    "data_reconciliation_required": "boolean",
    "detailed_steps": ["string array"]
  },
  "risk_assessment": {
    "total_risk_score": "integer (0–100)",
    "single_points_of_failure": ["string array of job_ids"],
    "mitigation_strategies": ["string array"]
  },
  "api_call_metadata": {
    "model": "string",
    "tokens_input": "integer",
    "tokens_output": "integer",
    "cost_usd": "float",
    "latency_seconds": "float"
  },
  "timestamp": "ISO8601"
}
```

**Validation Rules (Pre-Call):**
- `job_dependency_graph` must have ≥5 jobs (meaningful analysis)
- Each job must have unique `job_id`
- Cyclic dependencies must be detected and reported (error condition)
- All referenced job_ids in `downstream_jobs` / `upstream_jobs` must exist in graph

**Validation Rules (Post-Call):**
- Wave 0 (pilot) must have ≤ `migration_constraints.pilot_job_count` jobs
- Total jobs across all waves must equal input job count
- `critical_path_minutes` must be ≤ `business_context.sla_minutes` if `sla_achievable=true`
- All `rollback_strategy.detailed_steps` must be non-empty strings
- `api_call_metadata.cost_usd` must be ≤ $0.15

---

### 7.2 Test Case Matrices

#### ACC-02-AI: BASIC Routine Translator — Test Cases

| Test ID | Input | Expected Output | Pass Criteria | Notes |
|---|---|---|---|---|
| **T-02-001** | `Trim(Customer_Name)` | `LTRIM(RTRIM(Customer_Name))` | Output syntax valid; logic equivalent | SIMPLE case; function in lookup table |
| **T-02-002** | `Trim(Upcase(Status_Code))` | `UPPER(LTRIM(RTRIM(Status_Code)))` | Nested functions; order preserved | Validates function chaining |
| **T-02-003** | `IsNull(Middle_Name)` | `ISNULL(Middle_Name)` | Direct mapping | NULL handling |
| **T-02-004** | `If IsNull(x) Then 'N/A' Else x` | `IIF(ISNULL(x), 'N/A', x)` | Conditional logic translated | IIF pattern |
| **T-02-005** | `DateDiff(End_Date, Start_Date, 'D')` | `DATEDIFF('DD', Start_Date, End_Date)` | Parameter order adjusted | Date functions; param order change |
| **T-02-006** | 5-line BASIC algorithm with business logic | Valid expression OR "Review required" flag | Confidence < 80 OR assumptions listed | COMPLEX case; human review expected |
| **T-02-007** | BASIC code with undocumented function `CalcHash(x, seed)` | Claude suggests `HASHFUNCTION(x, seed)` OR flags "unsupported" | Requires review; not in lookup | MEDIUM case; workaround expected |
| **T-02-008** | Empty string | Error: "basic_code must be non-empty" | Validation error on input | Edge case: invalid input |
| **T-02-009** | Code >1000 chars | Error: "basic_code exceeds max length (1000)" | Validation error | Constraint check |
| **T-02-010** | BASIC with `Change(Description, 'old', 'new')` | `REPLACESTR(0, Description, 'old', 'new')` | Correct function mapping | Validates comprehensive lookup table |

**Acceptance Criteria (All Tests):**
- ✅ Output is syntactically valid Informatica expression
- ✅ Business logic is preserved (within Claude assessment)
- ✅ Confidence score is provided and reasonable
- ✅ If confidence < 80, `requires_human_review = true`
- ✅ API cost ≤ $0.10 per call
- ✅ Latency < 10 seconds

---

#### ACC-08-AI: C++ Operator Rewriter — Test Cases

| Test ID | Input | Expected Output | Pass Criteria | Notes |
|---|---|---|---|---|
| **T-08-001** | Simple C++ class: add 10 to input integer | Valid Java class with same logic | Syntax valid; logic equivalent | SIMPLE operator |
| **T-08-002** | C++ class: string concatenation + length check | Java equivalent using String/StringBuilder | Thread-safe; no side effects | STRING manipulation |
| **T-08-003** | C++ class: hash function (MD5) | Java equivalent using `MessageDigest` | Security implications noted; review flag | MEDIUM complexity; external dependency |
| **T-08-004** | C++ code with file I/O (`fopen`, `fread`) | Java code with flag: "File I/O unsupported in IDMC cloud" | Unsupported feature listed; workaround suggested | FILE_IO constraint |
| **T-08-005** | C++ code with network call (`curl_easy_perform`) | Java code with flag: "Network calls limited in cloud environment" | Security/network flags; review required | NETWORK constraint |
| **T-08-006** | Complex C++ algorithm (500 lines) | Complete Java rewrite | Confidence ≥85 or flagged for review | HIGH effort rewrite |
| **T-08-007** | C++ code with undefined external symbol | Claude identifies missing symbol; suggests Java library | Workaround listed; requires engineer decision | DEPENDENCY resolution |
| **T-08-008** | Malformed C++ (syntax errors) | Error: "Input C++ code is not syntactically valid" | Validation error; human review required | EDGE case: bad input |
| **T-08-009** | C++ with DataStage-specific API calls | Claude identifies and flags non-portable code | Unsupported features listed; manual rewrite noted | DATASTAGE-specific features |
| **T-08-010** | C++ operator with proper input/output schemas | Java code that matches input/output schema exactly | Schema fidelity verified | SCHEMA matching |

**Acceptance Criteria (All Tests):**
- ✅ Output is syntactically valid Java (Java 11+)
- ✅ All input parameters are preserved as output
- ✅ All output columns are produced correctly
- ✅ Edge cases (nulls, type mismatches) are handled
- ✅ Unsupported features are clearly flagged
- ✅ Confidence ≥85 or explicit review required flag
- ✅ API cost ≤ $0.15 per call
- ✅ Latency < 15 seconds

---

#### ACC-09-AI: Design Review — Test Cases

| Test ID | Scenario | Expected Issues Found | Pass Criteria | Notes |
|---|---|---|---|---|
| **T-09-001** | Mapping with 3 hard-coded table names (no parameters) | 3 × "Hard-coded value should be parameter" (MEDIUM severity) | All 3 flagged correctly | Parametrization opportunity |
| **T-09-002** | Mapping with no error handling for NULL inputs | "Missing NULL handling" (HIGH severity) | Flagged; suggested fix provided | Data quality |
| **T-09-003** | Join on 100K rows without pre-sort on 50K master | "Unsorted input to Joiner; performance risk" (MEDIUM severity) | Flagged with optimization suggestion | PERFORMANCE issue |
| **T-09-004** | Mapping with 20 transformations, complex logic chain | Design review completes; ≥3 improvement suggestions | Output is comprehensive; suggestions are actionable | COMPLEX mapping |
| **T-09-005** | Mapping with plaintext password in parameter default | "Security issue: password in plaintext" (CRITICAL severity) | Flagged; remediation step provided | SECURITY issue |
| **T-09-006** | Simple 3-stage mapping (Source → Filter → Target) | 0–1 issues (good design) | Minimal issues; validation of baseline | SIMPLE, good design |
| **T-09-007** | Mapping with unknown transformation type in spec | Claude flags as "Cannot classify; review manually required" | Graceful degradation | EDGE case: unknown input |
| **T-09-008** | Mapping specified for 5-minute SLA with 10 joins | "SLA risk: 10 joins may not complete in 5 min; consider pushdown or parallelism" | Risk flagged with mitigation | SLA concern |
| **T-09-009** | Empty mapping spec | Error: "mapping_spec must be non-empty JSON/YAML" | Validation error | INVALID input |
| **T-09-010** | Mapping with all Informatica best practices applied | 0 critical issues, 0–2 low-level suggestions | Validation of well-designed mapping | POSITIVE baseline |

**Acceptance Criteria (All Tests):**
- ✅ All issues have severity level (CRITICAL/HIGH/MEDIUM/LOW)
- ✅ All issues have suggested fix
- ✅ If confidence < 75, additional manual review flagged
- ✅ Estimated SLA impact calculated (if applicable)
- ✅ No false positives (every flagged issue is real)
- ✅ API cost ≤ $0.20 per call
- ✅ Latency < 15 seconds

---

#### ACC-10-AI: Dependency Analysis — Test Cases

| Test ID | Job Graph | Expected Output | Pass Criteria | Notes |
|---|---|---|---|---|
| **T-10-001** | Linear chain: Job A → B → C | Wave 0: [A], Wave 1: [B, C] or Wave 1: [B], Wave 2: [C] | Logical wave sequencing; critical path identified | Simple chain |
| **T-10-002** | Diamond: A → B,C → D | Wave 0: [A], Wave 1: [B, C], Wave 2: [D] | Parallelization opportunity identified | Parallel execution |
| **T-10-003** | Circular dependency: A → B → C → A | Error: "Circular dependency detected; cannot migrate" | Validation failure; requires manual intervention | CRITICAL error |
| **T-10-004** | Complex graph (50+ jobs, multiple branches) | 3–5 waves; critical path ≤ SLA | Wave plan is executable; SLA achievable | Complex DAG |
| **T-10-005** | Job with implicit parameter dependency (not in graph) | Claude flags: "Hidden dependency on job X (via parameter)" | Additional dependencies identified | HIDDEN dependency |
| **T-10-006** | All jobs independent (no dependencies) | Wave 0: [all jobs] | All can run in parallel; single wave | Parallelizable estate |
| **T-10-007** | Job A is "CRITICAL" tier; 20 jobs depend on it | Pilot wave includes A; subsequent waves clearly marked "dependent on Pilot success" | Criticality affects wave sequencing | Risk mitigation |
| **T-10-008** | Empty job graph | Error: "Job graph must contain ≥5 jobs for meaningful analysis" | Validation failure; insufficient data | EDGE case: too small |
| **T-10-009** | SLA 30 min; critical path is 120 min | `sla_achievable = false`; "Cannot meet SLA; 4× parallelism required or reduce scope" | SLA conflict identified; mitigation suggested | SLA constraint |
| **T-10-010** | 500 jobs with complex interdependencies | Wave plan with 6–8 waves; rollback strategy detailed | Comprehensive analysis; actionable plan | Large estate |

**Acceptance Criteria (All Tests):**
- ✅ Wave plan is logically consistent (dependencies respected)
- ✅ Critical path is calculated correctly
- ✅ If circular dependency detected, error raised immediately
- ✅ Rollback strategy is detailed and executable
- ✅ SLA impact is assessed
- ✅ Risk factors are identified
- ✅ API cost ≤ $0.15 per call
- ✅ Latency < 20 seconds

---

### 7.3 Acceptance Criteria

#### ACC-02-AI: BASIC Translator — Acceptance Criteria

**Functional Acceptance:**
- [ ] Translation is syntactically valid Informatica expression (parseable)
- [ ] Business logic matches BASIC intent (within Claude assessment)
- [ ] All input columns appear in output (no drops)
- [ ] All output columns are produced (no missing derivations)
- [ ] Data type conversions are handled (BASIC type → Informatica type)

**Quality Acceptance:**
- [ ] Confidence score ≥80, OR `requires_human_review = true`
- [ ] All assumptions are explicitly listed
- [ ] Warnings are clear and actionable
- [ ] Function mappings reference lookup table entries

**Performance Acceptance:**
- [ ] API latency ≤10 seconds
- [ ] Cost ≤$0.10 per call
- [ ] Tokens (input + output) ≤5000

**Compliance Acceptance:**
- [ ] No sensitive data (passwords, keys) in output
- [ ] Output contains no DataStage-specific syntax
- [ ] Output is idiomatic Informatica (not literal translation)

---

#### ACC-08-AI: C++ Operator Rewriter — Acceptance Criteria

**Functional Acceptance:**
- [ ] Java code is syntactically valid and compilable (Java 11+)
- [ ] Input schema is fully honored (all input parameters used)
- [ ] Output schema is fully produced (all output columns generated)
- [ ] Business logic is preserved exactly (within AI assessment)
- [ ] Edge cases (nulls, type coercion) are handled safely

**Security Acceptance:**
- [ ] No hardcoded credentials in Java code
- [ ] File I/O, network calls, and system operations are flagged (if unsupported)
- [ ] All external dependencies are declared

**Quality Acceptance:**
- [ ] Confidence score ≥85, OR explicit review flag
- [ ] Unsupported C++ features are clearly listed
- [ ] Suggested workarounds are provided
- [ ] Java code includes comments explaining assumptions

**Performance Acceptance:**
- [ ] API latency ≤15 seconds
- [ ] Cost ≤$0.15 per call
- [ ] Tokens ≤8000

**Compliance Acceptance:**
- [ ] Java code follows Informatica Java Transformation API contract
- [ ] No DataStage-specific API calls in output
- [ ] Suggested test cases are provided

---

#### ACC-09-AI: Design Review — Acceptance Criteria

**Functional Acceptance:**
- [ ] All issues found are legitimate (no false positives)
- [ ] Each issue has severity level, description, impact, and fix
- [ ] Severity levels are consistent (CRITICAL > HIGH > MEDIUM > LOW)
- [ ] No duplicate issues reported

**Quality Acceptance:**
- [ ] Confidence score ≥75, OR flag for additional manual review
- [ ] Best practices recommendations are idiomatic IDMC patterns
- [ ] Questions for engineer are clarifying and specific
- [ ] SLA impact estimate is provided (if applicable)

**Actionability Acceptance:**
- [ ] Every issue has a suggested fix (code snippet or approach)
- [ ] Fix complexity is rated (TRIVIAL | SIMPLE | MEDIUM | COMPLEX)
- [ ] Fixes are implementable by mid-level engineer

**Performance Acceptance:**
- [ ] API latency ≤15 seconds
- [ ] Cost ≤$0.20 per call
- [ ] Tokens ≤8000

**Compliance Acceptance:**
- [ ] No sensitive mapping data leaked in output
- [ ] Recommendations align with enterprise governance

---

#### ACC-10-AI: Dependency Analysis — Acceptance Criteria

**Functional Acceptance:**
- [ ] Wave plan respects all job dependencies (no forward dependencies)
- [ ] Critical path is calculated correctly (verified by hand)
- [ ] Circular dependencies are detected and reported (error condition)
- [ ] Hidden dependencies are identified (if any)

**Quality Acceptance:**
- [ ] Wave sizes are balanced (≤`max_wave_size` constraint)
- [ ] Pilot wave respects `pilot_job_count` target
- [ ] Risk assessment is accurate and specific
- [ ] Single points of failure are identified

**Actionability Acceptance:**
- [ ] Wave plan is executable (engineer can follow it)
- [ ] Rollback strategy is detailed with step-by-step instructions
- [ ] Data reconciliation requirements are explicit
- [ ] Go/No-Go criteria per wave are clear

**Performance Acceptance:**
- [ ] API latency ≤20 seconds
- [ ] Cost ≤$0.15 per call
- [ ] Tokens ≤8000

**Compliance Acceptance:**
- [ ] Wave plan does not exceed resource constraints
- [ ] Rollback strategy accounts for business continuity
- [ ] Risk mitigation aligns with enterprise RTO/RPO

---

### 7.4 Error Handling Specifications

#### Global Error Handling

| Error Condition | Response Code | Response Body | Retry Policy | Notes |
|---|---|---|---|---|
| **Invalid Input Schema** | 400 | `{error: "Input validation failed", details: [list]}` | Do not retry | Client must fix input |
| **API Rate Limit** | 429 | `{error: "Rate limit exceeded", retry_after_seconds: 60}` | Exponential backoff (2^n seconds) | Max 3 retries |
| **API Timeout** | 504 | `{error: "Request timeout", latency_seconds: X}` | Retry after 30 seconds | Max 2 retries |
| **Model Unavailable** | 503 | `{error: "Service unavailable", retry_after_seconds: 300}` | Retry after 5 min | Fallback to alternative model if available |
| **Token Limit Exceeded** | 400 | `{error: "Input too large", max_tokens: X, actual_tokens: Y}` | Do not retry; require input truncation | User must reduce input size |
| **Cost Threshold Exceeded** | 402 | `{error: "Cost limit reached", total_cost_usd: X, limit_usd: Y}` | Do not retry; require approval | Circuit breaker for cost overruns |
| **Invalid Output Generation** | 500 | `{error: "Output generation failed", details: "..."}` | Retry once after 10 seconds | Likely transient; log for investigation |
| **Circular Dependency Detected** (ACC-10) | 400 | `{error: "Circular dependency", cycle: [A→B→C→A]}` | Do not retry | Manual intervention required |
| **Malformed Input Code** | 400 | `{error: "Code syntax invalid", language: "C++"}` | Do not retry | User must provide valid code |
| **Missing Required Field** | 400 | `{error: "Missing required field", field: "job_id"}` | Do not retry | Client must provide all required fields |

#### Accelerator-Specific Error Handling

**ACC-02-AI (BASIC Translator):**
```python
# If Claude response contains unsupported BASIC function:
if "unsupported_function" in claude_response.flags:
    return {
        "translated_expression": null,
        "requires_human_review": True,
        "warnings": ["Unsupported function detected"],
        "fallback_action": "Manual translation required"
    }

# If confidence < 50:
if confidence_level < 50:
    return {
        "requires_human_review": True,
        "confidence_level": confidence_level,
        "recommendation": "Do not auto-deploy; requires senior engineer review"
    }
```

**ACC-08-AI (C++ Rewriter):**
```python
# If C++ has file I/O but constraint forbids it:
if has_file_io and not constraints["may_use_file_io"]:
    return {
        "java_source_code": null,
        "unsupported_features": [
            {"feature": "File I/O", "reason": "Forbidden by constraint"}
        ],
        "requires_human_review": True,
        "recommendation": "Architect must redesign operator"
    }
```

**ACC-09-AI (Design Review):**
```python
# If issue severity is CRITICAL:
if issue_severity == "CRITICAL":
    return {
        "block_deployment": True,
        "sev": "CRITICAL",
        "action_required": "Fix before deployment",
        "escalation": True
    }
```

**ACC-10-AI (Dependency Analysis):**
```python
# If circular dependency exists:
if circular_dependency_detected:
    raise CircularDependencyError(
        cycle=detected_cycle,
        message="Migration impossible; must resolve cycle manually"
    )
```

---

### 7.5 Dependency Graph

#### Accelerator Execution Dependencies

```
┌─────────────────────────────────────────────────────────────────┐
│               ACC Execution Dependency Graph                     │
└─────────────────────────────────────────────────────────────────┘

PHASE 1: Rule-Based (No AI, Execute in Parallel)
├── ACC-01 (Stage Classifier)        [No dependencies]
├── ACC-03 (Parameter Migrator)      [No dependencies]
├── ACC-04 (Connection Mapper)       [No dependencies]
├── ACC-07 (Naming Converter)        [No dependencies]
└── ACC-06 (Complexity Scorer)       [No dependencies]

    ↓ (All Phase 1 outputs available)

PHASE 2: Claude AI (Can execute in Parallel; depends on job inventory from Phase 1)
├── ACC-02-AI (BASIC Translator)     [Depends: ACC-01 job classification]
│                                    [Triggers: If BASIC_ROUTINE_FLAG = true]
│
├── ACC-05-AI (Taskflow Optimizer)   [Depends: ACC-01 job classification]
│                                    [Triggers: If JOB_TYPE = SEQUENCE_JOB]
│
├── ACC-08-AI (C++ Rewriter)         [Depends: ACC-01 job classification]
│                                    [Triggers: If CUSTOM_OPERATOR_FLAG = true]
│
└── ACC-09-AI (Design Review)        [Depends: ACC-02-AI, ACC-08-AI outputs]
                                     [Triggers: After translations complete]

    ↓ (All Phase 2 outputs available)

PHASE 3: Strategic Analysis (Requires full context; execute after Phase 2)
└── ACC-10-AI (Dependency Analysis)  [Depends: ACC-01, ACC-06, ACC-09-AI outputs]
                                     [Input: Full job graph + complexity scores]
                                     [Triggers: Once]

    ↓ (Output: Wave plan)

PHASE 4: Execution & Review
├── Wave 0 (Pilot): [Highest-confidence jobs from ACC-10 output]
├── Wave 1–N: [Subsequent jobs per wave plan]
└── Rollback Checkpoints: [Every wave; per ACC-10 rollback strategy]
```

#### Data Flow Between Accelerators

```
DSX Export
    │
    ├──→ ACC-01 ──┐
    │            ├──→ ACC-02-AI (if BASIC_FLAG)
    │            ├──→ ACC-08-AI (if CUSTOM_OP_FLAG)
    │            ├──→ ACC-05-AI (if SEQUENCE_FLAG)
    │            └──→ ACC-06 → Scoring matrix
    │
    ├──→ ACC-03 → Parameter files
    ├──→ ACC-04 → Connection configs
    ├──→ ACC-07 → Naming inventory
    │
    └──→ Job dependency extraction
         │
         └──→ ACC-10-AI ← [ACC-02, ACC-08, ACC-09 outputs]
              │
              └──→ Migration wave plan
```

#### Blocking Dependencies (Hard Stops)

| Condition | Blocks | Resolution |
|---|---|---|
| Circular dependency in job graph | ACC-10-AI execution | Manual intervention; resolve cycle in DataStage first |
| Invalid input schema for ACC-08-AI | C++ rewriting | Provide valid C++ code; skip if code unavailable |
| Confidence < 50 on ACC-02-AI output | Auto-deployment | Manual engineer review required before use |
| Critical issues found by ACC-09-AI | Wave deployment | Fix issues before proceeding to next wave |

---

### 7.6 Validation Rules & Constraints

#### Input Validation Rules (All Accelerators)

| Rule | Constraint | Validation Method | Error Response |
|---|---|---|---|
| **Uniqueness: job_id** | No duplicate job_ids per batch | `len(job_ids) == len(set(job_ids))` | 400 Bad Request |
| **Non-Empty: Code** | BASIC/C++ code must be >0 chars | `len(code) > 0` | 400 Bad Request |
| **Max Length: Code** | BASIC ≤1000, C++ ≤5000 chars | `len(code) <= max_length` | 400 Bad Request |
| **Format: Timestamp** | ISO8601 format | `RE.match(ISO8601_PATTERN, ts)` | 400 Bad Request |
| **Enum: Severity** | Must be CRITICAL\|HIGH\|MEDIUM\|LOW | `severity in ALLOWED_SEVERITIES` | 400 Bad Request |
| **Range: Confidence** | 0–100 | `0 <= confidence <= 100` | 400 Bad Request |
| **Positive Integer: job_count** | Load volume, SLA must be >0 | `value > 0` | 400 Bad Request |
| **Schema Consistency** | Input cols ≠ Output cols (C++ rewriter) | `len(input_cols) >= 1 and len(output_cols) >= 1` | 400 Bad Request |

#### Post-Call Output Validation

| Rule | Constraint | Validation Method | Error Response |
|---|---|---|---|
| **Syntax: Expression** (ACC-02) | Must parse as Informatica expression | Try parse; if fails, flag | Fallback to manual review flag |
| **Syntax: Java Code** (ACC-08) | Must compile (Java 11+) | Compile in test; if fails, flag | Fallback to manual review flag |
| **Consistency: Issue Count** (ACC-09) | sum(severities) == total_issues | Validate arithmetic | Log warning; do not block |
| **Consistency: Wave Plan** (ACC-10) | All jobs appear in exactly 1 wave | `union(all_waves) == all_jobs and len(intersections) == 0` | Error; regenerate |
| **Constraint: Cost** | cost_usd ≤ circuit breaker | `cost <= MAX_COST_PER_CALL` | 402 Payment Required |
| **Constraint: Latency** | latency ≤ SLA per accelerator | `latency_seconds <= SLA_SECONDS` | Warning logged; request allowed |
| **Range: Confidence** | 0–100 | `0 <= confidence <= 100` | Error; regenerate |

#### Business Logic Constraints

| Constraint | Description | Enforcement |
|---|---|---|
| **No Hard-Coded Values** | Params should not contain sensitive data (passwords, API keys) | ACC-09 flags; human review required |
| **Error Handling Complete** | All transformation error paths should be covered | ACC-09 flags; warning if missing |
| **SLA Achievable** | Wave plan must fit within load window and business SLA | ACC-10 flags `sla_achievable=false` if not met |
| **Critical Path ≤ SLA** | Critical path latency must be ≤ SLA minutes | ACC-10 calculated and reported |
| **Max Wave Size** | No single wave exceeds resource constraints | ACC-10 enforces `max_wave_size` |
| **Pilot Wave Target** | Wave 0 should have ≤ `pilot_job_count` jobs | ACC-10 tries to target; may exceed if unavoidable |
| **Risk Mitigation** | High-risk jobs in early waves; low-risk jobs in later waves | ACC-10 sequences by risk level |

#### Deployment Safety Constraints

| Constraint | Description | Enforcement |
|---|---|---|
| **Confidence Threshold** | Do not auto-deploy if confidence < 80 (configurable) | Manual review flag; block auto-deploy |
| **Review SLA** | All CRITICAL issues must be reviewed within 4 hours | Dashboard alert; escalation if overdue |
| **Rollback Plan Required** | No wave deployment without documented rollback steps | ACC-10 output must include rollback_strategy |
| **Pilot Success Gate** | Wave 1+ cannot start until Wave 0 passes QA | Wave plan blocks dependent waves |
| **Data Reconciliation** | Post-migration row counts must match source ±0.1% | Automated check before wave sign-off |

---

## Appendix C: SDD Compliance Checklist

Use this checklist to verify SDD compliance before deployment.

### Pre-Deployment Checklist

**Interface Specifications:**
- [ ] All input schemas documented (field type, required/optional, constraints)
- [ ] All output schemas documented (field type, nullable, ranges)
- [ ] Input validation rules specified for each accelerator
- [ ] Post-call validation rules specified for each accelerator

**Test Cases:**
- [ ] ≥10 test cases per accelerator (happy path + edge cases)
- [ ] Test cases document input, expected output, pass criteria
- [ ] All test cases are executable (not just examples)
- [ ] Edge cases are covered (empty input, max size, invalid syntax, etc.)

**Acceptance Criteria:**
- [ ] Functional acceptance criteria defined (logic, schema, correctness)
- [ ] Quality acceptance criteria defined (confidence, assumptions, clarity)
- [ ] Performance acceptance criteria defined (latency, cost, tokens)
- [ ] Compliance acceptance criteria defined (security, data, format)

**Error Handling:**
- [ ] Global error handling matrix documented
- [ ] Accelerator-specific error handling documented
- [ ] Retry policies defined (max retries, backoff strategy)
- [ ] Circuit breaker thresholds defined (cost, tokens, latency)

**Dependencies:**
- [ ] Accelerator execution order documented (Gantt-style)
- [ ] Data flow between accelerators specified
- [ ] Blocking dependencies identified (hard stops)
- [ ] Parallel execution opportunities identified

**Constraints:**
- [ ] Input validation constraints specified
- [ ] Output validation constraints specified
- [ ] Business logic constraints specified
- [ ] Deployment safety constraints specified

### Deployment Readiness

- [ ] All test cases pass (100%)
- [ ] All acceptance criteria are met
- [ ] All error handling is implemented (no unhandled exceptions)
- [ ] All dependencies are satisfied (no circular deps)
- [ ] All constraints are enforced (validation logic in place)
- [ ] Documentation is complete (README, API docs, prompt templates)
- [ ] Cost budget is confirmed (total cost ≤ approved limit)
- [ ] Human review process is defined (SLA, checklist, escalation)

---

*— End of Formal SDD Specification —*

*This specification is now SDD-compliant and ready for implementation. All accelerators have defined interfaces, test cases, acceptance criteria, error handling, dependencies, and constraints.*
