<script setup>
import { onMounted, computed, ref, watch } from 'vue'
import { useSimulationStore } from '../stores/simulation'
import ProjectionChart from '../components/ProjectionChart.vue'
import Scorecards from '../components/Scorecards.vue'
import ChartLegend from '../components/ChartLegend.vue'
import { AlertTriangle, CheckCircle2, XCircle, ChevronDown, ChevronUp, Lock, Unlock, Download, FileText, EyeOff, Eye } from 'lucide-vue-next'
import { exportBalancesToCSV, exportFlowsToCSV } from '../utils/export'

const store = useSimulationStore()
const alertsExpanded = ref(false)
const isAxisFrozen = ref(false)

// --- Persistence for Horizon ---
// We watch the store value and save it to localStorage
watch(() => store.simulationMonths, (newVal) => {
    localStorage.setItem('marty_simulation_months', newVal)
})

// --- Horizon / Duration Logic ---
const horizonMode = ref('years')
const horizonYears = ref(10)
const horizonMonths = ref(0)
const horizonDate = ref('')

const syncInputsFromStore = () => {
    const totalMonths = store.simulationMonths;
    horizonYears.value = Math.floor(totalMonths / 12);
    horizonMonths.value = totalMonths % 12;
    if (store.scenario) {
        const start = new Date(store.scenario.start_date);
        const end = new Date(start);
        end.setMonth(start.getMonth() + totalMonths);
        try {
            horizonDate.value = end.toISOString().split('T')[0];
        } catch (e) { console.error("Invalid Date", e) }
    }
}

const updateHorizon = () => {
    if (!store.scenario) return;
    const start = new Date(store.scenario.start_date);
    
    if (horizonMode.value === 'years') {
        const totalMonths = (parseInt(horizonYears.value || 0) * 12) + parseInt(horizonMonths.value || 0);
        store.setDuration(totalMonths);
        const newDate = new Date(start);
        newDate.setMonth(start.getMonth() + totalMonths);
        try {
            horizonDate.value = newDate.toISOString().split('T')[0];
        } catch (e) { }
    } else {
        if (!horizonDate.value) return;
        const end = new Date(horizonDate.value);
        let diffMonths = (end.getFullYear() - start.getFullYear()) * 12 + (end.getMonth() - start.getMonth());
        if (diffMonths < 1) diffMonths = 1;
        store.setDuration(diffMonths);
        horizonYears.value = Math.floor(diffMonths / 12);
        horizonMonths.value = diffMonths % 12;
    }
}

watch(() => store.scenario, (val) => { if (val) syncInputsFromStore(); });

// --- Persistence & Settings ---
const visibleAccountIds = ref([])
const aggregationMode = ref('account') 
const isSettingsLoaded = ref(false)
const hiddenAlertSignatures = ref(new Set()) 

const selectAllAccounts = () => {
    if (store.scenario && store.scenario.accounts) {
        visibleAccountIds.value = store.scenario.accounts.map(a => a.id);
    } else {
        visibleAccountIds.value = [];
    }
}

const updateVisibleAccounts = (newIds) => {
    if (!newIds) return;
    if (newIds.length !== visibleAccountIds.value.length) {
        visibleAccountIds.value = newIds;
        return;
    }
    const currentSorted = [...visibleAccountIds.value].sort();
    const newSorted = [...newIds].sort();
    const isSame = currentSorted.every((val, index) => val === newSorted[index]);
    
    if (!isSame) {
        visibleAccountIds.value = newIds;
    }
}

const loadSettings = () => {
    if (!store.activeScenarioId) return;
    const key = `marty_dash_${store.activeScenarioId}`;
    const saved = localStorage.getItem(key);
    const validIds = new Set(store.scenario?.accounts?.map(a => a.id) || []);

    if (saved) {
        try {
            const p = JSON.parse(saved);
            if (p.visibleAccountIds && Array.isArray(p.visibleAccountIds) && p.visibleAccountIds.length > 0) {
                const sanitized = p.visibleAccountIds.filter(id => validIds.has(id));
                if (sanitized.length > 0) visibleAccountIds.value = sanitized;
                else selectAllAccounts();
            } else { selectAllAccounts(); }
            
            if (p.aggregationMode) aggregationMode.value = p.aggregationMode;
            if (p.hiddenAlerts) hiddenAlertSignatures.value = new Set(p.hiddenAlerts);
        } catch(e) { selectAllAccounts(); }
    } else { selectAllAccounts(); }
    isSettingsLoaded.value = true;
}

