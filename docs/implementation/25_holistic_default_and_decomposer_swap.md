# 25 — Holistic Default & Decomposer Swap Infrastructure

> **Status**: Complete — all phases implemented, verified, and documented  
> **Date**: 2026-03-22  
> **Supersedes**: removed `experimental_decomposition` boolean in favour of `decomposition_mode` string  

---

## Motivation

The codebase's success depends on a **working, trustworthy default review mode**.
Naive sentence-level decomposition distorts context on dependency-heavy claims
and has not earned trust-grade status. Holistic single-claim review must be the
unconditional default at every layer — API, engine, smoke runners, CLI — while
decomposition remains available as an explicit, auditable opt-in for dedicated
experiments.

---

## Rule-Set

| Rule | Value |
|---|---|
| **Default mode** | `holistic` — single-claim review |
| **Experimental mode** | `rule_based` — sentence-split decomposition |
| **Control surfaces** | YAML config, Python parameter, CLI flag |
| **Precedence** | CLI > Python param > config file default |
| **Live calls** | Ladder tests only; all other tests remain fully mocked |
| **Dual-mode runs** | Never automatic — dedicated A/B experiment only |

---

## Phase 1 — Decomposer Resolution Infrastructure

### 1.1 Config model
**File**: `symposia/config/models.py`

Add `decomposition_mode: str = "holistic"` to the config. Allowed values:
`"holistic"`, `"rule_based"`.

### 1.2 Resolver functions
**File**: `symposia/kernel/decomposer.py`

```
DECOMPOSITION_MODES = {
    "holistic": HolisticSubclaimDecomposer,
    "rule_based": RuleBasedSubclaimDecomposer,
}

resolve_decomposer(mode: str) -> SubclaimDecomposer
resolve_decomposition_mode(cli, param, config_default) -> str
```

`resolve_decomposition_mode` implements strict precedence:
CLI > Python param > config file default > `"holistic"`.

### 1.3 YAML loader
**File**: `symposia/config/loader.py`

Parse optional `decomposition_mode` from YAML root. Absent = `"holistic"`.

### 1.4 YAML examples
**Files**: `examples/symposia.yaml`, `examples/symposia.local.yaml`,
`examples/symposia.test.yaml`

Add commented-out line: `# decomposition_mode: holistic  # holistic | rule_based`

---

## Phase 2 — Thread Mode Through API + Engine

### 2.1 `validate()` signature
**File**: `symposia/api.py`

Add `decomposition_mode: str = "holistic"`. Resolution inside `validate()`:

1. If `decomposition_mode` is explicitly provided → use it
2. Else → `"holistic"`

### 2.2 `InitialReviewEngine`
**File**: `symposia/initial/engine.py`

Accept `decomposition_mode: str = "holistic"`. Use `resolve_decomposer()`.
Emit mode string in `execution_policy`.

---

## Phase 3 — Smoke Runners: Holistic Default

**Core behavior change.** Every smoke runner switches from hardcoded
`RuleBasedSubclaimDecomposer` to parameterized, holistic-default.

### 3.1 Comparison runner
**File**: `symposia/smoke/openai_initial_comparison.py`

- `run_openai_initial_comparison()`: add `decomposition_mode: str = "holistic"`
- `_run_variant()`: accept `decomposer` instance instead of hardcoding
- Replace static `REVIEW_MODE`/`DECOMPOSITION_MODE` with dynamic derivation
- All artifact builders: mode-derived values

### 3.2 Trust evaluation runner
**File**: `symposia/smoke/openai_initial_trust_evaluation.py`

Add `decomposition_mode` param to `run_openai_initial_trust_evaluation()` and
`_v2()`, pass through to comparison call.

### 3.3 Silver labeling runner
**File**: `symposia/smoke/openai_initial_silver_labeling.py`

Same pattern — add param, pass through, update artifacts.

### 3.4 Dedicated decomposition experiment
`run_committee_trust_decomposition_experiment()` is the **sole A/B path**.
It explicitly passes `decomposition_mode="rule_based"` to its comparison calls.

---

## Phase 4 — CLI Flag

### 4.1 CLI option
**File**: `symposia/terminal/cli.py`

Add `--decomposition-mode` global option, choices `["holistic", "rule_based"]`,
default `None`. Thread to `ask` command.

### 4.2 CLI bridge
**File**: `symposia/terminal/services.py`

`run_deliberation()` accepts and passes `decomposition_mode`.

---

## Phase 5 — Tests

| Test | File | What |
|---|---|---|
| Resolver + precedence | `test_phase1_primitives.py` | `resolve_decomposer()` returns correct class; precedence logic |
| Engine mode string | `test_phase3_initial.py` | Default → "holistic"; explicit "rule_based"; backward compat |
| Smoke runner defaults | `test_openai_initial_comparison_runner.py` | Default artifacts are holistic; explicit rule_based variant |
| Trust runner defaults | `test_openai_initial_trust_evaluation_runner.py` | Holistic default fixtures |
| Silver labeling defaults | `test_openai_initial_silver_labeling.py` | Holistic default fixtures |
| Config loading | `test_config.py` | YAML `decomposition_mode` parsed; absent → "holistic" |
| API backward compat | `test_phase9_primary_surface.py` | Both old bool and new string work; string wins |

