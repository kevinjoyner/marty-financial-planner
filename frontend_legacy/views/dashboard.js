import { ACCOUNT_TYPES, isAccountTypeLocked, formatCurrency, formatDate, escapeAttr } from '../utils.js';
import { renderTable, renderBreadcrumbs, initSortableTables } from './common.js';
import { renderProjectionComponent } from './projection.js';
import * as API from '../api.js';
import { lastProjectionData } from '../state.js';

export { renderProjectionComponent };

export function renderScenarioDashboard(contentRoot, scenarioData) {
    const section = document.getElementById('scenario-detail-section');
    let nav = section.querySelector('.nav-bar');
    if (!nav) {
        nav = document.createElement('nav');
        nav.className = 'nav-bar';
        const header = document.getElementById('scenario-detail-header');
        section.insertBefore(nav, header);
    }
    let breadcrumbsContainer = nav.querySelector('.breadcrumbs');
    if (!breadcrumbsContainer) {
        breadcrumbsContainer = document.createElement('div');
        breadcrumbsContainer.className = 'breadcrumbs';
        nav.appendChild(breadcrumbsContainer);
    }
    renderBreadcrumbs(breadcrumbsContainer, [
        { label: 'Home', path: '/' },
        { label: scenarioData.name, path: `/scenarios/${scenarioData.id}` }
    ]);

    const liquidAccs = scenarioData.accounts.filter(a => !isAccountTypeLocked(a.account_type, a.tax_wrapper) && a.account_type !== 'RSU Grant');
    const lockedAccs = scenarioData.accounts.filter(a => (isAccountTypeLocked(a.account_type, a.tax_wrapper) || a.account_type === 'RSU Grant'));

    const buildAccRows = (accounts) => accounts.map(a => {
        let balanceDisplay = formatCurrency(a.starting_balance, a.currency);
        if (a.account_type === 'RSU Grant' && a.unit_price) {
            const units = a.starting_balance / 100.0;
            const pricePence = a.unit_price;
            const totalValuePence = units * pricePence;
            balanceDisplay = formatCurrency(totalValuePence, a.currency);
        }
        return [
            `<a href="/scenarios/${scenarioData.id}/accounts/${a.id}" class="table-action-link">${escapeAttr(a.name)}</a>`,
            a.account_type === 'RSU Grant' ? 'RSU Grant' : a.account_type,
            balanceDisplay,
            `${a.interest_rate}%`,
            a.owners.map(o => escapeAttr(o.name)).join(', ')
        ];
    });
    
    const buildCostRows = (costs) => costs.map(c => [
        `<a href="/scenarios/${scenarioData.id}/costs/${c.id}" class="table-action-link">${escapeAttr(c.name)}</a>`,
        formatCurrency(c.value, c.currency),
        c.cadence,
        formatDate(c.start_date)
    ]);

    const buildEventRows = (events) => events.map(e => {
        let icon = '';
        if (e.event_type === 'transfer') icon = '<span title="Transfer" style="font-weight:bold; margin-right: 6px;">⇄</span>';
        else if (e.value >= 0) icon = '<span title="Income" style="font-weight:bold; margin-right: 6px;">↗</span>';
        else icon = '<span title="Expense" style="font-weight:bold; margin-right: 6px;">↘</span>';
        
        return [
            `${icon}<a href="/scenarios/${scenarioData.id}/financial_events/${e.id}" class="table-action-link">${escapeAttr(e.name)}</a>`,
            formatCurrency(e.value, e.currency),
            formatDate(e.event_date)
        ];
    });
    
    const buildTransferRows = (transfers) => transfers.map(t => {
        const fromAcc = scenarioData.accounts.find(a => a.id === t.from_account_id);
        const toAcc = scenarioData.accounts.find(a => a.id === t.to_account_id);
        return [
            `<a href="/scenarios/${scenarioData.id}/transfers/${t.id}" class="table-action-link">${escapeAttr(t.name)}</a>`,
            formatCurrency(t.value, t.currency),
            t.cadence,
            fromAcc ? escapeAttr(fromAcc.name) : 'Unknown',
            toAcc ? escapeAttr(toAcc.name) : 'Unknown'
        ];
    });

    const sortedRules = scenarioData.automation_rules.sort((a, b) => a.priority - b.priority);
    
    const buildRuleRows = (rules) => rules.map((r, i) => {
        const title = r.name || r.rule_type;
        let typeDisplay = r.rule_type.replace('_', ' ').toUpperCase();
        if (typeDisplay === 'MORTGAGE SMART') typeDisplay = 'SMART OVERPAY';
        return [
            `<span class="priority-index">${i + 1}</span><input type="hidden" class="rule-id" value="${r.id}">`,
            `<span style="font-size:0.85rem; font-weight:600; color:#555;">${typeDisplay}</span>`,
            `<a href="/scenarios/${scenarioData.id}/rules/${r.id}" class="table-action-link">${escapeAttr(title)}</a>`,
            r.cadence
        ];
    });

    const buildTaxRows = (limits) => limits.map(l => [
        `<a href="/scenarios/${scenarioData.id}/tax_limits/${l.id}" class="table-action-link" style="font-weight:500">${escapeAttr(l.name)}</a>`,
        formatCurrency(l.amount),
        l.wrappers.map(w => `<span class="badge" style="background:#e5e7eb; font-size:0.75rem; padding:2px 6px; border-radius:4px; margin-right:4px;">${w}</span>`).join('')
    ]);

    const renderRuleTable = (rules) => {
        if (!rules || rules.length === 0) return '<p style="color:#666; font-size:0.9rem;">No automation rules defined.</p>';
        
        const rows = buildRuleRows(rules).map((cols, idx) => 
            `<tr class="draggable-row" draggable="true" data-index="${idx}">
                ${cols.map(c => `<td>${c}</td>`).join('')}
            </tr>`
        ).join('');
        
        return `<table class="data-table" id="rules-table">
                    <thead><tr><th>Pri</th><th>Type</th><th>Title</th><th>Freq</th></tr></thead>
                    <tbody>${rows}</tbody>
                </table>
                <p style="font-size:0.8rem; color:#666; margin-top:5px;">Drag and drop rows to reorder priority.</p>`;
    };

    contentRoot.innerHTML = `
        <div id="dashboard-proj-root"></div>
        
        <div class="grid grid-2">
            <div>
                <div class="card">
                    <div class="section-header">
                        <h3>Net Liquid Assets</h3>
                        <a href="/scenarios/${scenarioData.id}/accounts/new" class="btn btn-sm btn-secondary">+ Add</a>
                    </div>
                    ${liquidAccs.length ? renderTable(['Name', 'Type', 'Balance', 'Growth', 'Owners'], buildAccRows(liquidAccs), 'liquid-acc-table') : '<p>No liquid accounts.</p>'}
                </div>
                <div class="card">
                    <div class="section-header">
                        <h3>Illiquid Assets</h3>
                        <a href="/scenarios/${scenarioData.id}/accounts/new" class="btn btn-sm btn-secondary">+ Add</a>
                    </div>
                    ${lockedAccs.length ? renderTable(['Name', 'Type', 'Value', 'Growth', 'Owners'], buildAccRows(lockedAccs), 'locked-acc-table') : '<p>No illiquid accounts.</p>'}
                </div>
                 <div class="card">
                    <div class="section-header">
                        <h3>Owners</h3>
                        <a href="/scenarios/${scenarioData.id}/owners/new" class="btn btn-sm btn-secondary">+ Add</a>
                    </div>
                    ${scenarioData.owners.length ? renderTable(['Name', 'Income Sources'], scenarioData.owners.map(o => [
                        `<a href="/scenarios/${scenarioData.id}/owners/${o.id}" class="table-action-link">${escapeAttr(o.name)}</a>`,
                        o.income_sources.length
                    ]), 'owners-table') : '<p>No owners.</p>'}
                </div>
            </div>
            <div>
                <div class="card" style="border-left: 4px solid #0891b2;">
                    <div class="section-header">
                        <h3>Tax Limits</h3>
                        <a href="/scenarios/${scenarioData.id}/tax_limits/new" class="btn btn-sm btn-secondary">+ Add</a>
                    </div>
                    ${(scenarioData.tax_limits && scenarioData.tax_limits.length) ? renderTable(['Name', 'Limit', 'Applies To'], buildTaxRows(scenarioData.tax_limits), 'tax-limits-table') : '<p style="color:#666;">No tax limits defined.</p>'}
                </div>

                <div class="card">
                    <div class="section-header">
                        <h3>Recurring Costs</h3>
                        <a href="/scenarios/${scenarioData.id}/costs/new" class="btn btn-sm btn-secondary">+ Add</a>
                    </div>
                    ${scenarioData.costs.length ? renderTable(['Name', 'Value', 'Frequency', 'Start'], buildCostRows(scenarioData.costs), 'costs-table') : '<p>No costs.</p>'}
                </div>
                
                <div class="card" style="border-left: 4px solid var(--primary-color);">
                    <div class="section-header">
                        <div style="display:flex; gap:10px; align-items:center;">
                            <h3 style="margin:0">Automation Rules</h3>
                        </div>
                        <div>
                             <button id="btn-audit-automation" class="btn btn-sm btn-secondary" title="Audit Log" style="margin-right:5px;">Audit</button>
                             <button id="btn-mortgage-report" class="btn btn-sm btn-secondary" title="View Overpayment Analysis" style="margin-right:5px;">Mortgage Report</button>
                             <a href="/scenarios/${scenarioData.id}/rules/new" class="btn btn-sm btn-secondary">+ Add Rule</a>
                        </div>
                    </div>
                    ${renderRuleTable(sortedRules)}
                </div>

                <div class="card">
                    <div class="section-header">
                        <h3>One-Time Events</h3>
                        <a href="/scenarios/${scenarioData.id}/financial_events/new" class="btn btn-sm btn-secondary">+ Add</a>
                    </div>
                     ${scenarioData.financial_events.length ? renderTable(['Name', 'Value', 'Date'], buildEventRows(scenarioData.financial_events), 'events-table') : '<p>No events.</p>'}
                </div>
                <div class="card">
                    <div class="section-header">
                        <h3>Transfers</h3>
                        <a href="/scenarios/${scenarioData.id}/transfers/new" class="btn btn-sm btn-secondary">+ Add</a>
                    </div>
                     ${scenarioData.transfers.length ? renderTable(['Name', 'Value', 'Frequency', 'From', 'To'], buildTransferRows(scenarioData.transfers), 'transfers-table') : '<p>No transfers.</p>'}
                </div>
            </div>
        </div>
    `;
    
    document.getElementById('btn-mortgage-report')?.addEventListener('click', () => {
        if (!lastProjectionData || !lastProjectionData.mortgage_stats || lastProjectionData.mortgage_stats.length === 0) {
            alert("No overpayment data available. Run a projection first.");
            return;
        }
        renderMortgageStatsModal(lastProjectionData.mortgage_stats);
    });

    document.getElementById('btn-audit-automation')?.addEventListener('click', () => {
        if (!lastProjectionData || !lastProjectionData.rule_logs || lastProjectionData.rule_logs.length === 0) {
            alert("No automation logs available. Run a projection first.");
            return;
        }
        renderAutomationAuditModal(lastProjectionData.rule_logs);
    });

    renderProjectionComponent(contentRoot.querySelector('#dashboard-proj-root'), false);
    initSortableTables(contentRoot);
    initDraggableRules(document.getElementById('rules-table'));
}

