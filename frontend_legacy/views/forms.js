import { ACCOUNT_TYPES, formatCurrency, calculatePMT, calculateRemainingBalance, escapeAttr, formatDate } from '../utils.js';
import { renderBreadcrumbs } from './common.js';
import { renderProjectionComponent } from './projection.js';
import * as API from '../api.js';

async function handleFormSubmit(btn, actionPromise, callback) {
    const originalText = btn.textContent;
    try {
        await actionPromise();
        btn.classList.remove('btn-pulse');
        void btn.offsetWidth; 
        btn.classList.add('btn-pulse');
        btn.textContent = 'Saved!';
        setTimeout(() => { 
            btn.textContent = originalText;
            btn.classList.remove('btn-pulse'); 
        }, 1000);
        if (callback) callback();
    } catch (e) {
        console.error(e);
        alert("Failed to save. Check inputs.");
        btn.textContent = originalText;
    }
}

export function renderFormWithSidebar(breadcrumbs, title, formHtml, initFormCallback, lockedAccountId = null) {
    const contentRoot = document.getElementById('scenario-content-root');
    const header = document.getElementById('scenario-detail-header');
    if (header) { const existingActions = header.querySelector('.header-actions'); if (existingActions) existingActions.remove(); }
    const section = document.getElementById('scenario-detail-section');
    let nav = section.querySelector('.nav-bar');
    if (!nav) { nav = document.createElement('nav'); nav.className = 'nav-bar'; section.insertBefore(nav, header); }
    let container = nav.querySelector('.breadcrumbs');
    if (!container) { container = document.createElement('div'); container.className = 'breadcrumbs'; nav.appendChild(container); }
    renderBreadcrumbs(container, breadcrumbs);
    contentRoot.innerHTML = `<div class="layout-with-sidebar"><div><div class="card"><h3>${title}</h3>${formHtml}</div><div id="extra-content-root"></div></div><div class="compact-projection" id="sidebar-proj-root"></div></div>`;
    renderProjectionComponent(contentRoot.querySelector('#sidebar-proj-root'), true, lockedAccountId);
    if(initFormCallback) initFormCallback();
}

function getSortedAccountOptions(accounts, selectedId) {
    return accounts
        .slice()
        .sort((a, b) => a.name.localeCompare(b.name))
        .map(a => `<option value="${a.id}" ${selectedId === a.id ? 'selected' : ''}>${escapeAttr(a.name)}</option>`)
        .join('');
}