---

## Phase 6 — Run Ladder Live

1. `PYTHONPATH=. pytest -m "core or ladder"` — all green
2. `bash scripts/run_experiment_ladder_tests.sh` — holistic default with real API calls

---

## Phase 7 — Documentation

- Update `docs/implementation/24_decomposition_boundary_note.md` — control surfaces, precedence
- Update `CHANGELOG.md` — `decomposition_mode` replaces bool, three surfaces, smoke holistic
- Update `docs/configuration.md` — YAML key, CLI flag, Python param, precedence
- Update `docs/implementation/03_system_spec.md` — resolver in canonical contracts

---

## Artifact Vocabulary

| Layer | Field | Holistic value | Decomposed value |
|---|---|---|---|
| Config / param | `decomposition_mode` | `"holistic"` | `"rule_based"` |
| Artifact display | `review_mode` | `"holistic_single_claim"` | `"decomposed_experimental"` |
| Artifact display | `decomposition_mode` | `"no_decomposition"` | `"rule_based_sentence_split"` |

Config values are short identifiers. Artifact values are richer audit labels.

---

## Verification Checklist

- [x] `pytest -m core` — 125 passed, 120 deselected
- [x] `pytest -m ladder` — 33 passed, 212 deselected
- [x] `bash scripts/run_experiment_ladder_tests.sh` — 158 passed, 87 deselected
- [x] `pytest test_phase1_primitives.py -k resolve` — 9 passed, 11 deselected
- [x] `pytest test_openai_initial_comparison_runner.py` — 10 passed
- [x] CLI: `--decomposition-mode {holistic,rule_based}` global option present and functional
- [x] All output artifacts carry `review_mode` metadata via `_REVIEW_MODE_LABELS` / `_DECOMPOSITION_MODE_LABELS`

---

## Completion Report

**Verified**: 2026-03-22  
**Test baseline**: 158 core+ladder passed, 87 deselected, 0 failures

### Phases completed

| Phase | Scope | Files changed |
|---|---|---|
| 1 — Resolver infrastructure | Config model, decomposer registry, resolver functions | `config/models.py`, `kernel/decomposer.py`, `kernel/__init__.py` |
| 2 — API + Engine threading | Single `decomposition_mode` param, removed `experimental_decomposition` | `api.py`, `initial/engine.py` |
| 3 — Smoke runners holistic | All runners default to holistic; decomposition A/B is explicit opt-in | `smoke/openai_initial_comparison.py`, `smoke/openai_initial_trust_evaluation.py`, `smoke/openai_initial_silver_labeling.py` |
| 4 — CLI flag | `--decomposition-mode` global option, threaded to services | `terminal/cli.py`, `terminal/services.py` |
| 5 — Tests | 10 resolver/precedence tests, config default test, fixture updates | `test_phase1_primitives.py`, `test_config.py`, 3 smoke test files |
| 6 — Ladder live | All core + ladder tests green | `scripts/run_experiment_ladder_tests.sh` |
| 7 — Documentation | Doc 24 updated, doc 25 written, YAML examples annotated | `docs/implementation/24_decomposition_boundary_note.md`, this file |

### Additional work (post-plan)

| Item | Scope | Files changed |
|---|---|---|
| Profile personality injection | `JurorPromptBuilder.build()` now loads `Profile` and injects stance, evidence demand, safety bias into system prompt | `jurors/llm.py` |
| Prompt builder tests | 3 tests verifying distinct personality per profile, field inclusion, JSON contract | `test_phase1_primitives.py` |
| Generic profile purpose upgrade | All 5 generic purposes rewritten from terse labels to substantive LLM instructions with Catches/Does-NOT-fire-on guidance | `profiles/defaults.py` |

### Precedence verification

```
CLI flag  >  Python param  >  YAML config  >  unconditional "holistic"
```

Tested in `test_phase1_primitives.py`:
- `test_resolve_decomposition_mode_cli_wins_over_param_and_config`
- `test_resolve_decomposition_mode_param_wins_over_config`
- `test_resolve_decomposition_mode_config_used_when_others_none`
- `test_resolve_decomposition_mode_defaults_to_holistic`
- `test_resolve_decomposition_mode_rejects_unknown`

### Artifact vocabulary verified

| Layer | Holistic | Decomposed |
|---|---|---|
| Config/param | `"holistic"` | `"rule_based"` |
| `review_mode` artifact | `"holistic_single_claim"` | `"decomposed_experimental"` |
| `decomposition_mode` artifact | `"no_decomposition"` | `"rule_based_sentence_split"` |
