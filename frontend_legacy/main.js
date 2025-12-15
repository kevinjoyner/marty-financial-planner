import * as API from './api.js';
import * as Views from './views/index.js';
import { globalState, currentScenarioData, setScenarioData, setGlobalState } from './state.js';
import { escapeAttr } from './utils.js';

let currentScenarioId = null;
const contentRoot = document.getElementById('scenario-content-root');
const scenariosList = document.getElementById('scenarios-list');

async function handleRouting() {
    const path = window.location.pathname;
    
    if (path === '/help') { loadHelpView(); return; }
    if (path === '/compare') { loadComparisonView(); return; }
    
    const match = path.match(/^\/scenarios\/(\d+)/);
    if(match) { 
        loadScenarioView(match[1]); 
    } else {
        const detailSection = document.getElementById('scenario-detail-section');
        const listSection = document.getElementById('scenarios-section');
        if(detailSection) detailSection.classList.add('hidden');
        if(listSection) listSection.classList.remove('hidden');
        
        // FIX: Init buttons BEFORE fetching data so they work even if API fails
        initDashboardButtons(); 
        fetchScenarios();
    }
}

function loadHelpView() {
    document.getElementById('scenarios-section').classList.add('hidden');
    document.getElementById('scenario-detail-section').classList.remove('hidden');
    const header = document.getElementById('scenario-detail-header');
    if(header) header.style.display = 'none';
    Views.renderHelpView(contentRoot);
}

function setupGlobalNav() {
    let header = document.querySelector('body > header');
    if (!header) {
        const appTitle = document.querySelector('h1'); 
        if(appTitle && appTitle.parentNode.tagName === 'HEADER') {
            header = appTitle.parentNode;
        } else {
            header = document.createElement('header');
            header.style.cssText = "display:flex; justify-content:space-between; align-items:center; padding:10px 20px; background:#fff; border-bottom:1px solid #eee;";
            header.innerHTML = '<div style="font-weight:bold; font-size:1.2rem;">Marty</div>';
            document.body.insertBefore(header, document.body.firstChild);
        }
    }
    if (document.getElementById('nav-help-link')) return;

    const helpLink = document.createElement('a');
    helpLink.id = 'nav-help-link';
    helpLink.href = '/help';
    helpLink.target = '_blank';
    // Use SVG Icon
    helpLink.innerHTML = `Guide <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-left:4px; vertical-align:text-bottom;"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path><polyline points="15 3 21 3 21 9"></polyline><line x1="10" y1="14" x2="21" y2="3"></line></svg>`;
    helpLink.style.cssText = "text-decoration:none; color:var(--primary-color); font-weight:600; font-size:0.9rem; margin-left: auto;";
    header.appendChild(helpLink);
}

// NEW: Initialize buttons separately
function initDashboardButtons() {
    const compareBtn = document.getElementById('go-compare-btn');
    if(compareBtn) compareBtn.onclick = () => navigate('/compare');
    setupImportNew();
}

async function fetchScenarios() {
    try {
        const scenarios = await API.fetchScenarios();
        Views.renderScenarioList(scenariosList, scenarios);
    } catch (e) { console.error("Failed to load scenarios:", e); }
}

function setupImportNew() {
    const btn = document.getElementById('import-new-btn');
    const input = document.getElementById('import-new-input');
    if(btn && input) {
        // Remove old listeners by cloning
        const newBtn = btn.cloneNode(true);
        btn.parentNode.replaceChild(newBtn, btn);
        
        newBtn.onclick = () => input.click();
        input.onchange = null;
        input.onchange = (e) => {
            const file = e.target.files[0];
            if(!file) return;
            const reader = new FileReader();
            reader.onload = async (evt) => {
                try {
                    newBtn.textContent = "Uploading...";
                    const json = JSON.parse(evt.target.result);
                    const newScen = await API.importNewScenario(json);
                    alert("Imported!");
                    navigate(`/scenarios/${newScen.id}`);
                } catch (err) { alert("Import Failed: " + err.message); } 
                finally { newBtn.textContent = "Import Scenario"; input.value = ''; }
            };
            reader.readAsText(file);
        };
    }
}

