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

### Phase 13: Technical Debt & Refactoring
- [x] **13.1 Engine Deconstruction:** Refactor the monolithic `engine.py` into isolated Processors (e.g., `IncomeProcessor`, `MortgageProcessor`, `TaxProcessor`) to allow for unit testing and safe extension.

### Phase 14: Deep Domain Logic (Decumulation)
*Refining the financial engine fidelity and lifecycle planning.*
- [x] **2.1 Owner Specifics:** DOB-driven logic for Pension Access Age (57+ rule).
- [x] **2.2 Decumulation Engine:** Strategies for "Standard" drawdown (GIA -> ISA -> Pension).
- [x] **2.3 Solver:** Iterative Newton-Raphson solver for calculating gross withdrawals net of tax.

---

## Upcoming Phases (Prioritized)

### 1. Phase 16: Governance & Insight
*Making the "Black Box" transparent and strategic.*
- [ ] **5.1 Tax Regime Transparency:** UI for viewing and editing Tax Bands, Rates, and Limits (moving hardcoded logic to editable data).
- [ ] **5.2 Strategy Audit Report:** A narrative report explaining *how* the scenario is optimizing tax (e.g., "Utilizing 100% of ISA allowance to save £X in future tax").

### 2. Phase 13 (Continued): Technical Debt
- [ ] **13.2 Type Safety:** Stricter Pydantic/Typing enforcement across the calculation layer to prevent floating-point/integer errors.

### 3. Phase 12b: Probabilistic Modelling (Advanced Mode)
*Addressing uncertainty.*
- [ ] **1.2 Monte Carlo Simulation:** An optional "Toggle" mode to run thousands of simulations with variable market returns.
- [ ] **1.3 Confidence Intervals:** Visualizing the "Cone of Uncertainty" (e.g., 90% chance of solvency) rather than a single deterministic line.

### 4. Phase 15: Platform Maturity
- [ ] **4.1 Authentication:** Multi-user support (Login/Sign-up).

### Future Considerations (Low Priority)
- [ ] **3.1 Mobile Responsiveness:** Adapting the Sidebar/Modelling layout for phones/tablets.
- [ ] **4.2 Deployment:** Production Docker Compose, Nginx proxy, CI/CD pipeline.
