# System Specification

## Purpose

This document specifies the build of Symposia as a serious library rather than a whitepaper concept.

The build target is:
- simple public surface
- strong internal contracts
- deterministic verdict compilation
- institution-grade traceability
- explicit profile and profile-set control without surface sprawl

## Goals

### Functional goals
- validate claims and compound content
- support multiple domains
- run many jurors concurrently
- stop early when Round 0 is decisive
- escalate only disputed or risky items
- return typed, auditable verdicts
- support default and custom profile sets

### Non-functional goals
- low-friction API
- high observability
- reproducibility
- extensibility without surface sprawl
- graceful provider degradation

## Non-goals for v1
- full legal opinion generation
- open-ended multi-round debate loops
- fully automatic truth discovery without sources
- uncontrolled natural-language-only reasoning chains
- juror reputation based primarily on consensus alignment
- user-facing per-juror personality theatre

## System modules

### 1. Request Gateway
Receives the validation request and normalises:
- content
- domain
- mode
- jurisdiction
- profile
- profile set
- trace mode
- execution settings

### 2. Claim Kernel
Responsible for:
- holistic claim normalisation by default
- optional experimental content segmentation
- optional experimental subclaim extraction
- instruction detection
- dependency mapping when decomposition is enabled
- claim bundle normalisation

Outputs:
- `ClaimBundle`
- `Subclaim[]`
- dependency graph

Default runtime policy:
- create one subclaim containing the full claim text
- preserve full context unless the caller explicitly opts into experimental decomposition
- treat sentence-splitting decomposition as non-default until a more faithful dependency-aware method exists

### 3. Evidence Router
Chooses evidence policy per request:
- closed-book
- retrieval-backed
- caller-supplied evidence pack
- hybrid

Outputs:
- `EvidencePack`

### 4. Profile Registry
Resolves the adjudication configuration for the run.

Responsible for:
- profile lookup
- profile-set lookup
- default domain set resolution
- profile compatibility checks
- policy inheritance
- version pinning

Outputs:
- `ResolvedProfileSet`

### 5. Juror Engine
Creates the juror cohort:
- model provider
- reasoning profile
- role lens
- prompt template
- retrieval slice
- domain profile

Runs the adjudication concurrently.

Outputs:
- `JurorDecision[]`

### 6. Calibration Registry
Stores:
- domain calibration scores
- seed-set performance
- versioned model records
- weighting metadata

Outputs:
- calibrated weights for a given run

### 7. Aggregation Engine
Takes juror decisions and computes:
- support score
- contradiction score
- sufficiency score
- issuance score
- dissent indicators
- escalation decision

### 8. Escalation Engine
If required:
- select disputed subclaims
- construct structured rebuttal packet
- run one challenge round
- update compiled result

### 9. Verdict Compiler
Maps raw internal judgments into public outputs:
- verdict
- certainty
- issuance
- risk
- caveats
- summary
- dissent

### 10. Trace Engine
Produces:
- event log
- juror-level reasoning summaries
- evidence references
- decision graph
- final report object

### 11. Policy Layer
Domain-specific constraints and rules.

Examples:
- medical high-risk advice rules
- jurisdiction-sensitive legal rules
- finance recommendation restrictions

## Core entities

### ValidationRequest

```json
{
  "content": "string",
  "domain": "general | medical | legal | finance | custom",
  "mode": "validate",
  "jurisdiction": "optional string",
  "profile": "optional string",
  "profile_set": "optional string",
  "trace": false,
  "max_rounds": 2
}
```

### ClaimBundle

```json
{
  "bundle_id": "cb_...",
  "raw_content": "string",
  "subclaims": [],
  "dependencies": []
}
```

### Subclaim

```json
{
  "subclaim_id": "sc_...",
  "text": "string",
  "kind": "fact | instruction | inference | definition | normative",
  "criticality": "low | medium | high",
  "depends_on": []
}
```

### Profile

```json
{
  "profile_id": "sceptical_verifier_v1",
  "label": "Sceptical Verifier",
  "purpose": "challenge weak support and overclaiming",
  "behaviour": {
    "stance": "sceptical",
    "evidence_demand": "high",
    "safety_bias": "moderate",
    "literalism": "medium"
  },
  "failure_modes": ["may over-escalate borderline claims"],
  "version": "v1"
}
```

### ProfileSet

```json
{
  "profile_set_id": "medical_strict_v1",
  "domain": "medical",
  "profiles": [
    "balanced_reviewer_v1",
    "sceptical_verifier_v1",
    "evidence_maximalist_v1",
    "literal_parser_v1",
    "risk_sentinel_v1"
  ],
  "thresholds": {
    "support": 0.80,
    "confidence": 0.82
  },
  "max_rounds": 2,
  "issuance_policy": "conservative"
}
```

