<script setup>
import { ref, onMounted, watch, computed } from 'vue'
import { useSimulationStore } from '../stores/simulation'
import { ChartLine, Wallet, TrendingUp, Calendar, ArrowRight } from 'lucide-vue-next'
import ChartComponent from '../components/ProjectionChart.vue'
import CheckList from '../components/CheckList.vue'

const store = useSimulationStore()

// Local form inputs
const simName = ref('')
const simStartDate = ref('')
const simMonths = ref(120)

// Helper to safely format date for input type="date" (YYYY-MM-DD)
const formatDateForInput = (dateVal) => {
    if (!dateVal) return ''
    // If it's already a string YYYY-MM-DD, just return it
    if (typeof dateVal === 'string' && dateVal.match(/^\d{4}-\d{2}-\d{2}$/)) {
        return dateVal
    }
    const d = new Date(dateVal)
    if (isNaN(d.getTime())) return '' // Invalid date
    return d.toISOString().split('T')[0]
}

const syncInputsFromStore = () => {
    if (store.scenario) {
        simName.value = store.scenario.name
        simStartDate.value = formatDateForInput(store.scenario.start_date)
        // Default to 10 years if not set or just standard view
        // simMonths is purely local for the "Run" button usually
    }
}

onMounted(async () => {
    if (!store.scenario) {
        await store.init()
    }
    syncInputsFromStore()
})

// Watch for scenario changes (e.g. after load)
watch(() => store.scenario, () => {
    syncInputsFromStore()
}, { deep: true })

const updateScenario = async () => {
    if (!store.scenario) return
    await store.saveEntity('scenario', store.scenario.id, {
        name: simName.value,
        start_date: simStartDate.value
    }, "Updated Scenario")
}

const runSim = async () => {
    await store.runProjection()
}

// Computed Summaries
const netWorthStart = computed(() => {
    if (!store.projection || !store.projection.data_points.length) return 0
    return store.projection.data_points[0].balance
})

const netWorthEnd = computed(() => {
    if (!store.projection || !store.projection.data_points.length) return 0
    return store.projection.data_points[store.projection.data_points.length - 1].balance
})

const growthPct = computed(() => {
    if (netWorthStart.value === 0) return 0
    return ((netWorthEnd.value - netWorthStart.value) / netWorthStart.value) * 100
})

const formatCurrency = (val) => {
    return new Intl.NumberFormat('en-GB', { style: 'currency', currency: 'GBP', maximumFractionDigits: 0 }).format(val)
}
</script>

<template>
    <div class="space-y-6 pb-24">
        <div class="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
            <div class="flex flex-col md:flex-row gap-6 items-end">
                <div class="grow space-y-4 w-full">
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                            <label class="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">Scenario Name</label>
                            <input v-model="simName" @change="updateScenario" type="text" class="w-full border-slate-300 rounded-lg shadow-sm focus:border-indigo-500 focus:ring-indigo-500 transition-all font-medium text-slate-700">
                        </div>
                        <div>
                            <label class="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">Start Date</label>
                            <input v-model="simStartDate" @change="updateScenario" type="date" class="w-full border-slate-300 rounded-lg shadow-sm focus:border-indigo-500 focus:ring-indigo-500 transition-all text-slate-700">
                        </div>
                    </div>
                </div>
                
                <div class="shrink-0 flex gap-3">
                    <button @click="runSim" class="bg-indigo-600 hover:bg-indigo-700 text-white px-6 py-2.5 rounded-lg font-semibold shadow-sm transition-all flex items-center gap-2">
                        <TrendingUp class="w-4 h-4" />
                        Run Projection
                    </button>
                </div>
            </div>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-3 gap-6" v-if="store.projection">
            <div class="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex items-center gap-4">
                <div class="w-12 h-12 rounded-full bg-blue-50 text-blue-600 flex items-center justify-center">
                    <Wallet class="w-6 h-6" />
                </div>
                <div>
                    <div class="text-sm text-slate-500 font-medium">Starting Net Worth</div>
                    <div class="text-2xl font-bold text-slate-900">{{ formatCurrency(netWorthStart) }}</div>
                </div>
            </div>
            
            <div class="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex items-center gap-4">
                <div class="w-12 h-12 rounded-full bg-emerald-50 text-emerald-600 flex items-center justify-center">
                    <ChartLine class="w-6 h-6" />
                </div>
                <div>
                    <div class="text-sm text-slate-500 font-medium">Projected Net Worth</div>
                    <div class="text-2xl font-bold text-slate-900">{{ formatCurrency(netWorthEnd) }}</div>
                </div>
            </div>

             <div class="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex items-center gap-4">
                <div class="w-12 h-12 rounded-full bg-indigo-50 text-indigo-600 flex items-center justify-center">
                    <Calendar class="w-6 h-6" />
                </div>
                <div>
                    <div class="text-sm text-slate-500 font-medium">Total Growth</div>
                    <div class="text-2xl font-bold" :class="growthPct >= 0 ? 'text-emerald-600' : 'text-red-600'">
                        {{ growthPct >= 0 ? '+' : '' }}{{ growthPct.toFixed(1) }}%
                    </div>
                </div>
            </div>
        </div>

        <div class="bg-white p-6 rounded-xl border border-slate-200 shadow-sm min-h-[400px]">
            <h3 class="text-lg font-semibold text-slate-800 mb-6">Projection Timeline</h3>
            <ChartComponent v-if="store.projection" :projection="store.projection" />
            <div v-else class="h-64 flex items-center justify-center text-slate-400 italic">
                No projection data available.
            </div>
        </div>

        <div class="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
             <h3 class="text-lg font-semibold text-slate-800 mb-4 flex items-center gap-2">
                <div class="w-2 h-2 rounded-full bg-amber-400"></div>
                Insights & Milestones
             </h3>
             <CheckList />
        </div>
    </div>
</template>