export function renderAccountForm(contentRoot, id, scenarioData, isNew) {
    const acc = isNew ? {} : scenarioData.accounts.find(a => a.id == id);
    if(!isNew && !acc) return contentRoot.innerHTML = '<p>Not found</p>';
    const crumbs = [{ label: 'Home', path: '/' }, { label: scenarioData.name, path: `/scenarios/${scenarioData.id}` }];
    crumbs.push({ label: isNew ? 'Create Account' : acc.name, path: '#' });

    const TAX_WRAPPERS = ["None", "ISA", "Lifetime ISA", "Pension", "Junior ISA"];
    const vestingSchedule = acc.vesting_schedule || [];
    
    const generateVestingRow = (year = '', percent = '') => `
        <div class="vesting-row" style="display: flex; gap: 10px; margin-bottom: 8px; align-items: center;">
            <input type="number" name="vest_year[]" placeholder="Year" value="${year}" style="flex: 0.5;" min="1" required>
            <input type="number" name="vest_percent[]" placeholder="%" value="${percent}" style="flex: 1;" min="0" max="100" step="0.1" required>
            <button type="button" class="btn btn-danger btn-sm remove-vest-btn">x</button>
        </div>
    `;

    const bookCostVal = acc.book_cost !== undefined && acc.book_cost !== null ? Math.abs(acc.book_cost/100) : '';
    // NEW: Min Balance Logic
    const minBalVal = acc.min_balance !== undefined && acc.min_balance !== null ? Math.abs(acc.min_balance/100) : '';
    
    const paymentAccountOptions = getSortedAccountOptions(scenarioData.accounts, acc.payment_from_account_id);
    const rsuTargetOptions = getSortedAccountOptions(scenarioData.accounts.filter(a => a.account_type !== 'RSU Grant'), acc.rsu_target_account_id);

    const formHtml = `
        <form id="acc-form">
            <div class="form-group"><label>Name</label><input name="name" value="${escapeAttr(acc.name||'')}" required></div>
            <div class="grid grid-2">
                <div class="form-group"><label>Asset Type</label>
                    <select name="account_type" id="acc-type">${ACCOUNT_TYPES.map(t => `<option value="${t}" ${acc.account_type===t?'selected':''}>${t}</option>`).join('')}</select>
                </div>
                <div class="form-group" id="tax-wrapper-group"><label>Tax Wrapper</label>
                    <select name="tax_wrapper">${TAX_WRAPPERS.map(t => `<option value="${t}" ${acc.tax_wrapper===t?'selected':''}>${t}</option>`).join('')}</select>
                </div>
            </div>
            <div class="form-group"><label>Owners</label><div class="checkbox-list">${scenarioData.owners.map(o => `<div class="checkbox-group"><input type="checkbox" name="owner_ids" value="${o.id}" id="o${o.id}" ${acc.owners && acc.owners.some(x=>x.id===o.id)?'checked':''}> <label for="o${o.id}">${escapeAttr(o.name)}</label></div>`).join('')}</div></div>
            <div class="form-group"><label>Currency</label><select name="currency"><option value="GBP" ${acc.currency==='GBP'?'selected':''}>GBP</option><option value="USD" ${acc.currency==='USD'?'selected':''}>USD</option></select></div>
            
            <div class="grid grid-2">
                <div class="form-group"><label id="bal-label">Balance</label><input type="number" step="0.01" name="starting_balance" value="${acc.starting_balance !== undefined ? Math.abs(acc.starting_balance/100) : ''}" required></div>
                <div class="form-group" id="min-bal-group"><label>Minimum Balance</label><input type="number" step="0.01" name="min_balance" value="${minBalVal}"><small>Automation floor (e.g. Overdraft buffer)</small></div>
            </div>
            <div class="form-group" id="book-cost-group"><label>Book Cost (Capital)</label><input type="number" step="0.01" name="book_cost" value="${bookCostVal}"><small>Cost basis for CGT</small></div>
            
            <div id="std-interest" class="form-group"><label id="rate-label">Interest/Growth Rate %</label><input type="number" step="0.01" id="std-interest-input" name="interest_rate" value="${acc.interest_rate||0}" required></div>
            
            <div id="rsu-fields" class="hidden">
                <hr style="margin: 20px 0; border-top: 1px solid #eee;"><h4>RSU Configuration</h4>
                <div class="form-group"><label>Grant Start Date</label><input type="date" name="grant_date" value="${acc.grant_date||''}"></div>
                <div class="form-group"><label>Grant Price per Unit</label><input type="number" step="0.01" name="unit_price" value="${acc.unit_price ? acc.unit_price/100 : ''}"></div>
                <div class="form-group"><label>Target Account</label><select name="rsu_target_account_id"><option value="">-- Select --</option>${rsuTargetOptions}</select></div>
                <div class="form-group"><label>Vesting Schedule</label><div id="vesting-container" style="background: #f9fafb; padding: 10px; border: 1px solid #e5e7eb; border-radius: 6px;"><div id="vesting-rows">${vestingSchedule.length > 0 ? vestingSchedule.map(v => generateVestingRow(v.year, v.percent)).join('') : generateVestingRow(1, 25)}</div><button type="button" id="add-vest-btn" class="btn btn-secondary btn-sm" style="margin-top: 10px;">+ Add Year</button></div></div>
            </div>
            
            <div id="mortgage-fields" class="${(acc.account_type==='Mortgage' || acc.account_type==='Property')?'':'hidden'}">
                <hr style="margin: 20px 0; border-top: 1px solid #eee;">
                <h4 id="mortgage-header">${acc.account_type==='Property'?'Property Details':'Mortgage Details'}</h4>
                
                <div id="mortgage-preview-box" class="card ${acc.account_type==='Mortgage'?'':'hidden'}" style="background: #f0f9ff; border-color: #bae6fd;">
                    <p id="mortgage-summary" style="margin:0;color:#0c4a6e;font-size:0.9rem;">Enter details to preview payments...</p>
                </div>

                <div class="form-group">
                    <label id="start-date-label">${acc.account_type==='Property'?'Purchase Date':'Start Date'}</label>
                    <input type="date" id="m-start" name="mortgage_start_date" value="${acc.mortgage_start_date||''}">
                </div>
                
                <div id="mortgage-specifics" class="${acc.account_type==='Mortgage'?'':'hidden'}">
                    <div class="form-group"><label>Original Loan Amount</label><input type="number" step="0.01" id="m-amount" name="original_loan_amount" value="${acc.original_loan_amount !== undefined && acc.original_loan_amount !== null ? acc.original_loan_amount/100 : ''}"></div>
                    <div class="form-group"><label>Term (Years)</label><input type="number" id="m-term" name="amortisation_period_years" value="${acc.amortisation_period_years||''}"></div>
                    <div class="grid grid-2">
                        <div class="form-group"><label>Fixed Years</label><input type="number" id="m-fixed-years" name="fixed_rate_period_years" value="${acc.fixed_rate_period_years||''}"></div>
                        <div class="form-group"><label>Fixed Rate %</label><input type="number" step="0.01" id="m-fixed-rate" name="fixed_interest_rate" value="${acc.fixed_interest_rate||''}"></div>
                    </div>
                    <div class="form-group"><label>Pay From Account</label><select name="payment_from_account_id">${paymentAccountOptions}</select></div>
                </div>
            </div>

            <div class="form-group"><label>Notes</label><textarea name="notes" style="width:100%; height:80px; border:1px solid #e5e7eb; border-radius:6px; padding:8px;">${escapeAttr(acc.notes||'')}</textarea></div>
            <div class="form-actions" style="margin-top: 20px; display: flex; gap: 10px; align-items: center;"><button type="submit" class="btn btn-primary">${isNew?'Create':'Save'}</button>${!isNew ? '<button type="button" id="del-btn" class="btn btn-danger">Delete</button>' : ''}</div>
        </form>`;
    
    renderFormWithSidebar(crumbs, isNew ? 'Create Account' : `Edit: ${acc.name}`, formHtml, () => {
        const typeSel = document.getElementById('acc-type');
        const updateVisibility = () => {
            const val = typeSel.value;
            const mortDiv = document.getElementById('mortgage-fields');
            const rsuDiv = document.getElementById('rsu-fields');
            const taxDiv = document.getElementById('tax-wrapper-group');
            const mortSpec = document.getElementById('mortgage-specifics');
            const mortPreview = document.getElementById('mortgage-preview-box');
            const bookCostGroup = document.getElementById('book-cost-group');
            const minBalGroup = document.getElementById('min-bal-group');
            
            mortDiv.classList.add('hidden');
            rsuDiv.classList.add('hidden');
            taxDiv.style.display = 'block';
            bookCostGroup.style.display = 'block'; 
            minBalGroup.style.display = 'block';
            document.getElementById('bal-label').textContent = "Balance";
            document.getElementById('rate-label').textContent = "Interest/Growth Rate %";
            
            if (val === 'Mortgage') {
                mortDiv.classList.remove('hidden');
                mortSpec.classList.remove('hidden');
                mortPreview.classList.remove('hidden');
                taxDiv.style.display = 'none';
                bookCostGroup.style.display = 'none'; 
                minBalGroup.style.display = 'none'; // Min Bal irrelevant for Mortgage
                document.getElementById('mortgage-header').textContent = "Mortgage Details";
                document.getElementById('start-date-label').textContent = "Start Date";
                document.getElementById('rate-label').textContent = "Variable / Follow-on Rate %";
            } else if (val === 'Property') {
                mortDiv.classList.remove('hidden');
                mortSpec.classList.add('hidden'); 
                mortPreview.classList.add('hidden');
                minBalGroup.style.display = 'none';
                document.getElementById('mortgage-header').textContent = "Property Details";
                document.getElementById('start-date-label').textContent = "Purchase Date";
            } else if (val === 'RSU Grant') {
                rsuDiv.classList.remove('hidden');
                taxDiv.style.display = 'none';
                bookCostGroup.style.display = 'none'; 
                minBalGroup.style.display = 'none';
                document.getElementById('bal-label').textContent = "Number of Units";
                document.getElementById('rate-label').textContent = "Stock Growth Rate %";
            }
        };
        typeSel.addEventListener('change', updateVisibility);
        updateVisibility();

        const rowsDiv = document.getElementById('vesting-rows');
        if(rowsDiv) {
            document.getElementById('add-vest-btn').onclick = () => {
                const inputs = rowsDiv.querySelectorAll('input[name="vest_year[]"]');
                let nextYear = 1;
                if(inputs.length > 0) nextYear = parseInt(inputs[inputs.length-1].value) + 1;
                const div = document.createElement('div');
                div.innerHTML = generateVestingRow(nextYear, '');
                rowsDiv.appendChild(div.firstElementChild);
            };
            rowsDiv.addEventListener('click', (e) => { if (e.target.classList.contains('remove-vest-btn')) e.target.closest('.vesting-row').remove(); });
        }

        const updateMortgagePreview = () => {
            if (typeSel.value !== 'Mortgage') return;
            const amount = parseFloat(document.getElementById('m-amount').value) * 100;
            const term = parseInt(document.getElementById('m-term').value);
            const varRate = parseFloat(document.getElementById('std-interest-input').value);
            const fixRate = parseFloat(document.getElementById('m-fixed-rate').value);
            const fixYears = parseInt(document.getElementById('m-fixed-years').value) || 0;
            const summaryDiv = document.getElementById('mortgage-summary');
            if (!amount || !term) { summaryDiv.textContent = "Enter amount and term to preview."; return; }
            let html = `<strong>Estimated Payments:</strong><br>`;
            if (fixYears > 0 && !isNaN(fixRate)) {
                const fixPmt = calculatePMT(amount, fixRate, term);
                html += `Fixed (${fixYears} yrs @ ${fixRate}%): <strong>${formatCurrency(fixPmt)}/mo</strong><br>`;
                const balAfter = calculateRemainingBalance(amount, fixRate, term, fixYears);
                const remainingTerm = term - fixYears;
                if (remainingTerm > 0) {
                    const varPmt = calculatePMT(balAfter, varRate, remainingTerm);
                    html += `Follow-on (${remainingTerm} yrs @ ${varRate}%): <strong>${formatCurrency(varPmt)}/mo</strong>`;
                }
            } else {
                const pmt = calculatePMT(amount, varRate, term);
                html += `Standard (${term} yrs @ ${varRate}%): <strong>${formatCurrency(pmt)}/mo</strong>`;
            }
            summaryDiv.innerHTML = html;
        };
        ['m-amount', 'm-term', 'std-interest-input', 'm-fixed-rate', 'm-fixed-years'].forEach(id => {
            const el = document.getElementById(id);
            if(el) el.addEventListener('input', updateMortgagePreview);
        });
        updateMortgagePreview();
        
        const form = document.getElementById('acc-form');
        form.addEventListener('submit', async e => {
            e.preventDefault();
            const fd = new FormData(e.target);
            let taxWrapper = fd.get('tax_wrapper'); if (taxWrapper === 'None') taxWrapper = null;
            let vesting = [];
            if (fd.get('account_type') === 'RSU Grant') {
                const years = fd.getAll('vest_year[]');
                const percents = fd.getAll('vest_percent[]');
                years.forEach((y, i) => { if (y && percents[i]) vesting.push({ year: parseInt(y), percent: parseFloat(percents[i]) }); });
            }
            const bookCostInput = fd.get('book_cost');
            const bookCostPence = (bookCostInput && !isNaN(parseFloat(bookCostInput))) ? Math.round(parseFloat(bookCostInput) * 100) : null;
            const minBalInput = fd.get('min_balance');
            const minBalPence = (minBalInput && !isNaN(parseFloat(minBalInput))) ? Math.round(parseFloat(minBalInput) * 100) : 0;
            
            const body = {
                name: fd.get('name'), account_type: fd.get('account_type'), tax_wrapper: taxWrapper, currency: fd.get('currency'),
                interest_rate: parseFloat(fd.get('interest_rate')), starting_balance: Math.round(parseFloat(fd.get('starting_balance')) * 100),
                book_cost: bookCostPence, min_balance: minBalPence, // NEW
                owner_ids: Array.from(document.querySelectorAll('input[name="owner_ids"]:checked')).map(c=>parseInt(c.value)), scenario_id: scenarioData.id,
                notes: fd.get('notes'), rsu_target_account_id: parseInt(fd.get('rsu_target_account_id')) || null, vesting_schedule: vesting,
                mortgage_start_date: fd.get('mortgage_start_date') || null, grant_date: fd.get('grant_date') || null,
                unit_price: fd.get('unit_price') ? Math.round(parseFloat(fd.get('unit_price')) * 100) : null,
                original_loan_amount: fd.get('original_loan_amount') ? Math.round(parseFloat(fd.get('original_loan_amount')) * 100) : null,
                amortisation_period_years: fd.get('amortisation_period_years') ? parseInt(fd.get('amortisation_period_years')) : null,
                payment_from_account_id: parseInt(fd.get('payment_from_account_id')) || null,
                fixed_rate_period_years: fd.get('fixed_rate_period_years') ? parseInt(fd.get('fixed_rate_period_years')) : null,
                fixed_interest_rate: fd.get('fixed_interest_rate') ? parseFloat(fd.get('fixed_interest_rate')) : null
            };
            if (body.account_type === 'Mortgage') body.starting_balance = -Math.abs(body.starting_balance);
            await handleFormSubmit(form.querySelector('button[type="submit"]'), async () => {
                if (isNew) await API.createResource('/api/accounts/', body); else await API.updateResource(`/api/accounts/${id}`, body);
                const newData = await API.fetchScenario(scenarioData.id); 
                const url = `/scenarios/${scenarioData.id}`; history.pushState({}, '', url); window.dispatchEvent(new Event('popstate'));
            });
        });
        const delBtn = document.getElementById('del-btn');
        if(delBtn) delBtn.onclick = async () => { if(confirm("Delete?")) { await API.deleteResource(`/api/accounts/${id}`); const url = `/scenarios/${scenarioData.id}`; history.pushState({}, '', url); window.dispatchEvent(new Event('popstate')); } };
    });
}

