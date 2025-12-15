import { escapeAttr } from '../utils.js';

export function renderHelpView(container) {
    container.innerHTML = `
        <div class="help-layout">
            <aside class="help-sidebar">
                <div class="help-search-box">
                    <input type="text" id="help-search" placeholder="🔍 Search guide...">
                </div>
                <nav id="help-toc">
                    </nav>
            </aside>
            <main class="help-content" id="help-content">
                <h1>Aura Financial Handbook</h1>
                <p class="lead">A professional-grade personal wealth modelling system.</p>

                <section id="intro" data-title="Introduction">
                    <h2>1. Introduction</h2>
                    <p>Welcome to Aura. Unlike simple budgeting apps that track where your money <em>went</em>, Aura is a simulation engine that predicts where your money <em>will go</em>.</p>
                    <p>It models the complex interaction between your income, UK tax laws, asset growth, and liquidity to give you a realistic 10+ year forecast of your financial future.</p>
                </section>

                <section id="concepts" data-title="Core Concepts">
                    <h2>2. Core Concepts</h2>
                    <h3>🏘️ Scenarios</h3>
                    <p>A <strong>Scenario</strong> is a sandbox. You can create a "Primary" scenario that mirrors real life, and then duplicate it to create "What If" versions (e.g., <em>"What if I retire at 55?"</em>).</p>
                    <ul>
                        <li><strong>Owners:</strong> People in the scenario (e.g., You and your Partner). Assets and Income are linked to specific owners for tax calculations.</li>
                    </ul>

                    <h3>⏳ The Projection Engine</h3>
                    <p>When you click <strong>Update</strong>, Aura runs a month-by-month simulation. In every single month, it:</p>
                    <ol>
                        <li>Receives Income & deducts Tax/NI.</li>
                        <li>Pays bills (Costs).</li>
                        <li>Executes your <strong>Automation Rules</strong> (moving money).</li>
                        <li>Calculates Interest & Growth.</li>
                        <li>Checks for Tax Limits (ISA/Pension) and Capital Gains.</li>
                    </ol>
                </section>

                <section id="income" data-title="Income & Employment">
                    <h2>3. Income & Employment</h2>
                    <p>Aura includes a professional-grade UK Payroll engine.</p>

                    <h3>💵 Adding Salary</h3>
                    <p>Check the <strong>"Pre-Tax (Gross Income)"</strong> box.</p>
                    <ul>
                        <li><strong>Gross Amount:</strong> Enter your annual salary.</li>
                        <li><strong>The Engine:</strong> Will automatically deduct Income Tax (all bands) and Class 1 NI.</li>
                    </ul>

                    <h3>📉 Salary Sacrifice (Pension)</h3>
                    <p>If you contribute via Salary Sacrifice:</p>
                    <ul>
                        <li>Enter the <strong>Sacrifice Amount</strong> (Annual £).</li>
                        <li>Select your <strong>Pension Account</strong>.</li>
                        <li><strong>Result:</strong> Reduces Taxable Income (lowering tax) and moves money to Pension (tax-free).</li>
                    </ul>

                    <h3>🚗 Benefits in Kind (BiK)</h3>
                    <p>For non-cash benefits like Company Cars:</p>
                    <ul>
                        <li>Enter the <strong>Taxable Value</strong>.</li>
                        <li><strong>Result:</strong> Increases your "Taxable Income" for bracket calculations, but does <em>not</em> add cash to your balance.</li>
                    </ul>

                    <h3>🎁 Employer Contributions</h3>
                    <p>Use the <strong>Employer Pension Contribution</strong> field.</p>
                    <ul>
                        <li><strong>Result:</strong> Free money added to your Pension, completely tax-free. Does not affect your personal tax bands.</li>
                    </ul>
                </section>

                <section id="accounts" data-title="Accounts & Assets">
                    <h2>4. Accounts & Assets</h2>

                    <h3>🏦 Cash Accounts</h3>
                    <ul>
                        <li><strong>Interest:</strong> Earned monthly. Taxed via <strong>Personal Savings Allowance</strong> (PSA) unless in an ISA.</li>
                        <li><strong>Minimum Balance:</strong> A "Safety Floor" (e.g., £2,000). Automation rules will <em>never</em> pull money out below this level.</li>
                    </ul>

                    <h3>📈 Investments (GIA)</h3>
                    <p>General Investment Accounts are subject to <strong>Capital Gains Tax (CGT)</strong>.</p>
                    <ul>
                        <li><strong>Book Cost:</strong> Tracks the original purchase price (Section 104 Pool).</li>
                        <li><strong>Selling:</strong> The engine calculates "Realized Gain" and deducts CGT (18% or 24%) if you exceed the annual allowance.</li>
                    </ul>

                    <h3>🛡️ Tax Wrappers</h3>
                    <ul>
                        <li><strong>ISA:</strong> Tax-free growth/withdrawal. Capped at £20k/year.</li>
                        <li><strong>Pension:</strong> Tax-free growth. Contributions capped at £60k/year.</li>
                    </ul>

                    <h3>📜 RSU Grants</h3>
                    <p>Unvested equity (e.g., Tech grants).</p>
                    <ul>
                        <li><strong>Vesting:</strong> On vest date, units convert to cash, taxed as <strong>Income</strong>, and deposited to target.</li>
                    </ul>
                </section>

                <section id="limits" data-title="Tax Limits (Editable)">
                    <h2>5. Tax Limits (User Configurable)</h2>
                    <p>You can define custom Contribution Limits per scenario to model policy changes or personal caps.</p>

                    <h3>Configurable Logic</h3>
                    <ul>
                        <li><strong>Amount:</strong> Max inflow per tax year (e.g. £20,000).</li>
                        <li><strong>Wrappers:</strong> Applies to specific types (e.g. "ISA").</li>
                        <li><strong>Strictness:</strong> The engine applies the <em>strictest</em> matching limit. (e.g. If you have a £20k ISA limit and a £5k Cash-ISA limit, the Cash-ISA stops at £5k).</li>
                    </ul>

                    <h3>Safety Mechanisms</h3>
                    <p>If an automation rule tries to breach a limit:</p>
                    <ul>
                        <li><strong>Trimmed:</strong> Transfer is reduced to fill remaining allowance.</li>
                        <li><strong>Skipped:</strong> If full, the transfer doesn't happen.</li>
                        <li><strong>Warning:</strong> A yellow alert appears in the Projection Log.</li>
                    </ul>
                </section>

                <section id="automation" data-title="Automation Rules">
                    <h2>6. Automation Rules (The Brain)</h2>
                    <p>Rules run monthly after income and bills.</p>

                    <h3>🧹 Sweep ("Overflow")</h3>
                    <p><em>"If I have too much money, move it."</em></p>
                    <ul>
                        <li><strong>Logic:</strong> If Source > Trigger, move excess to Target.</li>
                    </ul>

                    <h3>🚰 Top-Up ("Rescue")</h3>
                    <p><em>"If I run out of money, fetch it."</em></p>
                    <ul>
                        <li><strong>Logic:</strong> If Target < Trigger, pull cash from Source to restore it.</li>
                    </ul>

                    <h3>🏠 Mortgage Smart Overpayment</h3>
                    <p><em>"Pay off debt efficiently."</em></p>
                    <ul>
                        <li>Calculates % of <strong>current</strong> balance at start of year.</li>
                        <li>Sets a smooth monthly payment.</li>
                        <li><strong>Smart:</strong> Skips if cash is low (Min Balance). Stops when mortgage is clear.</li>
                    </ul>
                </section>

                <section id="analysis" data-title="Analysis & Reports">
                    <h2>7. Analysis & Reports</h2>
                    
                    <h3>📊 Dashboard Scorecards</h3>
                    <ul>
                        <li><strong>Net Contributions (Active):</strong> Wealth from saving salary.</li>
                        <li><strong>Investment Growth (Passive):</strong> Wealth from returns/interest.</li>
                        <li><strong>Annual Return %:</strong> Your efficiency score. <br>🟢 > 2% (Beating Inflation). <br>🔴 < 2% (Losing Power).</li>
                    </ul>

                    <h3>🧾 Audit Logs</h3>
                    <ul>
                        <li><strong>Automation Audit:</strong> See exactly which rules fired and how much moved.</li>
                        <li><strong>Mortgage Report:</strong> Annual breakdown of overpayment targets vs actuals.</li>
                    </ul>
                </section>
            </main>
        </div>
    `;

    // --- Search & Navigation Logic ---
    const toc = document.getElementById('help-toc');
    const sections = document.querySelectorAll('.help-content section');
    const searchInput = document.getElementById('help-search');

    // Build ToC
    sections.forEach(sec => {
        const link = document.createElement('a');
        link.href = `#${sec.id}`;
        link.textContent = sec.dataset.title;
        link.onclick = (e) => {
            e.preventDefault();
            sec.scrollIntoView({ behavior: 'smooth' });
        };
        toc.appendChild(link);
    });

    // Search Filter
    searchInput.addEventListener('input', (e) => {
        const term = e.target.value.toLowerCase();
        
        sections.forEach(sec => {
            const text = sec.innerText.toLowerCase();
            const match = text.includes(term);
            sec.style.display = match ? 'block' : 'none';
            
            // Highlight logic could go here, but display toggling is cleaner for now
        });
    });
}