const saveSettings = () => {
    if (!store.activeScenarioId || !isSettingsLoaded.value) return;
    const key = `marty_dash_${store.activeScenarioId}`;
    localStorage.setItem(key, JSON.stringify({
        visibleAccountIds: visibleAccountIds.value,
        aggregationMode: aggregationMode.value,
        hiddenAlerts: Array.from(hiddenAlertSignatures.value)
    }));
}

onMounted(async () => {
    if (!store.activeScenarioId || !store.scenario) {
        await store.init();
    }
    if (!isSettingsLoaded.value) {
        loadSettings();
    }
    if(store.scenario) syncInputsFromStore();
})

watch(() => store.scenario, (newVal) => {
    if (newVal && newVal.accounts && newVal.accounts.length > 0) {
        if (visibleAccountIds.value.length === 0) {
            loadSettings();
        }
    }
}, { deep: true })

watch(() => store.activeScenarioId, async (newId) => {
    if(newId) {
        isSettingsLoaded.value = false;
        await store.loadScenario(); 
        loadSettings();
        syncInputsFromStore();
    }
});

watch([visibleAccountIds, aggregationMode, hiddenAlertSignatures], saveSettings, { deep: true });

// --- Alert Logic ---
const rawAlerts = computed(() => store.simulationData?.warnings || [])
const baselineAlerts = computed(() => store.baselineData?.warnings || [])

const getTaxYear = (dateStr) => {
    const d = new Date(dateStr)
    const year = d.getFullYear()
    const month = d.getMonth() + 1
    return month >= 4 ? `${year}/${year+1}` : `${year-1}/${year}`
}

const warnSig = (a) => `${a.source_type}:${a.account_id}:${getTaxYear(a.date)}`

const getSourceLabel = (alert) => {
    if (!store.scenario || !alert.source_id) return null
    if (alert.source_type === 'income') {
        for (const owner of store.scenario.owners || []) {
            const inc = (owner.income_sources || []).find(i => i.id === alert.source_id)
            if (inc) return `Income: "${inc.name}"`
        }
    } else if (alert.source_type === 'rule') {
        const rule = (store.scenario.automation_rules || []).find(r => r.id === alert.source_id)
        if (rule) return `Rule: "${rule.name}"`
    }
    return null
}

const dedupAndFilter = (warnings) => {
    const seen = new Set()
    const result = []
    for (const a of warnings) {
        const sig = warnSig(a)
        const hidSig = `${a.source_type}:${a.account_id}`
        if (seen.has(sig) || hiddenAlertSignatures.value.has(hidSig)) continue
        seen.add(sig)
        result.push({ ...a, tax_year: getTaxYear(a.date) })
    }
    return result
}

const alertDiff = computed(() => {
    const model = dedupAndFilter(rawAlerts.value)
    if (!isModelling.value) return { resolved: [], unchanged: model, introduced: [] }
    const base = dedupAndFilter(baselineAlerts.value)
    const baseSigSet = new Set(base.map(warnSig))
    const modelSigSet = new Set(model.map(warnSig))
    return {
        resolved: base.filter(a => !modelSigSet.has(warnSig(a))),
        unchanged: model.filter(a => baseSigSet.has(warnSig(a))),
        introduced: model.filter(a => !baseSigSet.has(warnSig(a)))
    }
})

const allSortedAlerts = computed(() => [
    ...alertDiff.value.introduced.map(a => ({ ...a, _kind: 'introduced' })),
    ...alertDiff.value.unchanged.map(a => ({ ...a, _kind: 'unchanged' })),
    ...alertDiff.value.resolved.map(a => ({ ...a, _kind: 'resolved' }))
])

const hasAnyAlerts = computed(() => allSortedAlerts.value.length > 0)
const visibleAlerts = computed(() => alertsExpanded.value ? allSortedAlerts.value : allSortedAlerts.value.slice(0, 1))
const hiddenCount = computed(() => Math.max(0, allSortedAlerts.value.length - 1))
const ignoredCount = computed(() => {
    const allSigs = new Set([
        ...rawAlerts.value.map(a => `${a.source_type}:${a.account_id}`),
        ...baselineAlerts.value.map(a => `${a.source_type}:${a.account_id}`)
    ])
    return [...hiddenAlertSignatures.value].filter(s => allSigs.has(s)).length
})

