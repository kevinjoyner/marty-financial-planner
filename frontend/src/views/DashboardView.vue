<script setup>
import { onMounted, computed, ref, watch } from 'vue'
import { useSimulationStore } from '../stores/simulation'
import ProjectionChart from '../components/ProjectionChart.vue'
import Scorecards from '../components/Scorecards.vue'
import ChartLegend from '../components/ChartLegend.vue'
import { AlertTriangle, ChevronDown, ChevronUp, Lock, Unlock, Download, FileText, EyeOff, Eye } from 'lucide-vue-next'
import { exportBalancesToCSV, exportFlowsToCSV } from '../utils/export'

const store = useSimulationStore()
const alertsExpanded = ref(false)
const isAxisFrozen = ref(false)

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
        horizonDate.value = end.toISOString().split('T')[0];
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
        horizonDate.value = newDate.toISOString().split('T')[0];
    } else {
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

const loadSettings = () => {
    if (!store.activeScenarioId) return;
    const key = `marty_dash_${store.activeScenarioId}`;
    const saved = localStorage.getItem(key);
    if (saved) {
        try {
            const p = JSON.parse(saved);
            if (p.visibleAccountIds && Array.isArray(p.visibleAccountIds) && p.visibleAccountIds.length > 0) {
                visibleAccountIds.value = p.visibleAccountIds;
            } else { selectAllAccounts(); }
            if (p.aggregationMode) aggregationMode.value = p.aggregationMode;
            if (p.hiddenAlerts) hiddenAlertSignatures.value = new Set(p.hiddenAlerts);
        } catch(e) { selectAllAccounts(); }
    } else { selectAllAccounts(); }
    isSettingsLoaded.value = true;
}

const selectAllAccounts = () => {
    if (store.scenario && store.scenario.accounts) {
        visibleAccountIds.value = store.scenario.accounts.map(a => a.id);
    }
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
    await store.init();
    loadSettings();
    if(store.scenario) syncInputsFromStore();
})

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

const filteredAlerts = computed(() => {
    return rawAlerts.value.filter(a => {
        const sig = `${a.source_type}:${a.account_id}`;
        return !hiddenAlertSignatures.value.has(sig);
    });
})

const visibleAlerts = computed(() => alertsExpanded.value ? filteredAlerts.value : filteredAlerts.value.slice(0, 1))
const hiddenCount = computed(() => Math.max(0, filteredAlerts.value.length - 1))
const ignoredCount = computed(() => rawAlerts.value.length - filteredAlerts.value.length)

const hideAlert = (alert) => {
    const sig = `${alert.source_type}:${alert.account_id}`;
    hiddenAlertSignatures.value.add(sig);
    saveSettings(); 
}

const resetHiddenAlerts = () => {
    hiddenAlertSignatures.value.clear();
    saveSettings();
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
    // FIX: Return safe defaults if no data points (New Scenario)
    if (!data || !data.data_points || data.data_points.length === 0) return safeDefaults;
    
    const lastPoint = data.data_points[data.data_points.length - 1];
    const firstPoint = data.data_points[0];
    
    let current_net_worth_pence = 0;
    if (store.scenario) {
        store.scenario.accounts.forEach(acc => {
            if (acc.account_type !== 'RSU Grant') {
                const bal = firstPoint.account_balances[acc.id] || 0;
                current_net_worth_pence += Math.round(bal * 100); 
            }
        });
    }

    const projected_net_worth_pence = Math.round(lastPoint.balance * 100); 

    let net_contributions_pence = 0;
    data.data_points.forEach(dp => {
        Object.values(dp.flows).forEach(f => {
            const flow_val = (f.income + (f.employer_contribution || 0) - f.costs - f.tax - f.cgt);
            net_contributions_pence += (flow_val * 100);
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
                
                <div v-if="rawAlerts.length > 0" class="mt-3 flex flex-col items-start relative z-20">
                     <div class="bg-amber-50 border border-amber-200 rounded-lg px-4 py-2 w-full max-w-xl transition-all shadow-sm">
                        <div :class="['space-y-1', alertsExpanded ? 'max-h-60 overflow-y-auto pr-2 custom-scrollbar' : '']">
                            <div v-if="filteredAlerts.length === 0" class="text-xs text-amber-700 italic">
                                All alerts hidden.
                            </div>
                            <div v-for="(alert, idx) in visibleAlerts" :key="idx" class="flex items-start justify-between group gap-4">
                                <div class="flex items-start gap-2">
                                    <AlertTriangle class="w-4 h-4 text-amber-600 mt-0.5 flex-shrink-0" />
                                    <span class="text-sm text-amber-900 font-medium leading-tight">
                                        <span class="font-mono text-xs opacity-75 mr-1">{{ alert.date }}:</span>
                                        {{ alert.message }}
                                    </span>
                                </div>
                                <button @click="hideAlert(alert)" class="text-amber-400 hover:text-amber-700 opacity-0 group-hover:opacity-100 transition-opacity p-0.5" title="Hide this type of alert">
                                    <EyeOff class="w-3.5 h-3.5" />
                                </button>
                            </div>
                        </div>
                        
                        <div class="flex justify-between items-center mt-2 pt-2 border-t border-amber-100">
                            <button v-if="hiddenCount > 0 || alertsExpanded" 
                                    @click="alertsExpanded = !alertsExpanded"
                                    class="text-xs text-amber-700 hover:text-amber-900 font-medium flex items-center gap-1">
                                <span v-if="!alertsExpanded">Show {{ hiddenCount }} more</span>
                                <span v-else>Show less</span>
                                <ChevronDown v-if="!alertsExpanded" class="w-3 h-3" />
                                <ChevronUp v-else class="w-3 h-3" />
                            </button>
                            
                            <button v-if="ignoredCount > 0" @click="resetHiddenAlerts" class="text-xs text-amber-600/60 hover:text-amber-800 flex items-center gap-1 ml-auto">
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
                     <div v-if="store.loading" class="flex items-center justify-center text-slate-400 h-[450px]">Updating Model...</div>
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
                            @update:selection="ids => visibleAccountIds = ids" />
                     </div>
                 </div>
             </div>
        </div>

    </div>
</template>
