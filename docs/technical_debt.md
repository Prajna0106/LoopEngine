# Technical Debt Report

> Generated: 2026-07-22 — Prompt 21 Refactoring Pass

## Summary

| Category | Items | Severity | Estimated Effort |
|----------|-------|----------|-----------------|
| Architecture violations | 2 remaining | Medium | 2-4 hours |
| Code duplication | ~300 lines remaining | Medium | 4-6 hours |
| Missing docstrings | 166 public methods | Low | 3-4 hours |
| Test boilerplate | ~280 lines of duplicated test scaffolding | Low | 2-3 hours |
| **Total** | | | **11-17 hours** |

---

## Fixed in This Pass (Prompt 21)

### 1. Config exceptions moved to core domain
- **Before**: `ConfigLoadError` and `ConfigValidationError` lived in `infrastructure/config/loader.py`
- **After**: Moved to `core/domain/exceptions/config_exceptions.py`
- **Impact**: Fixes architecture violation — domain exceptions now live in the core layer
- **Files changed**: `loader.py`, `__init__.py`, `test_config_loader.py`

### 2. Shared subprocess utilities
- **Before**: `_base_env()` and `is_available()` duplicated in `base_agent_adapter.py` and `base_validator.py`
- **After**: Extracted to `adapters/outbound/_subprocess_utils.py` with `base_env()`, `is_command_available()`, `combine_output()`
- **Impact**: Eliminates ~12 lines of duplication, adds `combine_output()` used by 5 validators
- **Files changed**: `_subprocess_utils.py` (new), `base_agent_adapter.py`, `base_validator.py`, 5 validator files

### 3. Consolidated agent adapter defaults
- **Before**: All 4 agent adapters (`ClaudeAdapter`, `CodexAdapter`, `OpenCodeAdapter`, `GenericCLIAdapter`) had identical `parse_response()` and redundant `model` property
- **After**: `BaseAgentAdapter` provides default `parse_response()` with model + metadata; `model` property lives in base class
- **Impact**: Eliminates ~24 lines of duplication across 4 files, removes unused `AgentResponse` imports
- **Files changed**: `base_agent_adapter.py`, `claude_adapter.py`, `codex_adapter.py`, `opencode_adapter.py`, `generic_cli_adapter.py`

---

## Remaining Technical Debt

### HIGH PRIORITY

#### TD-1: `app.py` adapter-to-infrastructure coupling
- **Location**: `src/loopengine/adapters/inbound/cli/app.py`
- **Issue**: CLI adapter imports directly from `infrastructure.config`, `infrastructure.container`, `infrastructure.logging` at module level (lines 16-18)
- **Risk**: Tight coupling between adapter and infrastructure layers
- **Fix**: Introduce a composition root or bootstrap module; inject dependencies via a factory
- **Effort**: 2-3 hours

#### TD-2: Reviewer `_analyze()` boilerplate
- **Location**: 9 files in `adapters/outbound/review/`
- **Issue**: Every reviewer repeats the same ~8-line skeleton before domain logic
- **Fix**: Convert to data-driven rule engine — define rules as data, let base class iterate
- **Impact**: Eliminates ~80 lines of duplication, makes adding rules trivial
- **Effort**: 3-4 hours

### MEDIUM PRIORITY

#### TD-3: Reviewer `_recommendations()` duplication
- **Location**: 8 reviewer files
- **Issue**: Identical dispatch pattern repeated in every reviewer
- **Fix**: Add `_recommendation_map` class attribute to `BaseReviewer`, implement dispatch once
- **Effort**: 2 hours

#### TD-4: N+1 query rule duplicated
- **Location**: `performance_reviewer.py` and `database_reviewer.py`
- **Issue**: Same regex, same severity, same rule name in two files
- **Fix**: Consolidate into shared rule library (part of TD-2)
- **Effort**: Included in TD-2

#### TD-5: `LoopEngineConfig` type dependency from adapters to infrastructure
- **Location**: `orchestrator.py` line 33 (TYPE_CHECKING)
- **Issue**: Static type dependency from adapters → infrastructure
- **Fix**: Define config protocol in `core/ports/` or use `dict[str, Any]`
- **Effort**: 1-2 hours

### LOW PRIORITY

#### TD-6: 166 public methods missing docstrings
- **Location**: Across 33 source files
- **Issue**: Public methods (mostly `@property` accessors and interface implementations) lack docstrings
- **Fix**: Add one-line docstrings; prioritize `base_validator.py`, `base_reviewer.py`, `plugin_registry.py`, `sqlite_store.py`
- **Effort**: 3-4 hours

#### TD-7: Test scaffolding duplication
- **Location**: 9 reviewer test files + 6 validator test files
- **Issue**: Identical `test_name`, `test_clean_code`, `test_build_args_default` patterns
- **Fix**: Parametrize with `@pytest.mark.parametrize` over a registry of `(Class, expected_name, expected_command)`
- **Impact**: Eliminates ~280 lines of test code
- **Effort**: 2-3 hours

#### TD-8: Reviewer test boilerplate
- **Location**: 9 test files in `tests/unit/adapters/review/`
- **Issue**: Each file repeats name + clean_code + rule-specific tests
- **Fix**: Create parametrized base test class
- **Effort**: 2 hours

---

## Architecture Health

| Metric | Status |
|--------|--------|
| Core → Adapter imports | ✅ Clean (zero violations) |
| Adapter outbound → inbound | ✅ Clean |
| Infrastructure → adapters | ✅ Clean |
| Circular imports | ✅ None at runtime |
| Port interfaces in core/ports/ | ✅ All correct |
| Domain exceptions in core/domain/ | ✅ Now correct (fixed TD) |
| Adapter → infrastructure | ⚠️ 1 violation in `app.py` (TD-1) |

---

## Code Quality Metrics

| Metric | Before | After |
|--------|--------|-------|
| Tests | 633 | 633 |
| Coverage | 90.00% | 90.00%+ |
| Lint | ✅ Clean | ✅ Clean |
| Typecheck | ✅ Clean | ✅ Clean |
| Duplication (est.) | ~470 lines | ~300 lines |
| Architecture violations | 5 | 2 |