function initDraggableRules(table) {
    if (!table) return;
    const tbody = table.querySelector('tbody');
    let dragSrcEl = null;
    const rows = table.querySelectorAll('.draggable-row');
    rows.forEach(row => {
        row.addEventListener('dragstart', handleDragStart);
        row.addEventListener('dragenter', handleDragEnter);
        row.addEventListener('dragover', handleDragOver);
        row.addEventListener('dragleave', handleDragLeave);
        row.addEventListener('drop', handleDrop);
        row.addEventListener('dragend', handleDragEnd);
    });
    function handleDragStart(e) {
        dragSrcEl = this;
        e.dataTransfer.effectAllowed = 'move';
        e.dataTransfer.setData('text/html', this.innerHTML);
        this.classList.add('dragging');
    }
    function handleDragOver(e) {
        if (e.preventDefault) e.preventDefault();
        e.dataTransfer.dropEffect = 'move';
        return false;
    }
    function handleDragEnter(e) { this.classList.add('drag-over'); }
    function handleDragLeave(e) { this.classList.remove('drag-over'); }
    function handleDrop(e) {
        if (e.stopPropagation) e.stopPropagation();
        if (dragSrcEl !== this) {
            const allRows = Array.from(tbody.querySelectorAll('tr'));
            const srcIndex = allRows.indexOf(dragSrcEl);
            const targetIndex = allRows.indexOf(this);
            if (srcIndex < targetIndex) tbody.insertBefore(dragSrcEl, this.nextSibling);
            else tbody.insertBefore(dragSrcEl, this);
            updatePrioritiesAndSave();
        }
        return false;
    }
    function handleDragEnd(e) {
        this.classList.remove('dragging');
        rows.forEach(row => row.classList.remove('drag-over'));
    }
    async function updatePrioritiesAndSave() {
        const newRows = Array.from(tbody.querySelectorAll('tr'));
        const ids = [];
        newRows.forEach((row, index) => {
            const indexSpan = row.querySelector('.priority-index');
            if (indexSpan) indexSpan.textContent = index + 1;
            const idInput = row.querySelector('.rule-id');
            if (idInput) ids.push(parseInt(idInput.value));
        });
        try {
            await API.reorderRules(ids);
            setTimeout(() => { window.dispatchEvent(new Event('popstate')); }, 100);
        } catch (e) { console.error("Reorder failed", e); alert("Failed to save new order."); }
    }
}