const hideAlert = (alert) => {
    const sig = `${alert.source_type}:${alert.account_id}`
    hiddenAlertSignatures.value.add(sig)
    saveSettings()
}

const resetHiddenAlerts = () => {
    hiddenAlertSignatures.value.clear()
    saveSettings()
}

// --- Metrics Calculation ---
const safeDefaults = { 
    current_net_worth: 0, 
    projected_net_worth: 0, 
    net_contributions: 0, 
    investment_growth: 0, 
    annual_return: 0 
};

const calculateMetrics = (data) => {
    if (!data || !data.data_points || data.data_points.length === 0) return safeDefaults;
    
    const lastPoint = data.data_points[data.data_points.length - 1];
    const firstPoint = data.data_points[0];
    
    let current_net_worth_pence = 0;
    if (store.scenario) {
        store.scenario.accounts.forEach(acc => {
            if (acc.account_type !== 'RSU Grant') {
                const bal = firstPoint.account_balances[acc.id] || 0;
                current_net_worth_pence += Math.round(bal); 
            }
        });
    }

    const projected_net_worth_pence = Math.round(lastPoint.balance); 

    let net_contributions_pence = 0;
    data.data_points.forEach(dp => {
        Object.values(dp.flows).forEach(f => {
            const flow_val = (f.income + (f.employer_contribution || 0) - f.costs - f.tax - f.cgt);
            net_contributions_pence += flow_val;
        });
    });
    net_contributions_pence = Math.round(net_contributions_pence); 
    
    const total_delta_pence = projected_net_worth_pence - current_net_worth_pence; 
    const investment_growth_pence = total_delta_pence - net_contributions_pence;
    
    const months = data.data_points.length;
    const years = months / 12;
    
    const total_invested_pence = current_net_worth_pence + net_contributions_pence;
    
    let annual_return = 0;
    if (total_invested_pence > 0 && years > 0) {
        const wealth_ratio = projected_net_worth_pence / total_invested_pence;
        if (wealth_ratio > 0) {
            annual_return = (Math.pow(wealth_ratio, 1/years) - 1) * 100;
        }
    }

    return { 
        current_net_worth: current_net_worth_pence, 
        projected_net_worth: projected_net_worth_pence, 
        net_contributions: net_contributions_pence, 
        investment_growth: investment_growth_pence, 
        annual_return 
    };
}

const metrics = computed(() => calculateMetrics(store.simulationData));
const baselineMetrics = computed(() => calculateMetrics(store.baselineData));
const isModelling = computed(() => store.activeOverrideCount > 0);

const downloadBalances = () => exportBalancesToCSV(store.simulationData, store.scenario)
const downloadFlows = () => exportFlowsToCSV(store.simulationData, store.scenario)
</script>

