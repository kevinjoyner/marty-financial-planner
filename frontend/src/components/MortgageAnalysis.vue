<script setup>
import { computed } from 'vue'
import { useSimulationStore } from '../stores/simulation'
import { formatCurrency } from '../utils/format'
import { Home, TrendingUp, CheckCircle, AlertTriangle } from 'lucide-vue-next'

const store = useSimulationStore()

const stats = computed(() => {
    if (!store.simulationData || !store.simulationData.mortgage_stats) return []
    // Sort by Year ascending
    return [...store.simulationData.mortgage_stats].sort((a, b) => a.year_start - b.year_start)
})

// Values in stats are in Pounds (float). formatCurrency expects Pence.
const formatAmount = (val) => formatCurrency(val * 100)
</script>

<template>
    <div>
        <div v-if="stats.length === 0" class="p-12 text-center flex flex-col items-center justify-center text-slate-400">
            <Home class="w-12 h-12 mb-4 opacity-50" />
            <p class="text-sm font-medium">No mortgage overpayment data.</p>
            <p class="text-xs mt-1">Add a "Mortgage Overpay" rule to see analysis here.</p>
        </div>

        <div v-else>
            <div class="px-6 py-4 bg-blue-50 border-b border-blue-100 flex items-start gap-3">
                <TrendingUp class="w-5 h-5 text-blue-600 mt-0.5" />
                <div>
                    <h4 class="text-sm font-bold text-blue-900">Smart Overpayment Performance</h4>
                    <p class="text-xs text-blue-700 mt-1">
                        This report tracks how well your "Smart Smooth" rules are performing against their annual targets. 
                        "Headroom" indicates the allowance that was <strong>missed</strong> because your Source Account (e.g. Current Account) 
                        dropped below its Minimum Balance.
                    </p>
                </div>
            </div>

            <table class="w-full text-left text-sm">
                <thead class="bg-slate-50 border-b border-slate-200 text-slate-500 sticky top-0 z-10 shadow-sm">
                    <tr>
                        <th class="px-6 py-3 font-medium w-32">Tax Year</th>
                        <th class="px-6 py-3 font-medium">Rule Name</th>
                        <th class="px-6 py-3 font-medium text-right">Target Allowance</th>
                        <th class="px-6 py-3 font-medium text-right">Actually Paid</th>
                        <th class="px-6 py-3 font-medium text-right">Missed (Headroom)</th>
                        <th class="px-6 py-3 font-medium text-center w-24">Status</th>
                    </tr>
                </thead>
                <tbody class="divide-y divide-slate-100">
                    <tr v-for="(row, idx) in stats" :key="idx" class="hover:bg-slate-50/50 transition-colors">
                        <td class="px-6 py-3 text-slate-500 font-mono text-xs">
                            {{ row.year_start }} - {{ row.year_start + 1 }}
                        </td>
                        <td class="px-6 py-3 font-medium text-slate-700">
                            {{ row.rule_name }}
                        </td>
                        <td class="px-6 py-3 text-right text-slate-500">
                            {{ formatAmount(row.allowance) }}
                        </td>
                        <td class="px-6 py-3 text-right font-bold text-slate-900">
                            {{ formatAmount(row.paid) }}
                        </td>
                        <td class="px-6 py-3 text-right font-mono" :class="row.headroom > 0 ? 'text-amber-600 font-bold' : 'text-slate-300'">
                            {{ formatAmount(row.headroom) }}
                        </td>
                        <td class="px-6 py-3 text-center">
                            <div v-if="row.headroom <= 0" class="inline-flex items-center gap-1 text-xs font-bold text-emerald-600 bg-emerald-50 px-2 py-1 rounded-full">
                                <CheckCircle class="w-3 h-3" /> Maxed
                            </div>
                            <div v-else class="inline-flex items-center gap-1 text-xs font-bold text-amber-600 bg-amber-50 px-2 py-1 rounded-full" title="Missed target due to low funds">
                                <AlertTriangle class="w-3 h-3" /> Missed
                            </div>
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>
</template>
