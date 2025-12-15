import { ACCOUNT_TYPES, isAccountTypeLocked, formatCurrency, formatDate, escapeAttr } from '../utils.js';
import * as API from '../api.js';
import * as Charts from '../charts.js';
import { globalState, currentScenarioData, lastProjectionData, setLastProjectionData } from '../state.js';

function getMonthDiff(d1, d2) {
    let months;
    months = (d2.getFullYear() - d1.getFullYear()) * 12;
    months -= d1.getMonth();
    months += d2.getMonth();
    return months <= 0 ? 0 : months;
}

function addMonths(date, months) {
    const d = new Date(date);
    d.setMonth(d.getMonth() + parseInt(months));
    return d;
}

export function renderProjectionComponent(container, isCompact = false, lockedAccountId = null) {
    const isChartLocked = lockedAccountId !== null;
    
    if (currentScenarioData) {
        const storageKey = `aura_chart_settings_${currentScenarioData.id}`;
        const savedSettings = localStorage.getItem(storageKey);
        let loaded = false;
        
        if (savedSettings) {
            try {
                const parsed = JSON.parse(savedSettings);
                if (parsed.years) globalState.years = parsed.years;
                if (parsed.mode) globalState.mode = parsed.mode;
                if (parsed.selectedAccounts && Array.isArray(parsed.selectedAccounts)) {
                    const currentIds = currentScenarioData.accounts.map(a => a.id);
                    const validIds = parsed.selectedAccounts.filter(id => currentIds.includes(id));
                    if (validIds.length > 0) {
                        globalState.selectedAccounts = validIds;
                        loaded = true;
                    }
                }
            } catch(e) { console.error("Failed to load chart settings", e); }
        }
        
        if (!loaded || globalState.selectedAccounts.length === 0) {
             if (isChartLocked) {
                 globalState.selectedAccounts = [lockedAccountId];
                 globalState.mode = 'split';
             } else {
                 const currentIds = currentScenarioData.accounts.map(a => a.id);
                 if (isCompact) {
                     globalState.selectedAccounts = currentIds;
                 } else {
                     const liquid = currentScenarioData.accounts.filter(a => !isAccountTypeLocked(a.account_type, a.tax_wrapper));
                     globalState.selectedAccounts = liquid.length > 0 ? liquid.map(a => a.id) : currentIds;
                 }
             }
        }
    }

    const startDate = new Date(currentScenarioData?.start_date || new Date());
    const currentYears = parseInt(globalState.years) || 10;
    const defaultTargetDate = addMonths(startDate, currentYears * 12).toISOString().split('T')[0];

    if (isCompact) {
        container.innerHTML = `
            <div class="card">
                <div id="projection-warnings-container"></div>
                <div class="projection-controls">
                    <h3>Projection</h3>
                    <div class="form-group">
                        <label>Target Date</label>
                        <input type="date" id="proj-target-date" value="${defaultTargetDate}">
                    </div>
                    <div class="form-group">
                        <label style="font-size: 0.9rem; font-weight:600; margin-bottom: 4px; display:block;">Accounts</label>
                        <div id="proj-accounts-container" style="max-height: 150px; overflow-y: auto; border: 1px solid #eee; padding: 5px; border-radius: 4px;"></div>
                    </div>
                    <div class="form-group">
                        <button id="run-projection-btn" class="btn btn-primary" style="width: 100%;">Update</button>
                    </div>
                </div>
                <div class="chart-container"><canvas id="projection-chart"></canvas></div>
            </div>`;
    } else {
        container.innerHTML = `
            <div id="projection-warnings-container"></div>
            
            <div class="dashboard-header">
                <div class="card" style="margin-bottom:0; height:100%">
                    <h3>Simulation</h3>
                    <div class="form-group">
                        <label>Target Date</label>
                        <div style="display:flex; gap:10px">
                            <input type="date" id="proj-target-date" value="${defaultTargetDate}">
                            <button id="run-projection-btn" class="btn btn-primary">Update</button>
                        </div>
                    </div>
                    <p style="font-size:0.85rem; color:#666; margin-top:10px;">Calculate projection until this date.</p>
                </div>
                <div id="metrics-container" class="metrics-grid" style="margin-bottom:0"></div>
            </div>

            <div class="card">
                <div class="chart-controls-bar">
                    <div style="display:flex; gap:15px; align-items:center;">
                        <h3 style="margin:0; margin-right:10px;">Projection Chart</h3>
                        <select id="proj-mode" class="chart-select">
                            <option value="aggregate" ${globalState.mode==='aggregate'?'selected':''}>Total Net Worth</option>
                            <option value="grouped" ${globalState.mode==='grouped'?'selected':''}>By Category</option>
                            <option value="split" ${globalState.mode==='split'?'selected':''}>By Account</option>
                        </select>
                        <button id="run-projection-btn-2" class="btn btn-sm btn-secondary" title="Update Chart">Update View</button>
                        <label style="font-size: 0.85rem; display: flex; align-items: center; gap: 5px; cursor:pointer;">
                            <input type="checkbox" id="freeze-axis" ${globalState.freezeAxis ? 'checked' : ''}> Freeze Axis
                        </label>
                    </div>
                    <div class="chart-tools">
                        <button id="dl-csv" class="btn btn-sm btn-secondary">Balances (CSV)</button>
                        <button id="dl-trans-csv" class="btn btn-sm btn-secondary">Transactions (CSV)</button>
                    </div>
                </div>

                <div class="grid layout-with-sidebar" style="grid-template-columns: 1fr 250px;">
                    <div class="chart-container">
                        <canvas id="projection-chart"></canvas>
                    </div>
                    <div>
                        <label style="font-weight:600; font-size:0.9rem; margin-bottom: 8px; display:block;">Visible Accounts</label>
                        <div id="proj-accounts-container" style="background:#f9fafb; padding:10px; border-radius:6px; border:1px solid #eee; max-height:400px; overflow-y:auto;"></div>
                    </div>
                </div>
            </div>
        `;
    }

    const runBtn = container.querySelector('#run-projection-btn');
    const runBtn2 = container.querySelector('#run-projection-btn-2');
    const dateInput = container.querySelector('#proj-target-date');
    const modeSel = container.querySelector('#proj-mode');
    const accContainer = container.querySelector('#proj-accounts-container');

    if (accContainer && currentScenarioData) {
        const liquidAccs = currentScenarioData.accounts.filter(a => !isAccountTypeLocked(a.account_type, a.tax_wrapper) && a.account_type !== 'RSU Grant');
        const illiquidAccs = currentScenarioData.accounts.filter(a => isAccountTypeLocked(a.account_type, a.tax_wrapper) && a.account_type !== 'RSU Grant');
        const rsuAccs = currentScenarioData.accounts.filter(a => a.account_type === 'RSU Grant');

        const renderGroup = (title, accounts) => {
            if (accounts.length === 0) return;
            const wrapper = document.createElement('div');
            wrapper.style.marginBottom = '12px';
            const header = document.createElement('div');
            header.style.cssText = "display: flex; justify-content: space-between; font-size: 0.8rem; font-weight: 600; color: #555; margin-bottom: 4px; border-bottom: 1px solid #eee; padding-bottom: 2px;";
            header.innerHTML = `<span>${title}</span> <a href="#" class="toggle-group" style="font-weight: normal; font-size: 0.75rem; color:var(--primary-color)">Toggle</a>`;
            wrapper.appendChild(header);

            const listDiv = document.createElement('div');
            listDiv.className = 'checkbox-list';
            listDiv.style.gridTemplateColumns = '1fr'; 
            
            accounts.forEach(acc => {
                const isChecked = globalState.selectedAccounts.includes(acc.id);
                const div = document.createElement('div');
                div.className = 'checkbox-group';
                div.innerHTML = `<input type="checkbox" value="${acc.id}" ${isChecked ? 'checked' : ''} id="chk-acc-${acc.id}"> <label for="chk-acc-${acc.id}" style="font-size:0.85rem">${escapeAttr(acc.name)}</label>`;
                listDiv.appendChild(div);
            });
            wrapper.appendChild(listDiv);
            accContainer.appendChild(wrapper);
            
            header.querySelector('.toggle-group').addEventListener('click', (e) => {
                e.preventDefault();
                const cbs = listDiv.querySelectorAll('input');
                const allChecked = Array.from(cbs).every(cb => cb.checked);
                cbs.forEach(cb => cb.checked = !allChecked);
                cbs[0].dispatchEvent(new Event('change', { bubbles: true }));
            });
        };
        
        renderGroup('Liquid Assets', liquidAccs);
        renderGroup('Illiquid Assets', illiquidAccs);
        renderGroup('RSU Grants', rsuAccs);

        accContainer.addEventListener('change', () => {
            const checked = Array.from(accContainer.querySelectorAll('input:checked')).map(cb => parseInt(cb.value));
            globalState.selectedAccounts = checked;
            if (!isCompact && currentScenarioData) {
                const settings = { years: globalState.years, mode: globalState.mode, selectedAccounts: checked };
                localStorage.setItem(`aura_chart_settings_${currentScenarioData.id}`, JSON.stringify(settings));
            }
        });
    }

    dateInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') runBtn.click();
    });

    const freezeChk = container.querySelector('#freeze-axis');
    if(freezeChk) freezeChk.addEventListener('change', (e) => {
        globalState.freezeAxis = e.target.checked;
        runBtn.click(); 
    });
    
    container.querySelector('#dl-csv')?.addEventListener('click', () => {
        if(lastProjectionData) Charts.exportChartDataToCSV(lastProjectionData, globalState.selectedAccounts, currentScenarioData);
    });
    container.querySelector('#dl-trans-csv')?.addEventListener('click', () => {
        if(lastProjectionData) Charts.exportTransactionReportToCSV(lastProjectionData, currentScenarioData);
    });

    const runLogic = async () => {
        const target = new Date(dateInput.value);
        const start = new Date(currentScenarioData.start_date);
        const months = getMonthDiff(start, target);

        if (months <= 0) {
            alert("Target date must be after start date.");
            return;
        }
        
        globalState.years = Math.ceil(months / 12); 
        if(modeSel) globalState.mode = modeSel.value;
        
        let checked = [];
        if (accContainer) {
            checked = Array.from(accContainer.querySelectorAll('input:checked')).map(cb => parseInt(cb.value));
        } else {
            checked = globalState.selectedAccounts;
        }
        
        globalState.selectedAccounts = checked;

        if (checked.length === 0) return alert("Select at least one account.");
        
        if (!isCompact && currentScenarioData) {
            const settings = { years: globalState.years, mode: globalState.mode, selectedAccounts: globalState.selectedAccounts };
            localStorage.setItem(`aura_chart_settings_${currentScenarioData.id}`, JSON.stringify(settings));
        }

        runBtn.textContent = 'Running...';
        if(runBtn2) runBtn2.textContent = '...';
        try {
            const data = await API.runProjection(currentScenarioData.id, months);
            setLastProjectionData(data);
            
            if(!isCompact) updateMetrics(data);
            renderWarnings(container, data.warnings);

            Charts.renderProjectionChart('projection-chart', data, globalState.mode, checked, currentScenarioData, globalState);
        } catch (e) { console.error(e); }
        runBtn.textContent = 'Update';
        if(runBtn2) runBtn2.textContent = 'Update View';
    };

    runBtn.addEventListener('click', runLogic);
    if(runBtn2) runBtn2.addEventListener('click', runLogic);

    setTimeout(runLogic, 0);
}

