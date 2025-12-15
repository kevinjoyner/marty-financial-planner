// --- API Client ---

export async function fetchScenarios() {
    const res = await fetch(`/api/scenarios/?_=${Date.now()}`);
    if (!res.ok) throw new Error('Failed to fetch scenarios');
    return await res.json();
}

export async function fetchScenario(id) {
    const res = await fetch(`/api/scenarios/${id}?_=${Date.now()}`);
    if (!res.ok) throw new Error('Failed to fetch scenario');
    return await res.json();
}

export async function runProjection(id, months) {
    const res = await fetch(`/api/projections/${id}/project?months=${months}`, { method: 'POST' });
    if (!res.ok) throw new Error('Failed to run projection');
    return await res.json();
}

async function handleResponse(res) {
    if (!res.ok) {
        let errorMsg = res.statusText;
        try {
            const errorData = await res.json();
            console.error("API Error Details:", errorData);
            if (errorData.detail) {
                if (Array.isArray(errorData.detail)) {
                    errorMsg = errorData.detail.map(e => `${e.loc.join('.')}: ${e.msg}`).join('\n');
                } else {
                    errorMsg = errorData.detail;
                }
            }
        } catch (e) {
            console.error("Could not parse error JSON", e);
        }
        alert(`Error ${res.status}: ${errorMsg}`);
        throw new Error(errorMsg);
    }
    return await res.json();
}

export async function createResource(url, body) {
    const res = await fetch(url, { 
        method: 'POST', 
        headers: {'Content-Type': 'application/json'}, 
        body: JSON.stringify(body) 
    });
    return handleResponse(res);
}

export async function updateResource(url, body) {
    const res = await fetch(url, { 
        method: 'PUT', 
        headers: {'Content-Type': 'application/json'}, 
        body: JSON.stringify(body) 
    });
    return handleResponse(res);
}

export async function deleteResource(url) {
    const res = await fetch(url, { method: 'DELETE' });
    if (!res.ok) throw new Error(res.statusText);
    return true;
}

export async function duplicateScenario(id) {
    const res = await fetch(`/api/scenarios/${id}/duplicate`, { method: 'POST' });
    return handleResponse(res);
}

export async function importScenario(id, data) {
    const res = await fetch(`/api/scenarios/${id}/import`, { 
        method: 'POST',
        headers: {'Content-Type': 'application/json'}, 
        body: JSON.stringify(data)
    });
    return handleResponse(res);
}

export async function importNewScenario(data) {
    const res = await fetch(`/api/scenarios/import_new`, { 
        method: 'POST',
        headers: {'Content-Type': 'application/json'}, 
        body: JSON.stringify(data)
    });
    return handleResponse(res);
}

export async function deleteStrategy(id) {
    const res = await fetch(`/api/overpayment_strategies/${id}`, { method: 'DELETE' });
    if (!res.ok) throw new Error(res.statusText);
    return true;
}

export async function updateStrategy(id, body) {
    const res = await fetch(`/api/overpayment_strategies/${id}`, { 
        method: 'PUT', 
        headers: {'Content-Type': 'application/json'}, 
        body: JSON.stringify(body) 
    });
    return handleResponse(res);
}

export async function createRule(body) {
    const res = await fetch('/api/automation_rules/', { 
        method: 'POST', 
        headers: {'Content-Type': 'application/json'}, 
        body: JSON.stringify(body) 
    });
    return handleResponse(res);
}

export async function updateRule(id, body) {
    const res = await fetch(`/api/automation_rules/${id}`, { 
        method: 'PUT', 
        headers: {'Content-Type': 'application/json'}, 
        body: JSON.stringify(body) 
    });
    return handleResponse(res);
}

export async function deleteRule(id) {
    const res = await fetch(`/api/automation_rules/${id}`, { method: 'DELETE' });
    if (!res.ok) throw new Error(res.statusText);
    return true;
}

export async function reorderRules(ruleIds) {
    const res = await fetch(`/api/automation_rules/reorder`, { 
        method: 'PUT', 
        headers: {'Content-Type': 'application/json'}, 
        body: JSON.stringify(ruleIds) 
    });
    return handleResponse(res);
}

export async function createTaxLimit(scenarioId, body) {
    const res = await fetch(`/api/tax_limits/${scenarioId}`, { 
        method: 'POST', 
        headers: {'Content-Type': 'application/json'}, 
        body: JSON.stringify(body) 
    });
    return handleResponse(res);
}

export async function updateTaxLimit(id, body) {
    const res = await fetch(`/api/tax_limits/${id}`, { 
        method: 'PUT', 
        headers: {'Content-Type': 'application/json'}, 
        body: JSON.stringify(body) 
    });
    return handleResponse(res);
}

export async function deleteTaxLimit(id) {
    const res = await fetch(`/api/tax_limits/${id}`, { method: 'DELETE' });
    if (!res.ok) throw new Error(res.statusText);
    return true;
}

// --- History Methods (Restored) ---
export async function fetchScenarioHistory(scenarioId) {
    const res = await fetch(`/api/scenarios/${scenarioId}/history`);
    if (!res.ok) throw new Error('Failed to fetch history');
    return await res.json();
}

export async function restoreScenarioHistory(scenarioId, historyId) {
    const res = await fetch(`/api/scenarios/${scenarioId}/history/${historyId}/restore`, { method: 'POST' });
    if (!res.ok) throw new Error('Failed to restore history');
    return await res.json();
}