### JurorAssignment

```json
{
  "juror_id": "jr_...",
  "profile_id": "risk_sentinel_v1",
  "provider": "openai:gpt-x",
  "retrieval_policy": "guideline_first",
  "weight_cap": 1.0
}
```

### JurorDecision

```json
{
  "juror_id": "jr_...",
  "subclaim_id": "sc_...",
  "supported": true,
  "contradicted": false,
  "sufficient": true,
  "issuable": false,
  "confidence": 0.86,
  "rationale": "string",
  "citations": [],
  "objection_level": "none | minor | critical"
}
```

### CompiledSubclaimVerdict

```json
{
  "subclaim_id": "sc_...",
  "verdict": "validated | rejected | insufficient | contested",
  "certainty": "high | moderate | low | very_low",
  "issuance": "safe_to_issue | issue_with_caveats | requires_expert_review | unsafe_to_issue",
  "risk": "low | medium | high",
  "caveats": [],
  "agreement": 0.0
}
```

### ValidationResult

```json
{
  "run_id": "spm_...",
  "verdict": "validated_with_caveats",
  "certainty": "moderate",
  "issuance": "issue_with_caveats",
  "risk": "high",
  "agreement": 0.82,
  "summary": "string",
  "caveats": [],
  "subclaims": [],
  "profile_set_used": "medical_strict_v1",
  "rounds_used": 1,
  "trace_id": "tr_..."
}
```

## Processing lifecycle

### Step 1. Normalise request
- validate schema
- apply defaults
- resolve profile or profile set

### Step 2. Resolve profile set
- if `profile_set` is explicit, load it
- else if `profile` is explicit, inject it into the domain default set where compatible
- else load the domain default set
- pin versions and policy inheritance

### Step 3. Build claim bundle
- split the input into adjudicable units
- mark critical or actionable units
- link dependencies

### Step 4. Build evidence pack
- attach supplied evidence or fetch via configured retrieval
- annotate source type and provenance

### Step 5. Spawn jurors
- determine cohort size from the resolved profile set
- assign profiles to juror slots
- inject domain and role guidance
- run independently

### Step 6. Aggregate Round 0
For each subclaim:
- compute weighted support
- compute weighted contradiction
- compute weighted sufficiency
- compute weighted issuance

### Step 7. Evaluate stopping rules
Stop if:
- verdict thresholds are met
- no critical objection survives
- certainty is above floor
- profile-set rules permit stop

### Step 8. Escalate if required
- select only disputed or risk-bearing subclaims
- build challenge packet
- re-run bounded adjudication

### Step 9. Compile final result
- map subclaim results to public verdict
- surface caveats and issuance status
- include profile-set identifier in metadata

## Profile resolution doctrine

### Default behaviour
A caller should almost never need to think about profile sets.

Given only:
- `content`
- `domain`

Symposia should choose the domain default profile set automatically.

### Advanced behaviour
Advanced callers may:
- choose a named profile set
- supply an overlay profile
- author and register custom sets

### Hard rule
Profiles may alter scrutiny and emphasis, but they must not alter the public verdict schema or core truth standard.

## Phase 1 canonical contracts (frozen names)

To prevent downstream drift, these Phase 1 object names are canonical:
- `ClaimBundle`
- `Subclaim`
- `SubclaimKind`
- `CompiledSubclaimVerdict`
- `ValidationResult`
- `VerdictClass`
- `Certainty`
- `Issuance`
- `Risk`

The decomposition contract is also canonical at this stage:
- `SubclaimDecomposer`
- `HolisticSubclaimDecomposer`
- `RuleBasedSubclaimDecomposer`

Interpretation:
- `HolisticSubclaimDecomposer` is the default runtime path.
- `RuleBasedSubclaimDecomposer` is maintained as an explicit experimental path.

For Phase 3, these names are canonical for initial review execution:
- `JurorDecision`
- `SubclaimDecision`
- `CompletionDecision`
- `CoreTrace`
- `InitialReviewEngine`

For Phase 5, these names are canonical for escalation contracts:
- `EscalationDecision`
- `EscalationReason`
- `EscalatedIssue`
- `DissentRecord`
- `ChallengePacket`
- `NextStageReviewInput`
- `NextStageReviewResult`
- `plan_escalation`

Any rename of these symbols after Phase 1 requires an explicit ADR and migration note before merge.

## Build principle

Profiles are first-class in the engine, but second-class on the surface.
