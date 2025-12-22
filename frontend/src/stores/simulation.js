import { defineStore } from 'pinia'
import { ref, computed, watch } from 'vue'
import { api } from '../services/api'

export const useSimulationStore = defineStore('simulation', () => {
  
  // Persistence
  const savedId = localStorage.getItem('marty_active_scenario_id')
  const activeScenarioId = ref(savedId ? parseInt(savedId) : null)
  
  const savedMonths = localStorage.getItem('marty_simulation_months')
  const simulationMonths = ref(savedMonths ? parseInt(savedMonths) : 120)

  const isInternalLoading = ref(false)
  const scenario = ref(null)
  
  const pinnedItems = ref([]) 
  const overrides = ref({})
  
  const baselineData = ref(null)
  const simulationData = ref(null)
  const history = ref([])

  watch(activeScenarioId, (newVal) => {
      if (newVal) localStorage.setItem('marty_active_scenario_id', newVal)
  })

  watch(simulationMonths, (newVal) => {
      if (newVal) localStorage.setItem('marty_simulation_months', newVal)
  })

  async function loadActiveScenario(id) {
      if (!id) return;
      activeScenarioId.value = id;
      await init();
  }

  async function init() {
    if (!activeScenarioId.value) {
        try {
            const list = await api.getScenarios();
            if (list.length > 0) activeScenarioId.value = list[0].id;
            else return;
        } catch (e) { return; }
    }
    isInternalLoading.value = true;
    try {
        await loadScenario();
        await runBaseline();
    } catch (e) { 
        console.error("Init failed:", e);
    } finally { isInternalLoading.value = false; }
  }

  async function loadScenario() {
      scenario.value = await api.getScenario(activeScenarioId.value);
  }

  function getApiOverrides() {
      return pinnedItems.value
        .filter(item => overrides.value[item.id] !== undefined)
        .map(item => ({
            type: item.type,
            id: item.realId,
            field: item.field,
            value: (item.format === 'currency' && typeof overrides.value[item.id] === 'number') 
                   ? Math.round(overrides.value[item.id] * 100) 
                   : overrides.value[item.id]
        }));
  }

  async function runBaseline() {
      const res = await api.runProjection(activeScenarioId.value, simulationMonths.value, []);
      baselineData.value = res;
      if (Object.keys(overrides.value).length === 0) {
          simulationData.value = res;
      } else {
          await runSimulation();
      }
  }

  async function runSimulation() {
    if (Object.keys(overrides.value).length === 0) {
        if (baselineData.value) simulationData.value = baselineData.value;
        return;
    }
    const apiOverrides = getApiOverrides();
    try {
        const res = await api.runProjection(activeScenarioId.value, simulationMonths.value, apiOverrides);
        simulationData.value = res;
    } catch (e) { console.error("Sim failed", e); }
  }

  async function setDuration(months) {
      simulationMonths.value = months;
      await runBaseline();
  }

  async function saveEntity(type, id, data, description = "Update") {
      isInternalLoading.value = true;
      if (scenario.value) { 
          history.value.unshift({
              timestamp: new Date(),
              description: description,
              scenarioSnapshot: JSON.parse(JSON.stringify(scenario.value))
          });
          if (history.value.length > 20) history.value.pop();
      }

      try {
          const payload = { ...data };
          if (id === 'new') payload.scenario_id = activeScenarioId.value;

          if (payload.value !== undefined) payload.value = Math.round(payload.value * 100);
          if (payload.net_value !== undefined) payload.net_value = Math.round(payload.net_value * 100);
          if (payload.starting_balance !== undefined) payload.starting_balance = Math.round(payload.starting_balance * 100);
          if (payload.original_loan_amount !== undefined && payload.original_loan_amount !== null) payload.original_loan_amount = Math.round(payload.original_loan_amount * 100);
          if (type === 'tax_limit' && payload.amount !== undefined) payload.amount = Math.round(payload.amount * 100);
          if (type === 'rule' && payload.trigger_value !== undefined) payload.trigger_value = Math.round(payload.trigger_value * 100);
          
          if (type === 'rule' && payload.transfer_value !== undefined && payload.transfer_value !== null) {
              if (payload.rule_type !== 'mortgage_smart') {
                  payload.transfer_value = Math.round(payload.transfer_value * 100);
              }
          }
          
          if (type === 'income') {
             if (payload.salary_sacrifice_value) payload.salary_sacrifice_value = Math.round(payload.salary_sacrifice_value * 100);
             if (payload.taxable_benefit_value) payload.taxable_benefit_value = Math.round(payload.taxable_benefit_value * 100);
             if (payload.employer_pension_contribution) payload.employer_pension_contribution = Math.round(payload.employer_pension_contribution * 100);
          }

          if (type === 'account') id === 'new' ? await api.createAccount(payload) : await api.updateAccount(id, payload);
          else if (type === 'income') id === 'new' ? await api.createIncome(payload) : await api.updateIncome(id, payload);
          else if (type === 'cost') id === 'new' ? await api.createCost(payload) : await api.updateCost(id, payload);
          else if (type === 'transfer') id === 'new' ? await api.createTransfer(payload) : await api.updateTransfer(id, payload);
          else if (type === 'event') id === 'new' ? await api.createFinancialEvent(payload) : await api.updateFinancialEvent(id, payload);
          else if (type === 'owner') id === 'new' ? await api.createOwner(payload) : await api.updateOwner(id, payload);
          else if (type === 'tax_limit') id === 'new' ? await api.createTaxLimit(activeScenarioId.value, payload) : await api.updateTaxLimit(id, payload);
          else if (type === 'rule') id === 'new' ? await api.createRule(payload) : await api.updateRule(id, payload);
          else if (type === 'strategy') id === 'new' ? await api.createStrategy(activeScenarioId.value, payload) : await api.updateStrategy(activeScenarioId.value, id, payload);

          await loadScenario();
          await runBaseline(); 
          return true;
      } catch (e) { console.error("Save failed", e); return false; } 
      finally { isInternalLoading.value = false; }
  }

  async function reorderRules(orderedIds) {
      isInternalLoading.value = true;
      if (scenario.value) {
          history.value.unshift({
              timestamp: new Date(),
              description: "Reordered Rules",
              scenarioSnapshot: JSON.parse(JSON.stringify(scenario.value))
          });
          if (history.value.length > 20) history.value.pop();
      }
      try {
          await api.reorderRules(orderedIds);
          await loadScenario();
          await runBaseline();
      } catch (e) { console.error("Reorder failed", e); }
      finally { isInternalLoading.value = false; }
  }

  async function deleteEntity(type, id) {
      if (!confirm("Are you sure you want to delete this?")) return false;
      isInternalLoading.value = true;
      
      if (scenario.value) { 
          history.value.unshift({
              timestamp: new Date(),
              description: `Deleted ${type}`,
              scenarioSnapshot: JSON.parse(JSON.stringify(scenario.value))
          });
      }

      try {
          let url = '';
          if (type === 'account') url = `/api/accounts/${id}`;
          else if (type === 'income') url = `/api/income_sources/${id}`;
          else if (type === 'cost') url = `/api/costs/${id}`;
          else if (type === 'transfer') url = `/api/transfers/${id}`;
          else if (type === 'event') url = `/api/financial_events/${id}`;
          else if (type === 'owner') url = `/api/owners/${id}`;
          else if (type === 'tax_limit') url = `/api/tax_limits/${id}`;
          else if (type === 'rule') url = `/api/automation_rules/${id}`;
          else if (type === 'strategy') url = `/api/scenarios/${activeScenarioId.value}/strategies/${id}`;
          
          await api.deleteResource(url);
          
          if (pinnedItems.value.some(p => p.realId === id && p.type === type)) {
              const item = pinnedItems.value.find(p => p.realId === id && p.type === type);
              unpinItem(item.id);
          }

          await loadScenario();
          await runBaseline(); 
          return true;
      } catch(e) { console.error("Delete failed", e); return false; }
      finally { isInternalLoading.value = false; }
  }

  async function restoreSnapshot(snapshotData, description = "Restored Snapshot") {
      if (!confirm("Rollback to this state?")) return;
      isInternalLoading.value = true;
      const oldId = activeScenarioId.value;
      try {
          const newScen = await api.restoreScenario(snapshotData);
          activeScenarioId.value = newScen.id;
          history.value.unshift({ timestamp: new Date(), description: description, scenarioSnapshot: JSON.parse(JSON.stringify(newScen)) });
          await loadScenario();
          await runBaseline();
          if (oldId && oldId !== newScen.id) await api.deleteScenario(oldId);
      } catch(e) { console.error("Rollback failed", e); } 
      finally { isInternalLoading.value = false; }
  }

  async function commitPinnedItem(item) {
      const val = overrides.value[item.id];
      if (val === undefined) return;
      const payload = {};
      payload[item.field] = val; 
      await saveEntity(item.type, item.realId, payload, `Updated ${item.label}`);
      unpinItem(item.id);
  }

  function pinItem(item) {
    if (!pinnedItems.value.find(i => i.id === item.id)) {
      pinnedItems.value.push(item)
      overrides.value[item.id] = item.value; 
    }
  }

  function unpinItem(itemId) {
    pinnedItems.value = pinnedItems.value.filter(i => i.id !== itemId)
    if (itemId in overrides.value) {
        delete overrides.value[itemId]
    }
    runSimulation()
  }

  function updateOverride(itemId, newValue) {
    overrides.value[itemId] = newValue;
    runSimulation();
  }

  function resetOverrides() {
    pinnedItems.value.forEach(item => overrides.value[item.id] = item.value);
    runSimulation();
  }

  const activeOverrideCount = computed(() => Object.keys(overrides.value).length)
  const currentNetWorth = computed(() => simulationData.value?.data_points[0]?.balance || 0)
  const projectedNetWorth = computed(() => simulationData.value?.data_points[simulationData.value.data_points.length - 1]?.balance || 0)
  const baselineProjectedNetWorth = computed(() => baselineData.value?.data_points[baselineData.value.data_points.length - 1]?.balance || 0)
  const annualReturn = computed(() => {
      if (!simulationData.value) return 0;
      const start = currentNetWorth.value;
      const end = projectedNetWorth.value;
      const years = simulationMonths.value / 12;
      return (start <= 0 || years <= 0) ? 0 : (Math.pow(end / start, 1 / years) - 1) * 100;
  })
  
  const accountsByCategory = computed(() => {
      if (!scenario.value) return { liquid: [], illiquid: [], liabilities: [], unvested: [] };
      const accs = scenario.value.accounts;
      return {
          liquid: accs.filter(a => 
              a.account_type !== 'RSU Grant' && 
              a.account_type !== 'Mortgage' && 
              a.account_type !== 'Loan' && 
              a.account_type !== 'Property' && 
              a.account_type !== 'Main Residence' && 
              (!a.tax_wrapper || a.tax_wrapper === 'None' || a.tax_wrapper === 'ISA' || a.tax_wrapper === 'GIA')
          ),
          illiquid: accs.filter(a => 
              (a.tax_wrapper === 'Pension' || a.tax_wrapper === 'LISA' || a.account_type === 'Property' || a.account_type === 'Main Residence') && 
              a.account_type !== 'RSU Grant'
          ),
          liabilities: accs.filter(a => a.account_type === 'Mortgage' || a.account_type === 'Loan'),
          unvested: accs.filter(a => a.account_type === 'RSU Grant')
      }
  })

  return {
    activeScenarioId, scenario, simulationMonths, pinnedItems, overrides, baselineData, simulationData, history,
    loadActiveScenario, init, setDuration, saveEntity, deleteEntity, pinItem, unpinItem, updateOverride, resetOverrides, restoreSnapshot, commitPinnedItem, getApiOverrides,
    activeOverrideCount, currentNetWorth, projectedNetWorth, baselineProjectedNetWorth, annualReturn, accountsByCategory, loadScenario, runBaseline, runSimulation, reorderRules
  }
})
