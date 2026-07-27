# AMIP Developer & Architectural Governance Guide

---

## 1. Coding Standards & Conventions

- **Python Version**: Python 3.11+
- **Type Annotations**: All function signatures in `amip/` MUST include explicit type hints (`from __future__ import annotations`, `typing.Dict`, `typing.Optional`, etc.).
- **Docstrings**: Google-style docstrings are mandatory for all classes and public functions.
- **Naming Conventions**:
  - Modules & Files: `snake_case.py`
  - Classes: `PascalCase` (e.g. `AmipSupervisorAgent`, `AmipExecutionContext`)
  - Functions & Variables: `snake_case`
  - Constants: `UPPER_SNAKE_CASE`
- **Zero Invasive Modification Policy**: Code within `amip/` must NEVER modify pre-existing domain services or routers directly. All extensions must use adapters or supervisory wrappers.

---

## 2. Package Responsibility Boundaries

- `amip/models/`: Contains ONLY dataclasses and Pydantic models (No business logic).
- `amip/interfaces/`: Contains ONLY Abstract Base Classes (`abc.ABC`) defining platform contracts.
- `amip/exceptions/`: Contains custom exception types inheriting from `Exception`.
- `amip/context/`: Manages state blackboards and context dictionary objects.
- `amip/supervisor/`: Manages task planning, goal execution, and supervisor loops.
- `amip/dispatcher/`: Handles event routing and service invocation.
- `amip/decision/`: Manages confidence evaluation rules.
- `amip/explainability/`: Manages audit provenance graphs.
- `amip/resilience/`: Manages retries, circuit breakers, and fallbacks.

---

## 3. Dependency Rules & Architectural Constraints

### Core Rule: Upward & Horizontal Isolation
1. **AMIP Package Isolation**: Components inside `amip/` may depend on core application models (`app.models.*`) and configuration (`app.config.settings`).
2. **Domain Service Protection**: Existing domain services (`app.services.bills`, `app.services.ai_extraction`, etc.) MUST NOT depend on `amip/` (Zero circular dependencies).
3. **Internal Hierarchy**:
   - `models/`, `interfaces/`, `exceptions/`, `utils/` have ZERO dependencies on other `amip/` sub-packages.
   - `context/`, `explainability/`, `resilience/` depend ONLY on `models/`, `interfaces/`, `exceptions/`, `utils/`.
   - `dispatcher/`, `decision/` depend on `context/`, `models/`, `interfaces/`.
   - `supervisor/` depends on `dispatcher/`, `decision/`, `context/`, `resilience/`, `explainability/`.

---

## 4. Communication Matrix (Allowed vs. Forbidden)

```
+-----------------------------------++-----------------------------------+
|       ALLOWED COMMUNICATIONS      ||      FORBIDDEN COMMUNICATIONS     |
+-----------------------------------++-----------------------------------+
| AMIP Supervisor -> Dispatcher     || Domain Services -> AMIP Internal  |
| AMIP Supervisor -> Context Manager|| Low-Level Engines -> Supervisor   |
| AMIP Dispatcher -> Domain Services|| Circular imports between sub-pkgs |
| AMIP Supervisor -> Resilience Ctrl|| Direct DB mutation inside Models  |
+-----------------------------------++-----------------------------------+
```

### ✅ Allowed Communication:
- `AMIPSupervisorAgent` ➔ `AMIPContextManager`
- `AMIPSupervisorAgent` ➔ `AMIPTaskDispatcher`
- `AMIPSupervisorAgent` ➔ `AMIPExplainabilityEngine`
- `AMIPSupervisorAgent` ➔ `AMIPResilienceController`
- `AMIPTaskDispatcher` ➔ Existing Domain Services (`BulkImportService`, `CopilotOrchestrator`, etc.)

### ❌ Forbidden Communication:
- Existing Domain Services ➔ `AMIPSupervisorAgent` (Prevents circular dependencies)
- Sub-packages (`amip/models/`, `amip/interfaces/`) ➔ High-level orchestrators (`amip/supervisor/`)
- `AMIPResilienceController` ➔ Direct database schema modification

---

*AMIP Developer & Architectural Governance Guide — Phase 9 Checkpoint 0*
