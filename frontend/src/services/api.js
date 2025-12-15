const API_BASE = '/api';

export const api = {
    async getScenarios() { return (await fetch(`${API_BASE}/scenarios/`)).json(); },
    
    async createScenario(data) { return (await fetch(`${API_BASE}/scenarios/`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) })).json(); },
    
    async duplicateScenario(id) { return (await fetch(`${API_BASE}/scenarios/${id}/duplicate`, { method: 'POST' })).json(); },
    
    async forkScenario(id, data) { return (await fetch(`${API_BASE}/scenarios/${id}/fork`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) })).json(); },
    
    async deleteScenario(id) { 
        const res = await fetch(`${API_BASE}/scenarios/${id}`, { method: 'DELETE' });
        if (!res.ok) throw new Error('Delete failed');
        return true;
    },
    
    async importNewScenario(jsonData) {
        const res = await fetch(`${API_BASE}/scenarios/import_new?is_legacy=false`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(jsonData) });
        if (!res.ok) throw new Error('Import failed');
        return res.json();
    },

    async restoreScenario(jsonData) {
        const res = await fetch(`${API_BASE}/scenarios/import_new?is_legacy=false`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(jsonData) });
        if (!res.ok) throw new Error('Restore failed');
        return res.json();
    },

    async getScenario(id) { return (await fetch(`${API_BASE}/scenarios/${id}`)).json(); },
    
    async runProjection(id, months = 12, overrides = []) {
        const payload = { simulation_months: months, overrides: overrides };
        return (await fetch(`${API_BASE}/projections/${id}/project`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) })).json();
    },

    async updateAccount(id, data) { return fetch(`${API_BASE}/accounts/${id}`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) }); },
    async updateIncome(id, data) { return fetch(`${API_BASE}/income_sources/${id}`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) }); },
    async updateCost(id, data) { return fetch(`${API_BASE}/costs/${id}`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) }); },
    async updateTransfer(id, data) { return fetch(`${API_BASE}/transfers/${id}`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) }); },
    async createTransfer(data) { return fetch(`${API_BASE}/transfers/`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) }); },
    async updateFinancialEvent(id, data) { return fetch(`${API_BASE}/financial_events/${id}`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) }); },
    async createFinancialEvent(data) { return fetch(`${API_BASE}/financial_events/`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) }); },
    async updateOwner(id, data) { return fetch(`${API_BASE}/owners/${id}`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) }); },
    async updateTaxLimit(id, data) { return fetch(`${API_BASE}/tax_limits/${id}`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) }); },
    async updateRule(id, data) { return fetch(`${API_BASE}/automation_rules/${id}`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) }); },
    async createRule(data) { return fetch(`${API_BASE}/automation_rules/`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) }); },
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
        if (!res.ok) throw new Error('Failed to fetch history');
        return await res.json();
    },

    async restoreScenarioHistory(scenarioId, historyId) {
        const res = await fetch(`${API_BASE}/scenarios/${scenarioId}/history/${historyId}/restore`, { method: 'POST' });
        if (!res.ok) throw new Error('Failed to restore history');
        return await res.json();
    }
};