// ... (keep other functions renderRuleView, renderOwnerView, etc. unchanged)
export function renderRuleView(id, scenarioData) {
    const crumbs = [{ label: 'Home', path: '/' }, { label: scenarioData.name, path: `/scenarios/${scenarioData.id}` }];
    const isNew = id === 'new';
    let rule = null;
    if(!isNew) { rule = scenarioData.automation_rules.find(r => r.id == id); crumbs.push({ label: 'Edit Rule', path: '#' }); } 
    else { crumbs.push({ label: 'Add Rule', path: '#' }); }
    const accOpts = (selId) => getSortedAccountOptions(scenarioData.accounts.filter(a => a.account_type !== 'RSU Grant'), selId);
    const targetOpts = `<option value="">-- External Expense --</option>` + accOpts(rule?.target_account_id);
    const formHtml = `
        <form id="rule-form">
            <input type="hidden" name="scenario_id" value="${scenarioData.id}">
            <div class="form-group"><label>Name (Title)</label><input type="text" name="name" value="${escapeAttr(rule?.name||'New Rule')}" required></div>
            <div class="form-group"><label>Type</label><select name="rule_type" id="rule-type"><option value="sweep" ${rule?.rule_type==='sweep'?'selected':''}>Sweep</option><option value="top_up" ${rule?.rule_type==='top_up'?'selected':''}>Top-Up</option><option value="transfer" ${rule?.rule_type==='transfer'?'selected':''}>Smart Transfer</option><option value="mortgage_smart" ${rule?.rule_type==='mortgage_smart'?'selected':''}>Mortgage Smart Smooth</option></select></div>
            <div class="grid grid-2">
                <div class="form-group"><label id="trigger-label">Trigger (£)</label><input type="number" step="0.01" name="trigger_value" value="${(rule && rule.trigger_value !== undefined) ? rule.trigger_value : ''}" required></div><div class="form-group" id="transfer-val-group"><label id="val-label">Amount (£)</label><input type="number" step="0.01" name="transfer_value" value="${(rule && rule.transfer_value !== undefined && rule.transfer_value !== null) ? rule.transfer_value : ''}"></div></div>
            <div class="form-group"><label>Source</label><select name="source_account_id">${accOpts(rule?.source_account_id)}</select></div>
            <div class="form-group"><label>Target</label><select name="target_account_id">${targetOpts}</select></div>
            <div class="grid grid-2"><div class="form-group"><label>Start</label><input type="date" name="start_date" value="${rule?.start_date||''}"></div><div class="form-group"><label>End</label><input type="date" name="end_date" value="${rule?.end_date||''}"></div></div>
            <div class="grid grid-2"><div class="form-group"><label>Frequency</label><select name="cadence" id="cadence-sel"><option value="monthly" ${rule?.cadence==='monthly'?'selected':''}>Monthly</option><option value="quarterly" ${rule?.cadence==='quarterly'?'selected':''}>Quarterly</option><option value="annually" ${rule?.cadence==='annually'?'selected':''}>Annually</option><option value="once" ${rule?.cadence==='once'?'selected':''}>Once</option></select></div><div class="form-group"><label>Priority</label><input type="number" name="priority" value="${rule?.priority||0}" required><small>Lower numbers run first.</small></div></div>
            <div class="form-group"><label>Notes</label><textarea name="notes" style="width:100%; height:60px;">${escapeAttr(rule?.notes||'')}</textarea></div>
            <div class="form-actions" style="margin-top:20px;"><button type="submit" class="btn btn-primary">${isNew?'Create':'Save'}</button>${!isNew ? '<button type="button" id="del-btn" class="btn btn-danger">Delete</button>' : ''}</div>
        </form>`;
    renderFormWithSidebar(crumbs, isNew ? 'Add Rule' : 'Edit Rule', formHtml, () => {
        const typeSel = document.getElementById('rule-type');
        const updateUI = () => {
             const valGroup = document.getElementById('transfer-val-group');
             const lbl = document.getElementById('val-label');
             if (typeSel.value === 'sweep' || typeSel.value === 'top_up') { valGroup.style.display = 'none'; } else { valGroup.style.display = 'block'; }
             if (typeSel.value === 'mortgage_smart') { lbl.textContent = 'Percentage (%)'; } else { lbl.textContent = 'Amount (£)'; }
        };
        typeSel.addEventListener('change', updateUI);
        updateUI();
        const form = document.getElementById('rule-form');
        form.addEventListener('submit', async e => {
             e.preventDefault();
             const fd = new FormData(e.target);
             const body = Object.fromEntries(fd);
             ['scenario_id','source_account_id','target_account_id'].forEach(k => body[k] = parseInt(body[k]) || null);
             body['priority'] = parseInt(body['priority']) || 0;
             ['trigger_value','transfer_value'].forEach(k => body[k] = body[k] ? parseFloat(body[k]) : null);
             if(!body.start_date) body.start_date = null; if(!body.end_date) body.end_date = null;
             await handleFormSubmit(form.querySelector('button[type="submit"]'), async () => {
                 if(isNew) await API.createRule(body); else await API.updateRule(id, body);
                 const url = `/scenarios/${scenarioData.id}`; history.pushState({}, '', url); window.dispatchEvent(new Event('popstate'));
             });
        });
        const del = document.getElementById('del-btn');
        if(del) del.onclick = async () => { if(confirm("Delete?")) { await API.deleteRule(id); const url = `/scenarios/${scenarioData.id}`; history.pushState({}, '', url); window.dispatchEvent(new Event('popstate')); } };
    });
}