function updateMetrics(data) {
    const metricsContainer = document.getElementById('metrics-container');
    if (!metricsContainer) return;
    
    const rsuIds = currentScenarioData.accounts
        .filter(a => a.account_type === 'RSU Grant')
        .map(a => a.id);
        
    const calculateTotalExcludingRSU = (dp) => {
        let sum = 0;
        Object.keys(dp.account_balances).forEach(accIdStr => {
            const accId = parseInt(accIdStr);
            if (!rsuIds.includes(accId)) {
                sum += dp.account_balances[accIdStr];
            }
        });
        return sum;
    };

    const startBal = calculateTotalExcludingRSU(data.data_points[0]);
    const endBal = calculateTotalExcludingRSU(data.data_points[data.data_points.length - 1]);
    const totalGrowth = endBal - startBal;
    
    const months = data.data_points.length;
    const years = Math.round(months / 12);

    let activeSavings = 0;
    
    data.data_points.forEach(dp => {
         Object.values(dp.flows).forEach(f => {
             activeSavings += f.income;
             activeSavings += f.employer_contribution || 0;
             activeSavings -= f.costs;
             activeSavings -= f.tax; 
             activeSavings -= f.cgt; 
             activeSavings += f.events;
         });
    });
    
    const passiveGrowth = totalGrowth - activeSavings;

    const investedCapital = startBal + activeSavings;
    let annualReturnPct = 0;
    
    // Simplified Modified Dietz: Return / (Start + 0.5 * Flows)
    const averageCapital = startBal + (0.5 * activeSavings);
    
    if (averageCapital > 0 && years > 0) {
        const totalRoi = passiveGrowth / averageCapital;
        // Simple Annualization: TotalROI / Years
        // Compound Annualization: (1 + TotalROI)^(1/Years) - 1
        // Let's use Compound for accuracy
        annualReturnPct = (Math.pow(1 + totalRoi, 1 / years) - 1) * 100;
    }
    
    const returnColor = annualReturnPct >= 2.0 ? 'var(--success-color)' : 'var(--danger-color)';
    const passiveColor = passiveGrowth >= 0 ? 'var(--success-color)' : 'var(--danger-color)';

    metricsContainer.innerHTML = `
        <div class="metric-card">
            <h4>Current Net Worth</h4>
            <div class="value">${formatCurrency(startBal * 100)}</div>
            <div class="subtext" style="color:#666; font-size:0.75rem;">(Excl. Unvested RSUs)</div>
        </div>
        <div class="metric-card">
            <h4>Projected Net Worth</h4>
            <div class="value">${formatCurrency(endBal * 100)}</div>
            <div class="subtext">in ${years} years</div>
        </div>
        <div class="metric-card">
            <h4>Net Contributions</h4>
            <div class="value" style="color: var(--primary-color)">${formatCurrency(activeSavings * 100)}</div>
            <div class="subtext">Active Savings</div>
        </div>
        <div class="metric-card">
            <h4>Investment Growth</h4>
            <div class="value" style="color: ${passiveColor}">${passiveGrowth >= 0 ? '+' : ''}${formatCurrency(passiveGrowth * 100)}</div>
            <div class="subtext">Passive Return</div>
        </div>
        <div class="metric-card">
            <h4>Annual Return (Est.)</h4>
            <div class="value" style="color: ${returnColor}">${annualReturnPct.toFixed(2)}%</div>
            <div class="subtext">Target: >2.0%</div>
        </div>
    `;
}

function renderWarnings(container, warnings) {
    const warnContainer = container.querySelector('#projection-warnings-container');
    if (!warnContainer) return;
    if (!warnings || warnings.length === 0) {
        warnContainer.innerHTML = '';
        return;
    }
    warnContainer.innerHTML = `
        <div class="warning-banner">
            <h4>⚠️ Scenario Alerts</h4>
            <ul>
                ${warnings.map(w => `<li>${w.date}: ${w.message}</li>`).join('')}
            </ul>
        </div>
    `;
}
