import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useSimulationStore = defineStore('simulation', () => {
    const scenario = ref(null)
    const projection = ref(null)
    const loading = ref(false)
    const error = ref(null)

    // Base URL handling for Dev vs Prod
    const API_BASE = import.meta.env.VITE_API_BASE || '/api'

    async function init() {
        loading.value = true
        error.value = null
        
        // 1. Try to load ID from localStorage, default to 1
        let id = localStorage.getItem('lastScenarioId') || 1
        
        try {
            await loadScenario(id)
        } catch (e) {
            console.warn(`Scenario ${id} not found. Attempting auto-discovery...`)
            // 2. Fallback: Fetch list of all scenarios
            try {
                const res = await fetch(`${API_BASE}/scenarios/`)
                if (!res.ok) throw new Error("Failed to list scenarios")
                
                const list = await res.json()
                if (list.length > 0) {
                    // 3. Load the first available one
                    console.log(`Auto-discovered scenario ID: ${list[0].id}`)
                    await loadScenario(list[0].id)
                } else {
                    // 4. No scenarios exist at all
                    error.value = "No scenarios found. Please create one."
                }
            } catch (listError) {
                error.value = "Failed to load application data."
                console.error(listError)
            }
        } finally {
            loading.value = false
        }
    }

    async function loadScenario(id) {
        const res = await fetch(`${API_BASE}/scenarios/${id}`)
        if (!res.ok) throw new Error("Scenario not found")
        
        scenario.value = await res.json()
        localStorage.setItem('lastScenarioId', id) // Save for next time
        
        // Load Projection immediately after
        await runProjection()
    }

    async function runProjection() {
        if (!scenario.value) return
        
        // Clean overrides logic if needed
        const payload = { months: 120 * 12 } // 120 years just to be safe/long
        
        const res = await fetch(`${API_BASE}/projections/${scenario.value.id}/project?months=600`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        })
        
        if (res.ok) {
            projection.value = await res.json()
        }
    }

    async function saveEntity(type, id, data, successMessage = null, silent = false) {
        if (!silent) loading.value = true
        
        // Determine endpoint based on type
        // mapping: 'automation_rule' -> 'automation_rules'
        const endpointMap = {
            'automation_rule': 'automation_rules',
            'decumulation_strategy': 'decumulation_strategies', // (Actually usually handled via dedicated router or generic items)
            // Wait, we defined Strategies in a dedicated router in main.py? 
            // Yes: app.include_router(strategies.router, ...) -> /api/decumulation_strategies/
        }
        
        // Pluralize simple rule: if ends in 'y' -> 'ies', else 's'
        let collection = endpointMap[type] || (type + 's') 
        
        const url = id === 'new' 
            ? `${API_BASE}/${collection}/`
            : `${API_BASE}/${collection}/${id}`
            
        const method = id === 'new' ? 'POST' : 'PUT'
        
        const res = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        })
        
        if (!res.ok) {
            const err = await res.text()
            console.error("Save failed", err)
            if (!silent) error.value = "Failed to save changes"
            throw new Error(err)
        }
        
        // Reload to sync state
        // In a perfect world we'd update the local object, but reloading ensures full sync
        await loadScenario(scenario.value.id)
        if (!silent) loading.value = false
    }

    async function deleteEntity(type, id) {
        loading.value = true
        let collection = type + 's' // Simple pluralization
        // Special case overrides if needed
        
        await fetch(`${API_BASE}/${collection}/${id}`, { method: 'DELETE' })
        await loadScenario(scenario.value.id)
        loading.value = false
    }

    return {
        scenario,
        projection,
        loading,
        error,
        init,
        runProjection,
        saveEntity,
        deleteEntity
    }
})