export function renderOwnerView(id, scenarioData) {
    const crumbs = [{ label: 'Home', path: '/' }, { label: scenarioData.name, path: `/scenarios/${scenarioData.id}` }];
    if(id === 'new') {
        crumbs.push({ label: 'Create Owner', path: '#' });
        renderFormWithSidebar(crumbs, 'Create Owner', `<form id="owner-form"><input type="hidden" name="scenario_id" value="${scenarioData.id}"><div class="form-group"><label>Name</label><input name="name" required></div><button type="submit" class="btn btn-primary">Create</button></form>`); 
    } else {
        const owner = scenarioData.owners.find(o => o.id == id);
        if(!owner) return document.getElementById('scenario-content-root').innerHTML = '<p>Not found</p>';
        crumbs.push({ label: owner.name, path: '#' });
        renderFormWithSidebar(crumbs, `Edit Owner: ${owner.name}`, `<form id="owner-form"><div class="form-group"><label>Name</label><input name="name" value="${escapeAttr(owner.name)}" required></div><div class="form-group"><label>Notes</label><textarea name="notes" style="width:100%; height:80px; border:1px solid #e5e7eb; border-radius:6px; padding:8px;">${escapeAttr(owner.notes||'')}</textarea></div><div class="form-actions" style="margin-top: 20px; display: flex; gap: 10px; align-items: center;"><button type="submit" class="btn btn-primary">Save</button><button type="button" id="del-btn" class="btn btn-danger">Delete</button></div></form>`, () => {
            document.getElementById('extra-content-root').innerHTML = `<div class="card"><div style="display:flex; justify-content:space-between; align-items:center;"><h4>Income Sources</h4><a href="/scenarios/${scenarioData.id}/owners/${id}/income_sources/new" class="btn btn-secondary btn-sm">+ Add</a></div><ul class="item-list">${owner.income_sources.map(i => `<li><div><span class="item-name">${escapeAttr(i.name)}</span><span class="item-meta">${formatCurrency(i.net_value, i.currency)} (${i.cadence})</span></div><a href="/scenarios/${scenarioData.id}/income_sources/${i.id}" class="btn btn-sm btn-secondary">Edit</a></li>`).join('')}</ul></div>`;
        });
    }
}

