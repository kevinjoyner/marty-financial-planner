# Marty: Personal Financial Planning & Simulation Engine

Marty is a deterministic financial simulation engine designed to model personal wealth trajectories with accounting-level precision. Unlike standard budgeting apps that track *past* spending, Marty projects *future* outcomes based on complex, interacting rules.

## Core Product Concept: Integrated Scenario Planning

Marty is built around a unified **Financial Simulation Environment** designed to support data-driven decision making.
- **The Dashboard (Current Reality):** Your defined financial state (Income, Accounts, Recurring Expenses, Tax Rules).
- **Modelling Bar (The What-If):** A non-destructive scratchpad on the right. You can "Pin" **any** variable (e.g., Salary, Mortgage Rate, ISA Limit, Inflation) to the bar and adjust it to see real-time impacts on your forecast.
- **Comparative Analysis:** Visualizes your "Baseline" (Current Reality) vs. "Projected" (Simulated Reality) simultaneously to show the delta of your decisions.
- **Timeline Intelligence:** Automated markers on the chart answer "When?" questions (e.g. "When will I be debt free?").

## Feature Specifications

### 1. The Simulation Engine
The core of Marty is a time-series projection engine.
- **Resolution:** Monthly steps.
- **Logic:** Deterministic flow (Income -> Tax -> Transfers -> Costs -> Growth -> Decumulation).
- **Simulation Mode:** The engine accepts temporary `overrides` (in-memory) to calculate hypothetical futures without altering the database.

### 2. Automated Decumulation & Safety Nets
Marty includes a sophisticated strategy engine for the "Exit" or "Retirement" phase of life.
- **Deficit Resolution:** If your liquid cash drops below a defined minimum (e.g., £0), the engine automatically triggers a "Sell" order to cover the shortfall.
- **Tax-Efficient Hierarchy:** Assets are sold in a specific order to minimise immediate tax liability:
    1.  **General Investments (GIA):** Sold first (subject to Capital Gains Tax).
    2.  **ISAs:** Sold second (Tax-free).
    3.  **Pensions:** Sold last (subject to Income Tax, only accessible if Age > 57).
- **Iterative Solver (Newton-Raphson):** Calculating the withdrawal amount is mathematically complex because withdrawals (especially from Pensions) are taxable, which reduces the net amount received, which requires a larger withdrawal, which increases the tax. Marty uses an **iterative numerical solver** to calculate the precise *Gross* withdrawal needed to satisfy the *Net* deficit to the penny.

### 3. Taxation Logic & Accounting
Marty models the UK tax regime to ensure projections are realistic.
- **Income Tax:** - The engine applies UK tax bands (Personal Allowance, Basic, Higher, Additional) to all taxable income streams.
    - **Hardcoded Values:** Currently, 2024/25 tax bands (e.g., £12,570 PA, £50,270 Basic Limit) are hardcoded in the service layer.
    - Future roadmap includes a fully editable Tax Regime UI.
- **National Insurance:** Class 1 NI is calculated on employment income.
- **Capital Gains Tax (CGT):** - The engine tracks the **Book Cost** vs **Current Value** of Investment Accounts.
    - When assets are sold (manually or via Decumulation), the engine calculates the realised gain and estimates the CGT liability based on your remaining Annual Exempt Amount.
- **Tax Wrappers:**
    - **ISA:** Growth and withdrawals are tax-free.
    - **Pension:** Contributions attract relief (logic planned), growth is tax-free, but withdrawals are taxed as income (25% tax-free lump sum logic is modeled via the UFPLS assumption in decumulation).
    - **GIA:** Fully taxable.

### 4. Financial Mechanics
* **Tax Limits:** Configurable limits for ISAs, Pensions, and LISAs to prevent over-contribution in simulations.
* **Accounts:**
    * **Liquid:** Cash, Current Accounts.
    * **Investments:** GIA, and tax-wrapped ISAs, LISAs and Pensions.
    * **Liabilities:** Mortgages (Amortization schedules, Overpayment logic, Fixed Rate periods).
    * **RSUs:** Unvested stock grants with specific vesting schedules.
* **Flows:**
    * **Transfers:** Automated movement between accounts.
    * **Waterfalls:** "Sweep" logic (e.g., "Move everything above £2k to Savings").
    * **Priorities:** Drag-and-drop ordering of automation rules.

### 5. Entity Management (The Drawers)
To maintain context, Marty uses a "Slide-over Drawer" pattern for editing.
- **Context:** Users remain on the main view (e.g., Accounts List).
- **Edit:** Clicking edit slides out a form panel with specialized logic.
- **Universal Pinning:** Every numerical, date, or boolean field (including Strategy Toggles) has a "Pin" toggle. Pinning moves that variable to the Modelling Bar for experimentation.
- **History:** A session-based Undo/Redo stack allows for safe experimentation with complex rule changes.

### 6. Visual Intelligence
Marty visualizes key moments in your financial future using a custom charting engine.
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
6.  **Rules (Automation):** Execute "Sweeps", "Top-ups", and "Smart Transfers".
7.  **Decumulation:** (New) Check for deficits and execute Strategy (Sell Assets) if required.
8.  **Mortgages:** Calculate interest, mandatory payments, and update amortisation.
9.  **Growth:** Apply interest/growth rates to remaining balances.
10. **Milestone Detection:** Check for state changes (e.g. Debt cleared).
11. **Snapshots:** Record end-of-month state.