async function loadComparisonView() {
    currentScenarioId = null;
    document.getElementById('scenarios-section').classList.add('hidden');
    document.getElementById('scenario-detail-section').classList.remove('hidden');
    document.getElementById('scenario-detail-name').textContent = "Compare Scenarios";
    
    const header = document.getElementById('scenario-detail-header');
    if(header) header.style.display = 'block';
    
    const existingActions = header.querySelector('.header-actions');
    if(existingActions) existingActions.remove();
    
    const navContainer = document.querySelector('.nav-bar .breadcrumbs');
    if(navContainer) { Views.renderBreadcrumbs(navContainer, [{ label: 'Home', path: '/' }, { label: 'Compare', path: '#' }]); }
    
    const scenarios = await API.fetchScenarios();
    Views.renderComparisonDashboard(contentRoot, scenarios);
    
    document.getElementById('run-comp-btn').addEventListener('click', async () => {
        const idA = document.getElementById('scen-a').value;
        const idB = document.getElementById('scen-b').value;
        const years = document.getElementById('comp-years').value;
        try {
            const [resA, resB] = await Promise.all([
                API.runProjection(idA, years*12),
                API.runProjection(idB, years*12)
            ]);
            document.getElementById('comp-results').classList.remove('hidden');
            const { renderComparisonChart } = await import('./charts.js');
            renderComparisonChart('comp-chart', resA, resB, "", "");
            Views.renderComparisonTable(resA, resB);
        } catch(e) { alert("Failed"); }
    });
}

async function loadScenarioView(id) {
    currentScenarioId = id;
    document.getElementById('scenarios-section').classList.add('hidden');
    document.getElementById('scenario-detail-section').classList.remove('hidden');
    
    const header = document.getElementById('scenario-detail-header');
    if(header) header.style.display = 'block';

    try {
        const data = await API.fetchScenario(id);
        setScenarioData(data); 
        document.getElementById('scenario-detail-name').textContent = data.name;
        
        const desc = data.description || '';
        if (desc.includes("Testing Gross Income")) {
            document.getElementById('scenario-detail-description').textContent = ''; 
        } else {
            document.getElementById('scenario-detail-description').textContent = desc;
        }
        
        setupHeaderActions();
        handleSubRouting();
    } catch (e) { console.error(e); }
}

function setupHeaderActions() {
    const header = document.getElementById('scenario-detail-header');
    const existingActions = header.querySelector('.header-actions');
    if(existingActions) existingActions.remove();
    const staticEditBtn = document.getElementById('edit-scenario-btn');
    if(staticEditBtn) staticEditBtn.remove();

    const actionsDiv = document.createElement('div');
    actionsDiv.className = 'header-actions';
    actionsDiv.style.cssText = "display: flex; gap: 10px; margin-left: auto;";

    const editBtn = document.createElement('button');
    editBtn.className = 'btn btn-secondary'; editBtn.textContent = 'Edit';
    editBtn.onclick = () => {
         const navContainer = document.querySelector('.nav-bar .breadcrumbs');
         const crumbs = [{ label: 'Home', path: '/' }, { label: currentScenarioData.name, path: '#' }];
         if(navContainer) Views.renderBreadcrumbs(navContainer, crumbs);
         Views.renderFormWithSidebar(crumbs, 'Edit Scenario', 
            `<form id="scen-form">
                <div class="form-group"><label>Name</label><input name="name" value="${escapeAttr(currentScenarioData.name)}" required></div>
                <div class="form-group"><label>Description</label><input name="description" value="${escapeAttr(currentScenarioData.description||'')}"></div>
                <div class="form-group"><label>Start Date</label><input type="date" name="start_date" value="${currentScenarioData.start_date}" required></div>
                <div class="form-group"><label>GBP to USD</label><input type="number" step="0.01" name="gbp_to_usd_rate" value="${currentScenarioData.gbp_to_usd_rate}" required></div>
                <div class="form-group"><label>Notes</label><textarea name="notes" style="width:100%; height:80px; border:1px solid #e5e7eb; border-radius:6px; padding:8px;">${escapeAttr(currentScenarioData.notes||'')}</textarea></div>
                <div class="form-actions" style="margin-top: 20px; display: flex; gap: 10px; align-items: center;">
                    <button type="submit" class="btn btn-primary">Save</button>
                    <button type="button" id="cancel-scen" class="btn btn-secondary">Cancel</button>
                </div>
            </form>`,
            () => {
                document.getElementById('scen-form').addEventListener('submit', async e => {
                    e.preventDefault();
                    const fd = new FormData(e.target);
                    const body = { name: fd.get('name'), description: fd.get('description'), start_date: fd.get('start_date'), gbp_to_usd_rate: parseFloat(fd.get('gbp_to_usd_rate')), notes: fd.get('notes') };
                    await API.updateResource(`/api/scenarios/${currentScenarioData.id}`, body);
                    loadScenarioView(currentScenarioData.id); 
                });
                document.getElementById('cancel-scen').addEventListener('click', () => loadScenarioView(currentScenarioData.id));
            }
         );
    };

    const duplicateBtn = document.createElement('button');
    duplicateBtn.className = 'btn btn-secondary'; duplicateBtn.textContent = 'Duplicate';
    duplicateBtn.onclick = async () => {
        if(!confirm("Duplicate?")) return;
        try {
            const newScen = await API.duplicateScenario(currentScenarioData.id);
            navigate(`/scenarios/${newScen.id}`);
        } catch(e) { alert(e.message); }
    };

    const exportBtn = document.createElement('button');
    exportBtn.className = 'btn btn-secondary'; exportBtn.textContent = 'Export';
    exportBtn.onclick = () => {
        const jsonStr = JSON.stringify(currentScenarioData, null, 2);
        const blob = new Blob([jsonStr], { type: "application/json" });
        const url = URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.href = url;
        link.download = `marty_scenario_${currentScenarioData.name.replace(/[^a-z0-9]/gi, '_').toLowerCase()}.json`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    };

    const importInput = document.createElement('input');
    importInput.type = 'file';
    importInput.accept = '.json';
    importInput.style.display = 'none';
    importInput.onchange = (e) => {
        const file = e.target.files[0];
        if(!file) return;
        const reader = new FileReader();
        reader.onload = async (evt) => {
            try {
                const json = JSON.parse(evt.target.result);
                if(!confirm(`Overwrite "${currentScenarioData.name}"?`)) { importInput.value = ''; return; }
                await API.importScenario(currentScenarioData.id, json);
                alert("Imported!");
                loadScenarioView(currentScenarioData.id);
            } catch (err) { alert("Failed."); } 
            finally { importInput.value = ''; }
        };
        reader.readAsText(file);
    };

    const importBtn = document.createElement('button');
    importBtn.className = 'btn btn-secondary'; importBtn.textContent = 'Import';
    importBtn.onclick = () => importInput.click();

    const historyBtn = document.createElement('button');
    historyBtn.className = 'btn btn-secondary'; historyBtn.textContent = 'History';
    historyBtn.onclick = () => Views.renderHistoryModal(currentScenarioData.id);

    actionsDiv.appendChild(editBtn);
    actionsDiv.appendChild(duplicateBtn);
    actionsDiv.appendChild(exportBtn);
    actionsDiv.appendChild(importBtn);
    actionsDiv.appendChild(importInput); 
    actionsDiv.appendChild(historyBtn);
    header.appendChild(actionsDiv);
}