function renderMortgageStatsModal(stats) {
    const modalOverlay = document.createElement('div');
    modalOverlay.className = 'modal-backdrop';
    stats.sort((a, b) => a.year_start - b.year_start);
    const rows = stats.map(s => {
        const isMaxed = s.headroom <= 0;
        const statusColor = isMaxed ? 'var(--success-color)' : '#d97706';
        const statusIcon = isMaxed ? '✅ Maxed' : '⚠️ Missed Target';
        return `<tr><td>${s.year_start} - ${s.year_start + 1}</td><td>${escapeAttr(s.rule_name)}</td><td>${formatCurrency(s.allowance * 100)}</td><td style="font-weight:bold;">${formatCurrency(s.paid * 100)}</td><td style="color:${statusColor}; font-weight:600;">${formatCurrency(s.headroom * 100)} <span style="font-size:0.8rem; margin-left:5px; color:#666;">${statusIcon}</span></td></tr>`;
    }).join('');
    modalOverlay.innerHTML = `<div class="modal" style="max-width: 700px;"><div class="modal-header"><h3>Mortgage Overpayment Analysis</h3><button class="modal-close">&times;</button></div><div class="modal-body"><p style="font-size:0.9rem; color:#666; margin-bottom:15px;">Annual breakdown of "Smart Smooth" rules. "Headroom" indicates the amount of allowance missed due to insufficient funds.</p><table class="data-table"><thead><tr><th>Year</th><th>Rule</th><th>Target Allowance</th><th>Actually Paid</th><th>Headroom (Missed)</th></tr></thead><tbody>${rows}</tbody></table></div></div>`;
    document.body.appendChild(modalOverlay);
    modalOverlay.querySelector('.modal-close').addEventListener('click', () => modalOverlay.remove());
    modalOverlay.addEventListener('click', (e) => { if (e.target === modalOverlay) modalOverlay.remove(); });
}