export function renderItemView(type, id, scenarioData, parentId = null) { 
    const crumbs = [{ label: 'Home', path: '/' }, { label: scenarioData.name, path: `/scenarios/${scenarioData.id}` }];
    const isNew = id === 'new';
    let item = null, title = '', formHtml = '';
    const accOpts = (selId) => getSortedAccountOptions(scenarioData.accounts.filter(a => a.account_type !== 'RSU Grant'), selId);
    const notesField = (val) => `<div class="form-group"><label>Notes</label><textarea name="notes" style="width:100%; height:60px;">${escapeAttr(val||'')}</textarea></div>`;

    if (type === 'income_sources') { 
        if (!isNew) { for(const o of scenarioData.owners) { const f = o.income_sources.find(i => i.id == id); if(f) { item = f; parentId = o.id; break; } } } 
        title = isNew ? 'Add Income' : 'Edit Income'; crumbs.push({ label: title, path: '#' }); 
        
        const isPreTax = item?.is_pre_tax || false;
        const sacVal = item?.salary_sacrifice_value ? item.salary_sacrifice_value/100 : '';
        const bikVal = item?.taxable_benefit_value ? item.taxable_benefit_value/100 : '';
        const empVal = item?.employer_pension_contribution ? item.employer_pension_contribution/100 : '';
        
        formHtml = `
        <input type="hidden" name="owner_id" value="${parentId}">
        <div class="form-group"><label>Name</label><input name="name" value="${escapeAttr(item?.name||'')}" required></div>
        
        <div class="card" style="background:#f0fdf4; border-color:#bbf7d0; padding:15px;">
            <div class="checkbox-group" style="margin-bottom:8px;">
                <input type="checkbox" name="is_pre_tax" id="is_pre_tax" value="true" ${isPreTax ? 'checked' : ''}> 
                <label for="is_pre_tax" style="font-weight:600">Pre-Tax (Gross Income)</label>
            </div>
            
            <div id="pre-tax-fields" class="${isPreTax ? '' : 'hidden'}">
                <div class="form-group"><label id="amt-label">Gross Amount</label><input type="number" step="0.01" name="net_value" value="${item && item.net_value !== undefined ? item.net_value/100 : ''}" ${isPreTax ? 'required' : ''}></div>
                
                <hr style="margin: 15px 0; border-top: 1px dashed #bbf7d0;">
                
                <div class="grid grid-2">
                    <div class="form-group">
                        <label>Salary Sacrifice Amount</label>
                        <input type="number" step="0.01" name="salary_sacrifice_value" value="${sacVal}">
                    </div>
                    <div class="form-group">
                        <label>Sacrifice Into Account</label>
                        <select name="salary_sacrifice_account_id"><option value="">-- None --</option>${accOpts(item?.salary_sacrifice_account_id)}</select>
                    </div>
                </div>
                <div class="form-group">
                    <label>Employer Pension Contribution</label>
                    <input type="number" step="0.01" name="employer_pension_contribution" value="${empVal}">
                    <small>Added to Pension Account (Tax Free).</small>
                </div>
                
                <div class="form-group">
                    <label>Taxable Benefits (BiK)</label>
                    <input type="number" step="0.01" name="taxable_benefit_value" value="${bikVal}">
                    <small>Added to Taxable Income, but not paid as cash.</small>
                </div>
            </div>
            
            <div id="post-tax-fields" class="${isPreTax ? 'hidden' : ''}">
                <div class="form-group"><label>Net Amount (Cash)</label><input type="number" step="0.01" name="net_value_net" value="${!isPreTax && item && item.net_value !== undefined ? item.net_value/100 : ''}" ${!isPreTax ? 'required' : ''}></div>
            </div>
        </div>

        <div class="form-group"><label>Currency</label><select name="currency"><option value="GBP" ${item?.currency==='GBP'?'selected':''}>GBP</option><option value="USD" ${item?.currency==='USD'?'selected':''}>USD</option></select></div>
        <div class="form-group"><label>Cadence</label><select name="cadence"><option value="monthly" ${item?.cadence==='monthly'?'selected':''}>Monthly</option><option value="quarterly" ${item?.cadence==='quarterly'?'selected':''}>Quarterly</option><option value="annually" ${item?.cadence==='annually'?'selected':''}>Annually</option></select></div>
        <div class="form-group"><label>Account (for Net Pay)</label><select name="account_id">${accOpts(item?.account_id)}</select></div>
        <div class="grid grid-2"><div class="form-group"><label>Start</label><input type="date" name="start_date" value="${item?.start_date||''}" required></div><div class="form-group"><label>End</label><input type="date" name="end_date" value="${item?.end_date||''}"></div></div>
        ${notesField(item?.notes)}`; 
    } else if (type === 'costs') {
        if (!isNew) item = scenarioData.costs.find(c => c.id == id); title = isNew ? 'Add Cost' : 'Edit Cost'; crumbs.push({ label: title, path: '#' });
        formHtml = `<input type="hidden" name="scenario_id" value="${scenarioData.id}"><div class="form-group"><label>Name</label><input name="name" value="${escapeAttr(item?.name||'')}" required></div><div class="form-group"><label>Value</label><input type="number" step="0.01" name="value" value="${item && item.value !== undefined ? item.value/100 : ''}" required></div><div class="form-group"><label>Currency</label><select name="currency"><option value="GBP" ${item?.currency==='GBP'?'selected':''}>GBP</option><option value="USD" ${item?.currency==='USD'?'selected':''}>USD</option></select></div><div class="form-group"><label>Cadence</label><select name="cadence"><option value="monthly" ${item?.cadence==='monthly'?'selected':''}>Monthly</option><option value="quarterly" ${item?.cadence==='quarterly'?'selected':''}>Quarterly</option><option value="annually" ${item?.cadence==='annually'?'selected':''}>Annually</option></select></div><div class="form-group"><label>Pay From</label><select name="account_id">${accOpts(item?.account_id)}</select></div><div class="grid grid-2"><div class="form-group"><label>Start</label><input type="date" name="start_date" value="${item?.start_date||''}" required></div><div class="form-group"><label>End</label><input type="date" name="end_date" value="${item?.end_date||''}"></div></div><input type="hidden" name="is_recurring" value="true">${notesField(item?.notes)}`;
    } else if (type === 'financial_events') {
        if (!isNew) item = scenarioData.financial_events.find(e => e.id == id); title = isNew ? 'Add Event' : 'Edit Event'; crumbs.push({ label: title, path: '#' });
        const isTransfer = item?.event_type === 'transfer';
        formHtml = `<input type="hidden" name="scenario_id" value="${scenarioData.id}"><div class="form-group"><label>Type</label><select name="event_type" id="ev-type"><option value="income_expense" ${!isTransfer?'selected':''}>Income/Expense</option><option value="transfer" ${isTransfer?'selected':''}>Transfer</option></select></div><div class="form-group"><label>Name</label><input name="name" value="${escapeAttr(item?.name||'')}" required></div><div class="form-group"><label>Value</label><input type="number" step="0.01" name="value" value="${item && item.value !== undefined ? item.value/100 : ''}" required></div><div class="form-group"><label>Currency</label><select name="currency"><option value="GBP" ${item?.currency==='GBP'?'selected':''}>GBP</option><option value="USD" ${item?.currency==='USD'?'selected':''}>USD</option></select></div><div class="form-group"><label>Date</label><input type="date" name="event_date" value="${item?.event_date||''}" required></div><div id="ev-ie" class="${isTransfer?'hidden':''}"><div class="form-group"><label>Account</label><select name="from_account_id_ie">${accOpts(item?.from_account_id)}</select></div></div><div id="ev-tr" class="${!isTransfer?'hidden':''}"><div class="form-group"><label>From</label><select name="from_account_id_t">${accOpts(item?.from_account_id)}</select></div><div class="form-group"><label>To</label><select name="to_account_id">${accOpts(item?.to_account_id)}</select></div></div>${notesField(item?.notes)}`;
    } else if (type === 'transfers') {
        if (!isNew) item = scenarioData.transfers.find(t => t.id == id); title = isNew ? 'Add Transfer' : 'Edit Transfer'; crumbs.push({ label: title, path: '#' });
        formHtml = `<input type="hidden" name="scenario_id" value="${scenarioData.id}"><div class="form-group"><label>Name</label><input name="name" value="${escapeAttr(item?.name||'')}" required></div><div class="form-group"><label>Value</label><input type="number" step="0.01" name="value" value="${item && item.value !== undefined ? item.value/100 : ''}" required></div><div class="form-group"><label>Currency</label><select name="currency"><option value="GBP" ${item?.currency==='GBP'?'selected':''}>GBP</option><option value="USD" ${item?.currency==='USD'?'selected':''}>USD</option></select></div><div class="form-group"><label>Cadence</label><select name="cadence"><option value="monthly" ${item?.cadence==='monthly'?'selected':''}>Monthly</option><option value="quarterly" ${item?.cadence==='quarterly'?'selected':''}>Quarterly</option><option value="annually" ${item?.cadence==='annually'?'selected':''}>Annually</option></select></div><div class="form-group"><label>From</label><select name="from_account_id">${accOpts(item?.from_account_id)}</select></div><div class="form-group"><label>To</label><select name="to_account_id">${accOpts(item?.to_account_id)}</select></div><div class="grid grid-2"><div class="form-group"><label>Start</label><input type="date" name="start_date" value="${item?.start_date||''}" required></div><div class="form-group"><label>End</label><input type="date" name="end_date" value="${item?.end_date||''}"></div></div>${notesField(item?.notes)}`;
    }

    renderFormWithSidebar(crumbs, title, `<form id="generic-form">${formHtml}<div class="form-actions" style="margin-top: 20px; display: flex; gap: 10px; align-items: center;"><button type="submit" class="btn btn-primary">${isNew?'Create':'Save'}</button>${!isNew ? '<button type="button" id="del-btn" class="btn btn-danger">Delete</button>' : ''}</div></form>`, () => {
        if(type === 'financial_events') { const sel = document.getElementById('ev-type'); if (sel) { sel.addEventListener('change', e => { if(e.target.value==='transfer') { document.getElementById('ev-tr').classList.remove('hidden'); document.getElementById('ev-ie').classList.add('hidden'); } else { document.getElementById('ev-tr').classList.add('hidden'); document.getElementById('ev-ie').classList.remove('hidden'); } }); } }
        
        if (type === 'income_sources') {
            const chk = document.getElementById('is_pre_tax');
            const preFields = document.getElementById('pre-tax-fields');
            const postFields = document.getElementById('post-tax-fields');
            const grossInput = document.querySelector('input[name="net_value"]');
            const netInput = document.querySelector('input[name="net_value_net"]');
            
            if (chk) {
                chk.addEventListener('change', (e) => {
                    if(e.target.checked) {
                        preFields.classList.remove('hidden');
                        postFields.classList.add('hidden');
                        grossInput.required = true;
                        netInput.required = false;
                        if(netInput.value) grossInput.value = netInput.value;
                    } else {
                        preFields.classList.add('hidden');
                        postFields.classList.remove('hidden');
                        grossInput.required = false;
                        netInput.required = true;
                        if(grossInput.value) netInput.value = grossInput.value;
                    }
                });
            }
            const form = document.getElementById('generic-form');
            form.addEventListener('submit', (e) => {
               const isPre = document.getElementById('is_pre_tax').checked;
               if (!isPre) { grossInput.value = netInput.value; }
            });
        }
    });
}