// ... handleSubRouting and other view handlers remain the same ...
function handleSubRouting() {
    const path = window.location.pathname.split('/');
    const view = path[3];
    const id = path[4];

    if (!view) return Views.renderScenarioDashboard(contentRoot, currentScenarioData);
    
    if (view === 'rules') {
        Views.renderRuleView(id, currentScenarioData);
        return;
    }

    if (view === 'tax_limits') { 
        Views.renderTaxLimitView(id, currentScenarioData);
        return;
    }

    if (view === 'accounts') {
        Views.renderAccountForm(contentRoot, id, currentScenarioData, id === 'new');
        return;
    } 
    
    if (['owners', 'costs', 'financial_events', 'transfers', 'income_sources'].includes(view)) {
        if (view === 'owners') {
             if (path[5] === 'income_sources' && path[6] === 'new') {
                 Views.renderItemView('income_sources', 'new', currentScenarioData, id); 
                 attachGenericListeners('income_sources', 'new', `/api/income_sources/`, id);
                 return;
             }
             Views.renderOwnerView(id, currentScenarioData);
        } else {
             Views.renderItemView(view, id, currentScenarioData);
        }
        
        const form = document.querySelector('form');
        if(form) {
            const url = `/api/${view}/${id === 'new' ? '' : id}`;
            const finalUrl = view === 'owners' ? `/api/owners/${id === 'new' ? '' : id}` : url;
            attachGenericListeners(view, id, finalUrl);
        }
    }
}

