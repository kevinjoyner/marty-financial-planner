# Technical Roadmap & Architecture

## System Architecture

Marty is a specialized **Single Page Application (SPA)** with a Python simulation backend.

### Backend (The Brain)
* **Framework:** Python / FastAPI.
* **Database:** SQLite (dev) / PostgreSQL (prod) via SQLAlchemy.
* **Engine:** Pure Python logic `app/engine`. Stateless projection capabilities.
* **API Design:** RESTful. 
    * `/scenarios`: CRUD for persistent data.
    * `/project`: **Simulation Endpoint**. Accepts a Scenario ID + a JSON body of `overrides`. Returns the projection array. Does *not* write to DB.

### Frontend (The Interface)
* **Framework:** Vue 3 (Composition API).
* **Build Tool:** Vite.
* **State Management:** Pinia (`simulation` store).
* **Styling:** Tailwind CSS.
* **Components:**
    * `ModellingBar.vue`: Universal "Pinning" system for overriding any variable.
    * `ProjectionChart.vue`: Chart.js wrapper handling "Ghost Line" rendering and Gantt-style annotations.
    * `Drawer.vue`: Reusable slide-over for forms.
* **Routing:** Vue Router (Dashboard, Income, Accounts, Transactions, Tax, Automation).

---

## Development Phases (Completed)

### Phase 1-7: Foundation
- [x] Python Engine Core (Cashflow, Tax, Growth).
- [x] Database Models (SQLAlchemy).
- [x] Automation Rules Engine (Sweeps, Waterfalls).
- [x] UK Tax Logic implementation.

### Phase 8: The Financial Cockpit
- [x] **Architecture:** Migrate to Vue 3 + Vite + Pinia.
- [x] **Simulation Engine:** Implement non-destructive `/project` endpoint with override capabilities.
- [x] **Modelling Bar:** Universal Pinning for any numeric/date field.
- [x] **Visualization:** Interactive Chart.js integration (Baseline vs Projected).

### Phase 9: Persistence & Entity Management
- [x] **Deep Entity Management:** Specialized drawers for Mortgages, Income (Pre/Post tax), and Rules.
- [x] **Tax & People:** New view for managing Owners and Tax Limits (ISA/Pension caps).
- [x] **Data Portability:** Robust JSON Import/Export with legacy data migration logic.
- [x] **Session History:** In-memory undo/redo stack for safe experimentation.

### Phase 10: User Trust & Guidance
- [x] **User Guide:** Integrated "Handbook" view.
- [x] **Audit Logs:** Detailed logs for Automation Rules and Mortgage Overpayments.
- [x] **History Browser:** Session-based restoration of states.

### Phase 11: Visual Intelligence
- [x] **Automated Milestones:** Engine detection for Debt Freedom, RSU Vesting, and Insolvency Crossovers.
- [x] **Smart Layout:** Custom Chart.js plugin for non-overlapping, Gantt-style label placement below the axis.
- [x] **Comparison:** Comparative milestones (Ghost Labels) for Baseline vs Simulation.

### Phase 12: Simulation Control
- [x] **1.1 Save Simulation:** "Fork" a set of temporary overrides into a brand new permanent Scenario.

### Phase 13: Technical Debt & Refactoring (Initial)
- [x] **13.1 Engine Deconstruction:** Refactor the monolithic `engine.py` into isolated Processors.

### Phase 14: Deep Domain Logic (Decumulation)
- [x] **2.1 Owner Specifics:** DOB-driven logic for Pension Access Age (57+ rule).
- [x] **2.2 Decumulation Engine:** Strategies for "Standard" drawdown (GIA -> ISA -> Pension).
- [x] **2.3 Solver:** Iterative Newton-Raphson solver for calculating gross withdrawals net of tax.

---

## Upcoming Phases (Prioritized & Technical)

### Phase 15: Stability & Data Recovery (Mission 1)
*Immediate remediation of data ingest and legacy compatibility.*
- [ ] **15.1 Legacy Migration Adapter:** Implement an interceptor layer in the JSON Import flow to detect schema drift (missing `vesting_schedule`, `strategy` fields) and apply default sanitization before Pydantic validation.
- [ ] **15.2 Strict Schema Validation:** Replace `List[Dict[str, Any]]` in `ScenarioImport` with strict Pydantic models for nested entities (`owners`, `accounts`, etc.). This ensures API contracts are explicit and validation occurs at the boundary, returning 422s instead of 500s.
- [ ] **15.3 Transactional Integrity:** Implement a "Shadow Copy" strategy for imports. Write new scenario data to a staging area and verify complete success before swapping the active record pointer, preventing data loss on failed updates.

### Phase 16: The "Pence" Standard (Mission 3)
*Eliminating floating-point ambiguity across the stack.*
- [ ] **16.1 Audit & Standardization:** Identify all `int` -> `float` coercions.
- [ ] **16.2 Strict Types:** Introduce `Money = NewType('Money', int)` to enforce integer-only currency passing in Pydantic models.
- [ ] **16.3 Calculation Precision:** Refactor the Engine to use `decimal.Decimal` for all intermediate rate multiplications (Growth, Tax, Interest) before rounding back to Integer Pence.
- [ ] **16.4 API Consistency:** Ensure all API responses return Pence (Integers). Frontend becomes solely responsible for formatting to Pounds.
- [ ] **16.5 Logic Centralization:** Migrate business logic (e.g., Account Categorization "Liquid vs Illiquid", Rounding rules) from Frontend stores (`simulation.js`) to Backend computed properties or response fields. Ensure the Frontend is purely a view layer.

### Phase 17: Architectural Layering & Test Coverage (Mission 2)
*Decoupling the Engine from the Database to enable robust testing.*
- [ ] **17.1 Repository Pattern:** Introduce a Data Access Layer. The Engine should request `Domain Objects` (Pure Python dataclasses), not SQLAlchemy ORM objects.
- [ ] **17.2 Property-Based Testing:** Implement `Hypothesis` tests for the Calculation Engine. Define invariants (e.g., "Liquid Assets never imply debt without a loan") and fuzz-test the engine with generated edge cases.
- [ ] **17.3 DB Mocking:** Ensure Engine unit tests run without a DB session, improving test speed and isolation.

### Phase 18: The Tax Engine & Governance (Mission 4)
*Moving from Opaque Code to Transparent Configuration.*
- [ ] **18.1 Configuration over Code:** Extract hardcoded Tax Bands/Limits from `services/tax.py` into versioned JSON/YAML files (e.g., `tax_regime_2024_uk.json`).
- [ ] **18.2 Event-Sourced Tax Calculation:** Refactor the tax flow:
    1. **Emit:** Processors emit `TaxableEvent` objects (e.g., "Interest Received", "Salary Paid") during the monthly loop.
    2. **Aggregate:** A `TaxProcessor` consumes these events at the Fiscal Year boundary.
    3. **Resolve:** Calculate the final `TaxBill` based on the active Regime Configuration and deduct from cash.
- [ ] **18.3 Generic Wrappers:** Replace `Enum.ISA` with configurable `AccountBehavior` definitions (`growth_taxable: bool`, `contribution_limit_rule: str`).

### Phase 19: Probabilistic Modelling (Advanced Mode)
*Addressing uncertainty.*
- [ ] **19.1 Monte Carlo Simulation:** An optional "Toggle" mode to run thousands of simulations with variable market returns.
- [ ] **19.2 Confidence Intervals:** Visualizing the "Cone of Uncertainty" (e.g., 90% chance of solvency).

### Future Considerations
- [ ] **Auth:** Multi-user support.
- [ ] **Deployment:** Production Docker/Nginx/CI pipelines.