<template>
    <div class="space-y-6 pb-24 min-h-full flex flex-col">
        
        <div class="flex justify-between items-start flex-shrink-0">
            <div>
                <h1 class="text-2xl font-bold text-slate-900">Financial Dashboard</h1>
                <p class="text-slate-500 text-sm">Real-time projection of your financial future.</p>
                
                <div v-if="hasAnyAlerts" class="mt-3 flex flex-col items-start relative z-20">
                    <div :class="['rounded-lg px-4 py-2 w-full max-w-xl transition-all shadow-sm', isModelling ? 'bg-purple-50 border border-purple-300' : 'bg-amber-50 border border-amber-200']">

                        <!-- A: Modelled scenario header -->
                        <div v-if="isModelling" class="flex items-center gap-2 mb-2 pb-2 border-b border-purple-200">
                            <span class="text-xs font-bold text-purple-600 uppercase tracking-wide">Modelled Scenario</span>
                        </div>

                        <div :class="['space-y-2', alertsExpanded ? 'max-h-64 overflow-y-auto pr-2 custom-scrollbar' : '']">
                            <div v-if="allSortedAlerts.length === 0" :class="['text-xs italic', isModelling ? 'text-purple-700' : 'text-amber-700']">
                                All alerts hidden.
                            </div>
                            <div v-for="(alert, idx) in visibleAlerts" :key="idx" class="flex items-start justify-between group gap-4">
                                <div class="flex items-start gap-2 min-w-0">
                                    <!-- B: Icon by kind -->
                                    <CheckCircle2 v-if="alert._kind === 'resolved'" class="w-4 h-4 text-emerald-500 mt-0.5 flex-shrink-0" />
                                    <XCircle v-else-if="alert._kind === 'introduced'" class="w-4 h-4 text-rose-500 mt-0.5 flex-shrink-0" />
                                    <AlertTriangle v-else class="w-4 h-4 text-amber-600 mt-0.5 flex-shrink-0" />

                                    <div class="min-w-0">
                                        <!-- B: Message with kind-appropriate colour -->
                                        <span :class="['text-sm font-medium leading-tight', alert._kind === 'resolved' ? 'text-emerald-800 opacity-70 line-through' : alert._kind === 'introduced' ? 'text-rose-900' : 'text-amber-900']">
                                            <span :class="['font-mono text-xs opacity-75 mr-1 px-1 rounded', alert._kind === 'resolved' ? 'bg-emerald-100' : alert._kind === 'introduced' ? 'bg-rose-100' : 'bg-amber-100']">{{ alert.tax_year }}:</span>
                                            {{ alert.message }}
                                        </span>
                                        <!-- C: Source label -->
                                        <div v-if="getSourceLabel(alert)" :class="['text-[10px] mt-0.5', alert._kind === 'resolved' ? 'text-emerald-600' : alert._kind === 'introduced' ? 'text-rose-500' : 'text-amber-600']">
                                            {{ getSourceLabel(alert) }}
                                        </div>
                                        <!-- B: Kind badge for resolved / introduced -->
                                        <div v-if="isModelling && alert._kind !== 'unchanged'" :class="['text-[10px] font-bold uppercase tracking-wide mt-0.5', alert._kind === 'resolved' ? 'text-emerald-500' : 'text-rose-500']">
                                            {{ alert._kind === 'resolved' ? 'Resolved by model' : 'Introduced by model' }}
                                        </div>
                                    </div>
                                </div>
                                <button @click="hideAlert(alert)" :class="['opacity-0 group-hover:opacity-100 transition-opacity p-0.5 flex-shrink-0', alert._kind === 'resolved' ? 'text-emerald-400 hover:text-emerald-700' : alert._kind === 'introduced' ? 'text-rose-400 hover:text-rose-700' : 'text-amber-400 hover:text-amber-700']" title="Hide this type of alert">
                                    <EyeOff class="w-3.5 h-3.5" />
                                </button>
                            </div>
                        </div>

                        <div :class="['flex justify-between items-center mt-2 pt-2 border-t', isModelling ? 'border-purple-100' : 'border-amber-100']">
                            <button v-if="hiddenCount > 0 || alertsExpanded"
                                    @click="alertsExpanded = !alertsExpanded"
                                    :class="['text-xs font-medium flex items-center gap-1', isModelling ? 'text-purple-700 hover:text-purple-900' : 'text-amber-700 hover:text-amber-900']">
                                <span v-if="!alertsExpanded">Show {{ hiddenCount }} more</span>
                                <span v-else>Show less</span>
                                <ChevronDown v-if="!alertsExpanded" class="w-3 h-3" />
                                <ChevronUp v-else class="w-3 h-3" />
                            </button>
                            <button v-if="ignoredCount > 0" @click="resetHiddenAlerts" :class="['text-xs flex items-center gap-1 ml-auto', isModelling ? 'text-purple-600/60 hover:text-purple-800' : 'text-amber-600/60 hover:text-amber-800']">
                                <Eye class="w-3 h-3" /> Reset {{ ignoredCount }} hidden
                            </button>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="bg-white border border-slate-200 rounded-lg p-2 shadow-sm flex flex-col gap-2 min-w-[280px]">
                <div class="flex justify-between items-center px-1">
                    <span class="text-xs font-bold text-slate-400 uppercase">Horizon</span>
                    <div class="flex gap-2">
                        <button @click="horizonMode = 'years'" :class="horizonMode === 'years' ? 'text-primary font-bold' : 'text-slate-400 hover:text-slate-600'" class="text-xs">Duration</button>
                        <button @click="horizonMode = 'date'" :class="horizonMode === 'date' ? 'text-primary font-bold' : 'text-slate-400 hover:text-slate-600'" class="text-xs">Date</button>
                    </div>
                </div>
                <div v-if="horizonMode === 'years'" class="flex gap-2 items-center">
                    <div class="relative flex-1"><input type="number" v-model="horizonYears" @change="updateHorizon" class="w-full border border-slate-200 rounded px-2 py-1 text-sm font-bold text-slate-700 text-center cursor-pointer hover:border-slate-300 focus:cursor-text" min="1" max="50"><span class="text-[10px] text-slate-400 absolute right-2 top-1.5 pointer-events-none">Y</span></div>
                    <div class="relative flex-1"><input type="number" v-model="horizonMonths" @change="updateHorizon" class="w-full border border-slate-200 rounded px-2 py-1 text-sm font-bold text-slate-700 text-center cursor-pointer hover:border-slate-300 focus:cursor-text" min="0" max="11"><span class="text-[10px] text-slate-400 absolute right-2 top-1.5 pointer-events-none">M</span></div>
                </div>
                <div v-else><input type="date" v-model="horizonDate" @change="updateHorizon" class="w-full border border-slate-200 rounded px-2 py-1 text-sm font-bold text-slate-700 cursor-pointer"></div>
            </div>
        </div>

        <div class="flex-shrink-0">
            <Scorecards :metrics="metrics" :baselineMetrics="baselineMetrics" :isModelling="isModelling" />
        </div>

        <div class="bg-white rounded-xl border border-slate-200 shadow-sm p-6 flex flex-col mb-10">
             
             <div class="flex justify-between items-start mb-4 flex-shrink-0">
                 <div class="flex items-center gap-4">
                     <h2 class="text-lg font-semibold text-slate-800">Projection</h2>
                     
                     <div class="relative">
                        <select v-model="aggregationMode" class="appearance-none bg-slate-50 border border-slate-300 text-slate-700 text-xs font-semibold rounded px-3 py-1.5 pr-8 focus:outline-none focus:border-primary cursor-pointer hover:bg-slate-100 transition-colors">
                            <option value="total">Total Net Worth</option>
                            <option value="category">By Category</option>
                            <option value="account">By Account</option>
                        </select>
                        <ChevronDown class="w-3 h-3 text-slate-500 absolute right-2.5 top-2 pointer-events-none" />
                     </div>
                 </div>

                 <div class="flex gap-2">
                     <button @click="isAxisFrozen = !isAxisFrozen" :class="isAxisFrozen ? 'text-primary bg-primary/10' : 'text-slate-400 hover:bg-slate-100'" class="p-1.5 rounded-md transition-colors" :title="isAxisFrozen ? 'Unlock Axis' : 'Freeze Axis Scale'">
                        <Lock v-if="isAxisFrozen" class="w-4 h-4" /><Unlock v-else class="w-4 h-4" />
                     </button>
                     <div class="h-6 w-px bg-slate-200 mx-1"></div>
                     <button @click="downloadBalances" class="text-slate-400 hover:text-slate-600 p-1.5 rounded-md transition-colors" title="Download Balances"><Download class="w-4 h-4" /></button>
                     <button @click="downloadFlows" class="text-slate-400 hover:text-slate-600 p-1.5 rounded-md transition-colors" title="Download Transactions"><FileText class="w-4 h-4" /></button>
                 </div>
             </div>
             
             <div class="flex gap-6 min-h-[450px]">
                 <div class="flex-1 min-w-0">
                     <div v-if="store.isInternalLoading" class="flex items-center justify-center text-slate-400 h-[450px]">Updating Model...</div>
                     <ProjectionChart v-else-if="store.simulationData && isSettingsLoaded" 
                        :data="store.simulationData" 
                        :visibleAccountIds="visibleAccountIds" 
                        :aggregationMode="aggregationMode"
                        :freezeAxis="isAxisFrozen" />
                 </div>
                 
                 <div class="w-64 flex-shrink-0 border-l border-slate-100 pl-4 relative">
                     <div class="absolute inset-0 overflow-y-auto custom-scrollbar">
                        <ChartLegend v-if="isSettingsLoaded"
                            :initialSelection="visibleAccountIds"
                            @update:selection="updateVisibleAccounts" />
                     </div>
                 </div>
             </div>
        </div>

    </div>
</template>