function attachGenericListeners(type, id, url, parentId=null) {
    const form = document.getElementById('generic-form') || document.getElementById('owner-form');
    if(!form) return;

    form.addEventListener('submit', async e => {
        e.preventDefault();
        const fd = new FormData(e.target);
        
        if (type === 'income_sources') {
            const isPre = document.getElementById('is_pre_tax');
            if (isPre && !isPre.checked) {
                const netVal = document.querySelector('input[name="net_value_net"]').value;
                fd.set('net_value', netVal);
            }
            if (isPre) {
                fd.set('is_pre_tax', isPre.checked); 
            }
        }

        const body = Object.fromEntries(fd);
        
        const toPence = (val) => (val && !isNaN(parseFloat(val))) ? Math.round(parseFloat(val) * 100) : 0;
        
        if('value' in body) body.value = toPence(body.value);
        if('net_value' in body) body.net_value = toPence(body.net_value);
        
        if ('transfer_value' in body) {
            if (body.rule_type === 'mortgage_smart') {
                body.transfer_value = body.transfer_value ? parseFloat(body.transfer_value) : 0;
            } else {
                body.transfer_value = toPence(body.transfer_value);
            }
        }
        
        body.salary_sacrifice_value = toPence(body.salary_sacrifice_value);
        body.taxable_benefit_value = toPence(body.taxable_benefit_value);
        body.employer_pension_contribution = toPence(body.employer_pension_contribution);
        
        ['owner_id', 'account_id', 'from_account_id', 'to_account_id', 'scenario_id', 'salary_sacrifice_account_id'].forEach(k => { 
            if (body[k] === '' || body[k] === undefined || body[k] === null) {
                body[k] = null;
            } else {
                const parsed = parseInt(body[k]);
                body[k] = isNaN(parsed) ? null : parsed;
            }
        });
        
        if(body.end_date === '') body.end_date = null;

        if (type === 'financial_events') {
            if (body.event_type === 'transfer') { body.from_account_id = parseInt(body.from_account_id_t); body.to_account_id = parseInt(body.to_account_id); }
            else { body.from_account_id = parseInt(body.from_account_id_ie); body.to_account_id = null; }
        }

        if(id === 'new') {
             await API.createResource(url, body);
             let redirect = `/scenarios/${currentScenarioData.id}`;
             if(type === 'income_sources') redirect = `/scenarios/${currentScenarioData.id}/owners/${body.owner_id || parentId}`;
             navigate(redirect);
        } else {
             await updateAndStay(url, body, e.submitter); 
        }
    });

    const del = document.getElementById('del-btn');
    if(del) del.addEventListener('click', () => deleteAndRedirect(url));
}

async function updateAndStay(url, body, btnElement) {
    const btn = btnElement || document.querySelector('button[type="submit"]');
    try {
        await API.updateResource(url, body);
        if (btn) { btn.classList.remove('btn-pulse'); void btn.offsetWidth; btn.classList.add('btn-pulse'); setTimeout(() => { btn.classList.remove('btn-pulse'); }, 600); }
        loadScenarioView(currentScenarioData.id);
    } catch(e) { console.error(e); alert('Failed'); }
}

async function deleteAndRedirect(url) {
    if(!confirm("Delete?")) return;
    await API.deleteResource(url);
    navigate(`/scenarios/${currentScenarioData.id}`);
}

function navigate(url) {
    history.pushState({}, '', url);
    handleRouting();
}

document.getElementById('create-scenario-form')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const fd = new FormData(e.target);
    await API.createResource('/api/scenarios/', { name: fd.get('name'), description: fd.get('description'), start_date: fd.get('start_date'), gbp_to_usd_rate: parseFloat(fd.get('gbp_to_usd_rate')) });
    fetchScenarios();
});

if(scenariosList) {
    scenariosList.addEventListener('click', async (e) => {
        if (e.target.classList.contains('import-file-input')) return;
        const li = e.target.closest('li');
        if(!li) return;
        const id = li.dataset.id;
        if (e.target.classList.contains('delete-btn')) {
            e.stopPropagation();
            if (!confirm("Delete?")) return;
            await API.deleteResource(`/api/scenarios/${id}`);
            fetchScenarios();
            return;
        }
        if (e.target.classList.contains('export-btn')) {
            e.stopPropagation();
            try {
                const data = await API.fetchScenario(id);
                const jsonStr = JSON.stringify(data, null, 2);
                const blob = new Blob([jsonStr], { type: "application/json" });
                const url = URL.createObjectURL(blob);
                const link = document.createElement("a");
                link.href = url;
                link.download = `marty_scenario_${data.name.replace(/[^a-z0-9]/gi, '_').toLowerCase()}.json`;
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
            } catch(err) { alert("Export failed"); }
            return;
        }
        if (e.target.classList.contains('import-btn')) {
            e.stopPropagation();
            const input = li.querySelector('.import-file-input');
            if(input) {
                input.onchange = null;
                input.onchange = (evt) => {
                    const file = evt.target.files[0];
                    if(!file) return;
                    const reader = new FileReader();
                    reader.onload = async (re) => {
                        try {
                            if(!confirm("Overwrite?")) { input.value = ''; return; }
                            const json = JSON.parse(re.target.result);
                            await API.importScenario(id, json);
                            alert("Imported!");
                            navigate(`/scenarios/${id}`);
                        } catch(err) { alert("Import failed"); }
                        finally { input.value = ''; }
                    };
                    reader.readAsText(file);
                };
                input.click();
            }
            return;
        }
        navigate(`/scenarios/${id}`);
    });
}

setupGlobalNav();
window.addEventListener('popstate', handleRouting);
handleRouting();
