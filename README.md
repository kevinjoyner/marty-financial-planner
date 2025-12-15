# Aura: Personal Financial Simulation Cockpit

Aura is a deterministic financial simulation engine designed to model personal wealth trajectories with accounting-level precision. Unlike standard budgeting apps that track *past* spending, Aura projects *future* outcomes based on complex, interacting rules.

## Core Product Concept: "The Cockpit"

Aura is built around the concept of a **Financial Cockpit**. 
- **Center Stage (The Reality):** Your defined financial state (Income, Accounts, Recurring Expenses, Tax Rules).
- **Modelling Bar (The What-If):** A non-destructive scratchpad on the right. You can "Pin" **any** variable (e.g., Salary, Mortgage Rate, ISA Limit, Inflation) to the bar and adjust it to see real-time impacts.
- **Ghost Charting:** Visualizes your "Baseline" (Current Reality) vs. "Projected" (Simulated Reality) simultaneously to show the delta of your decisions.
- **Timeline Intelligence:** Automated markers on the chart answer "When?" questions (e.g. "When will I be debt free?").

## Feature Specifications

### 1. The Simulation Engine
The core of Aura is a time-series projection engine.
- **Resolution:** Monthly steps.
- **Logic:** Deterministic flow (Income -> Tax -> Transfers -> Costs -> Growth).
- **Simulation Mode:** The engine accepts temporary `overrides` (in-memory) to calculate hypothetical futures without altering the database.

### 2. Financial Mechanics
* **Income:** Supports Salary, Bonuses, Dividends. Handles Pre-tax vs Post-tax logic.
* **Taxation:** UK Tax Logic (Income Tax Bands, National Insurance, Capital Gains Tax).
* **Tax Limits:** Configurable limits for ISAs, Pensions, and LISAs.
* **Accounts:**
    * **Liquid:** Cash, Current Accounts.
    * **Investments:** GIA, ISA (Tax wrappers applied).
    * **Liabilities:** Mortgages (Amortization schedules, Overpayment logic, Fixed Rate periods).
    * **RSUs:** Unvested stock grants with specific vesting schedules.
* **Flows:**
    * **Transfers:** Automated movement between accounts.
    * **Waterfalls:** "Sweep" logic (e.g., "Move everything above £2k to Savings").
    * **Priorities:** Drag-and-drop ordering of automation rules.

### 3. Entity Management (The Drawers)
To maintain context, Aura uses a "Slide-over Drawer" pattern for editing.
- **Context:** Users remain on the main view (e.g., Accounts List).
- **Edit:** Clicking edit slides out a form panel with specialized logic (e.g., Mortgage Calculators).
- **Universal Pinning:** Every numerical or date field has a "Pin" toggle. Pinning moves that variable to the Modelling Bar for experimentation.
- **History:** A session-based Undo/Redo stack allows for safe experimentation with complex rule changes.

### 4. Visual Intelligence
Aura visualizes key moments in your financial future using a custom charting engine.
- **Automated Milestones:** The engine detects state changes and generates markers for:
    - **Debt Freedom:** The month a mortgage balance hits zero.
    - **Liquidity Crossover:** The month Liquid Assets exceed Total Liabilities.
    - **Vesting Events:** When RSU grants fully vest.
- **Transaction Markers:** High-impact events (e.g., "House Purchase") can be toggled to appear on the chart.
- **Gantt-Style Layout:** A custom Chart.js plugin manages label placement below the horizontal axis, using collision detection to create non-overlapping "lanes" for high-density timelines.

## Calculation Logic (Engine)

The engine runs a sequential processing loop for `N` months:
1.  **Date Step:** Increment month.
2.  **Income:** Process salary, RSUs (Vesting). Calculate Tax/NI.
3.  **Costs:** Deduct living expenses.
4.  **Transfers (Pre-Logic):** Scheduled standing orders.
5.  **Events:** One-off financial events (e.g., "Buy Car").
6.  **Rules (Automation):** Execute "Sweeps", "Top-ups", and "Smart Transfers" in user-defined priority order.
7.  **Mortgages:** Calculate interest, mandatory payments, and update amortisation.
8.  **Growth:** Apply interest/growth rates to remaining balances.
9.  **Milestone Detection:** Check for state changes (e.g. Debt cleared).
10. **Snapshots:** Record end-of-month state.
