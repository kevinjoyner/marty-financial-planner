const API_BASE = '/api';

async function handleResponse(res) {
    if (!res.ok) {
        const text = await res.text();
        throw new Error(`API Error ${res.status}: ${text}`);
    }
    return res.json();
}

export const api = {
    async getScenarios() { 
        const res = await fetch(`${API_BASE}/scenarios/`);
        return handleResponse(res);
    },
    
    async createScenario(data) { 
        const res = await fetch(`${API_BASE}/scenarios/`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) });
        return handleResponse(res);
    },
    
    async duplicateScenario(id) { 
        const res = await fetch(`${API_BASE}/scenarios/${id}/duplicate`, { method: 'POST' });
        return handleResponse(res);
    },
    
    async forkScenario(id, data) { 
        const res = await fetch(`${API_BASE}/scenarios/${id}/fork`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) });
        return handleResponse(res);
    },
    
    async deleteScenario(id) { 
        const res = await fetch(`${API_BASE}/scenarios/${id}`, { method: 'DELETE' });
        if (!res.ok) throw new Error('Delete failed');
        return true;
    },
    
    async importNewScenario(jsonData) {
        const res = await fetch(`${API_BASE}/scenarios/import_new?is_legacy=false`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(jsonData) });
        return handleResponse(res);
    },

    async restoreScenario(jsonData) {
        const res = await fetch(`${API_BASE}/scenarios/import_new?is_legacy=false`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(jsonData) });
        return handleResponse(res);
    },

    async getScenario(id) { 
        const res = await fetch(`${API_BASE}/scenarios/${id}`);
        return handleResponse(res);
    },
    
    async runProjection(id, months = 12, overrides = []) {
        const payload = { simulation_months: months, overrides: overrides };
        const res = await fetch(`${API_BASE}/projections/${id}/project`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
        return handleResponse(res);
    },

    // --- Entity Management ---

    async getStrategies(scenarioId) { 
        const res = await fetch(`${API_BASE}/scenarios/${scenarioId}/strategies/`);
        return handleResponse(res);
    },
    async createStrategy(scenarioId, data) { return fetch(`${API_BASE}/scenarios/${scenarioId}/strategies/`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) }); },
    async updateStrategy(scenarioId, strategyId, data) { return fetch(`${API_BASE}/scenarios/${scenarioId}/strategies/${strategyId}`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) }); },
    async deleteStrategy(scenarioId, strategyId) { return fetch(`${API_BASE}/scenarios/${scenarioId}/strategies/${strategyId}`, { method: 'DELETE' }); },

    async createAccount(data) { return fetch(`${API_BASE}/accounts/`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) }); },
    async updateAccount(id, data) { return fetch(`${API_BASE}/accounts/${id}`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) }); },
    
    async createIncome(data) { return fetch(`${API_BASE}/income_sources/`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) }); },
    async updateIncome(id, data) { return fetch(`${API_BASE}/income_sources/${id}`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) }); },
    
    async createCost(data) { return fetch(`${API_BASE}/costs/`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) }); },
    async updateCost(id, data) { return fetch(`${API_BASE}/costs/${id}`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) }); },
    
    async createTransfer(data) { return fetch(`${API_BASE}/transfers/`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) }); },
    async updateTransfer(id, data) { return fetch(`${API_BASE}/transfers/${id}`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) }); },
    
    async createFinancialEvent(data) { return fetch(`${API_BASE}/financial_events/`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) }); },
    async updateFinancialEvent(id, data) { return fetch(`${API_BASE}/financial_events/${id}`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) }); },
    
    async createOwner(data) { return fetch(`${API_BASE}/owners/`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) }); },
    async updateOwner(id, data) { return fetch(`${API_BASE}/owners/${id}`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) }); },
    
    async createTaxLimit(scenarioId, data) { return fetch(`${API_BASE}/tax_limits/${scenarioId}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) }); },
    async updateTaxLimit(id, data) { return fetch(`${API_BASE}/tax_limits/${id}`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) }); },
    
    async createRule(data) { return fetch(`${API_BASE}/automation_rules/`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) }); },
    async updateRule(id, data) { return fetch(`${API_BASE}/automation_rules/${id}`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) }); },
    async reorderRules(ids) { return fetch(`${API_BASE}/automation_rules/reorder`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(ids) }); },

    async updateScenario(id, data) { return fetch(`${API_BASE}/scenarios/${id}`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) }); },

    async deleteResource(url) {
        const res = await fetch(url, { method: 'DELETE' });
        if (!res.ok) throw new Error('Delete failed');
        return true;
    },

    // --- History ---
    async fetchScenarioHistory(scenarioId) {
        const res = await fetch(`${API_BASE}/scenarios/${scenarioId}/history`);
        return handleResponse(res);
    },

    async restoreScenarioHistory(scenarioId, historyId) {
        const res = await fetch(`${API_BASE}/scenarios/${scenarioId}/history/${historyId}/restore`, { method: 'POST' });
        return handleResponse(res);
    }
};