export function renderTaxLimitView(id, scenarioData) {
    const crumbs = [{ label: 'Home', path: '/' }, { label: scenarioData.name, path: `/scenarios/${scenarioData.id}` }];
    const isNew = id === 'new';
    let limit = null;
    if(!isNew) { limit = scenarioData.tax_limits.find(l => l.id == id); crumbs.push({ label: 'Edit Limit', path: '#' }); } 
    else { crumbs.push({ label: 'Add Limit', path: '#' }); }

    const TAX_WRAPPERS = ["ISA", "Lifetime ISA", "Pension", "Junior ISA", "None"];
    const ACCOUNT_TYPES = ["Cash", "Investment", "Property", "Mortgage", "Loan", "RSU Grant"];
    const renderMultiSelect = (label, name, options, selectedValues) => `
        <div class="form-group"><label>${label}</label><div class="checkbox-list" style="max-height:150px;overflow-y:auto;border:1px solid #eee;padding:8px;">${options.map(opt => `<div class="checkbox-group"><input type="checkbox" name="${name}" value="${opt}" id="${name}-${opt}" ${(selectedValues && selectedValues.includes(opt))?'checked':''}> <label for="${name}-${opt}">${opt}</label></div>`).join('')}</div></div>
    `;

    const formHtml = `
        <form id="limit-form">
            <div class="form-group"><label>Name</label><input name="name" value="${escapeAttr(limit?.name||'')}" required placeholder="e.g. ISA Allowance"></div>
            <div class="form-group"><label>Annual Limit (£)</label><input type="number" step="0.01" name="amount" value="${limit && limit.amount !== undefined ? limit.amount/100 : ''}" required></div>
            <div class="grid grid-2">
                ${renderMultiSelect('Applies to Wrappers', 'wrappers', TAX_WRAPPERS, limit?.wrappers)}
                ${renderMultiSelect('Restricted to Account Types', 'account_types', ACCOUNT_TYPES, limit?.account_types)}
            </div>
            <div class="grid grid-2"><div class="form-group"><label>Start</label><input type="date" name="start_date" value="${limit?.start_date||''}" required></div><div class="form-group"><label>End</label><input type="date" name="end_date" value="${limit?.end_date||''}"></div></div>
            <div class="form-actions" style="margin-top:20px;"><button type="submit" class="btn btn-primary">${isNew?'Create':'Save'}</button>${!isNew?'<button type="button" id="del-btn" class="btn btn-danger">Delete</button>':''}</div>
        </form>
    `;

    renderFormWithSidebar(crumbs, isNew ? 'Add Tax Limit' : 'Edit Tax Limit', formHtml, () => {
        const form = document.getElementById('limit-form');
        form.addEventListener('submit', async e => {
            e.preventDefault();
            const fd = new FormData(e.target);
            const wrappers = Array.from(document.querySelectorAll('input[name="wrappers"]:checked')).map(c => c.value);
            const types = Array.from(document.querySelectorAll('input[name="account_types"]:checked')).map(c => c.value);
            const body = { name: fd.get('name'), amount: Math.round(parseFloat(fd.get('amount')) * 100), wrappers: wrappers, account_types: types.length > 0 ? types : null, start_date: fd.get('start_date'), end_date: fd.get('end_date') || null };
            await handleFormSubmit(form.querySelector('button[type="submit"]'), async () => {
                if (isNew) await API.createTaxLimit(scenarioData.id, body); else await API.updateTaxLimit(id, body);
                const url = `/scenarios/${scenarioData.id}`; history.pushState({}, '', url); window.dispatchEvent(new Event('popstate'));
            });
        });
        const delBtn = document.getElementById('del-btn');
        if(delBtn) delBtn.onclick = async () => { if(confirm("Delete?")) { await API.deleteTaxLimit(id); const url = `/scenarios/${scenarioData.id}`; history.pushState({}, '', url); window.dispatchEvent(new Event('popstate')); } };
    });
}