function renderAutomationAuditModal(logs) {
    const modalOverlay = document.createElement('div');
    modalOverlay.className = 'modal-backdrop';
    
    const summary = {};
    logs.forEach(log => {
        const key = `${log.rule_type}|${log.source_account}|${log.target_account}`;
        if (!summary[key]) summary[key] = { type: log.rule_type, source: log.source_account, target: log.target_account, count: 0, total: 0 };
        summary[key].count++;
        summary[key].total += log.amount;
    });
    const summaryRows = Object.values(summary).sort((a,b) => b.total - a.total).map(s => `
        <tr>
            <td><span class="badge">${s.type}</span></td>
            <td>${escapeAttr(s.source)} &rarr; ${escapeAttr(s.target)}</td>
            <td>${s.count}</td>
            <td style="font-weight:bold;">${formatCurrency(s.total * 100)}</td>
        </tr>
    `).join('');

    const timelineRows = logs.slice(0, 500).map(log => `
        <tr>
            <td>${log.date}</td>
            <td>${log.rule_type}</td>
            <td>${escapeAttr(log.source_account)} &rarr; ${escapeAttr(log.target_account)}</td>
            <td style="font-weight:bold;">${formatCurrency(log.amount * 100)}</td>
            <td style="font-size:0.8rem; color:#666;">${escapeAttr(log.reason)}</td>
        </tr>
    `).join('');

    modalOverlay.innerHTML = `
        <div class="modal" style="max-width: 900px;">
            <div class="modal-header">
                <h3>Automation Audit Log</h3>
                <button class="modal-close">&times;</button>
            </div>
            <div class="modal-body">
                <div class="tabs" style="display:flex; gap:10px; margin-bottom:15px; border-bottom:1px solid #eee;">
                    <button class="tab-btn active" data-tab="summary" style="padding:8px 15px; background:none; border:none; border-bottom:2px solid var(--primary-color); cursor:pointer; font-weight:600;">Summary</button>
                    <button class="tab-btn" data-tab="timeline" style="padding:8px 15px; background:none; border:none; cursor:pointer;">Timeline</button>
                    <button class="btn btn-sm btn-secondary" id="btn-audit-export" style="margin-left:auto;">Download CSV</button>
                </div>
                <div id="tab-summary" class="tab-content">
                    <table class="data-table"><thead><tr><th>Type</th><th>Flow Path</th><th>Executions</th><th>Total Moved</th></tr></thead><tbody>${summaryRows}</tbody></table>
                </div>
                <div id="tab-timeline" class="tab-content" style="display:none; max-height:400px; overflow-y:auto;">
                    <table class="data-table"><thead><tr><th>Date</th><th>Type</th><th>Flow</th><th>Amount</th><th>Reason / Trigger</th></tr></thead><tbody>${timelineRows}</tbody></table>
                </div>
            </div>
        </div>
    `;
    document.body.appendChild(modalOverlay);
    const tabs = modalOverlay.querySelectorAll('.tab-btn');
    tabs.forEach(btn => {
        btn.addEventListener('click', () => {
            tabs.forEach(t => { t.classList.remove('active'); t.style.borderBottom = 'none'; });
            btn.classList.add('active');
            btn.style.borderBottom = '2px solid var(--primary-color)';
            modalOverlay.querySelectorAll('.tab-content').forEach(c => c.style.display = 'none');
            document.getElementById(`tab-${btn.dataset.tab}`).style.display = 'block';
        });
    });
    document.getElementById('btn-audit-export').addEventListener('click', () => {
        const header = ['Date', 'Type', 'Source', 'Target', 'Amount', 'Reason'];
        const csvRows = [header.join(',')];
        logs.forEach(l => { csvRows.push([l.date, l.rule_type, `"${l.source_account}"`, `"${l.target_account}"`, l.amount.toFixed(2), `"${l.reason}"`].join(',')); });
        const blob = new Blob([csvRows.join("\n")], { type: 'text/csv' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `aura_automation_audit_${new Date().toISOString().slice(0,10)}.csv`;
        a.click();
    });
    modalOverlay.querySelector('.modal-close').addEventListener('click', () => modalOverlay.remove());
    modalOverlay.addEventListener('click', (e) => { if (e.target === modalOverlay) modalOverlay.remove(); });
}

export function renderHistoryModal(scenarioId) {
    API.fetchScenarioHistory(scenarioId).then(history => {
        const modalOverlay = document.createElement('div');
        modalOverlay.className = 'modal-backdrop';
        const rows = history.map(h => `<tr><td>${formatDate(h.timestamp)}</td><td>${escapeAttr(h.action_description)}</td><td><button class="btn btn-sm btn-secondary restore-btn" data-id="${h.id}">Restore</button></td></tr>`).join('');
        modalOverlay.innerHTML = `<div class="modal" style="max-width: 600px;"><div class="modal-header"><h3>Scenario History</h3><button class="modal-close">&times;</button></div><div class="modal-body">${history.length === 0 ? '<p>No history available.</p>' : `<table class="data-table"><thead><tr><th>Time</th><th>Action</th><th>Restore</th></tr></thead><tbody>${rows}</tbody></table>`}</div></div>`;
        document.body.appendChild(modalOverlay);
        modalOverlay.querySelector('.modal-close').addEventListener('click', () => modalOverlay.remove());
        modalOverlay.addEventListener('click', (e) => { if (e.target === modalOverlay) modalOverlay.remove(); });
        modalOverlay.querySelectorAll('.restore-btn').forEach(btn => {
            btn.addEventListener('click', async () => {
                if(!confirm("Are you sure? This will overwrite the current scenario state.")) return;
                try {
                    await API.restoreScenarioHistory(scenarioId, btn.dataset.id);
                    alert("Restored successfully!");
                    window.location.reload();
                } catch(e) { alert("Failed to restore."); }
            });
        });
    }).catch(e => { alert("Could not fetch history."); console.error(e); });
}

export function renderScenarioList(container, scenarios) {
    container.innerHTML = scenarios.map(s => `
        <li data-id="${s.id}">
            <div>
                <strong>${escapeAttr(s.name)}</strong><br>
                <small>${escapeAttr(s.description||'')}</small>
            </div>
            <button class="btn btn-danger btn-sm delete-btn">Delete</button>
        </li>
    `).join('');
}
