<script setup>
import { computed, ref } from 'vue'
import { useSimulationStore } from '../stores/simulation'
import { formatCurrency } from '../utils/format'
import { ArrowRight, FileSearch, ArrowUp, ArrowDown } from 'lucide-vue-next'

const store = useSimulationStore()

// Sorting State
const sortKey = ref('date') 
const sortDesc = ref(true) // Default to Newest First

const sortBy = (key) => {
    if (sortKey.value === key) {
        sortDesc.value = !sortDesc.value
    } else {
        sortKey.value = key
        // Default sort direction for new columns:
        // Dates/Amounts -> Descending (True)
        // Text -> Ascending (False)
        sortDesc.value = ['date', 'amount'].includes(key)
    }
}

const logs = computed(() => {
    if (!store.simulationData || !store.simulationData.rule_logs) return []
    
    // Create a copy to sort
    const data = [...store.simulationData.rule_logs]
    
    return data.sort((a, b) => {
        let valA = a[sortKey.value]
        let valB = b[sortKey.value]
        
        // Handle strings case-insensitively
        if (typeof valA === 'string') valA = valA.toLowerCase()
        if (typeof valB === 'string') valB = valB.toLowerCase()
        
        let comparison = 0
        if (valA > valB) comparison = 1
        else if (valA < valB) comparison = -1
        
        return sortDesc.value ? comparison * -1 : comparison
    })
})

const formatAmount = (val) => formatCurrency(val)
</script>

<template>
    <div>
        <div v-if="logs.length === 0" class="p-12 text-center flex flex-col items-center justify-center text-slate-400">
            <FileSearch class="w-12 h-12 mb-4 opacity-50" />
            <p class="text-sm font-medium">No automation activity recorded.</p>
            <p class="text-xs mt-1">Run a simulation with Rules enabled to see logs here.</p>
        </div>

        <table v-else class="w-full text-left text-sm">
            <thead class="bg-slate-50 border-b border-slate-200 text-slate-500 sticky top-0 z-10 shadow-sm select-none">
                <tr>
                    <th @click="sortBy('date')" class="px-6 py-3 font-medium whitespace-nowrap w-32 cursor-pointer hover:bg-slate-100 transition-colors">
                        <div class="flex items-center gap-1">
                            Date
                            <span v-if="sortKey === 'date'" class="text-slate-400">
                                <ArrowDown v-if="sortDesc" class="w-3 h-3" />
                                <ArrowUp v-else class="w-3 h-3" />
                            </span>
                        </div>
                    </th>
                    <th @click="sortBy('rule_type')" class="px-6 py-3 font-medium whitespace-nowrap w-32 cursor-pointer hover:bg-slate-100 transition-colors">
                        <div class="flex items-center gap-1">
                            Rule Type
                            <span v-if="sortKey === 'rule_type'" class="text-slate-400">
                                <ArrowDown v-if="sortDesc" class="w-3 h-3" />
                                <ArrowUp v-else class="w-3 h-3" />
                            </span>
                        </div>
                    </th>
                    <th @click="sortBy('source_account')" class="px-6 py-3 font-medium cursor-pointer hover:bg-slate-100 transition-colors">
                        <div class="flex items-center gap-1">
                            Flow Path
                            <span v-if="sortKey === 'source_account'" class="text-slate-400">
                                <ArrowDown v-if="sortDesc" class="w-3 h-3" />
                                <ArrowUp v-else class="w-3 h-3" />
                            </span>
                        </div>
                    </th>
                    <th @click="sortBy('amount')" class="px-6 py-3 font-medium text-right w-32 cursor-pointer hover:bg-slate-100 transition-colors">
                        <div class="flex items-center justify-end gap-1">
                            Amount
                            <span v-if="sortKey === 'amount'" class="text-slate-400">
                                <ArrowDown v-if="sortDesc" class="w-3 h-3" />
                                <ArrowUp v-else class="w-3 h-3" />
                            </span>
                        </div>
                    </th>
                    <th @click="sortBy('reason')" class="px-6 py-3 font-medium w-1/3 cursor-pointer hover:bg-slate-100 transition-colors">
                        <div class="flex items-center gap-1">
                            Context
                            <span v-if="sortKey === 'reason'" class="text-slate-400">
                                <ArrowDown v-if="sortDesc" class="w-3 h-3" />
                                <ArrowUp v-else class="w-3 h-3" />
                            </span>
                        </div>
                    </th>
                </tr>
            </thead>
            <tbody class="divide-y divide-slate-100">
                <tr v-for="(log, idx) in logs" :key="idx" class="hover:bg-slate-50/50 transition-colors">
                    <td class="px-6 py-3 text-slate-500 font-mono text-xs">{{ log.date }}</td>
                    <td class="px-6 py-3">
                        <span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-slate-100 text-slate-700 border border-slate-200 uppercase tracking-wide">
                            {{ log.rule_type }}
                        </span>
                    </td>
                    <td class="px-6 py-3">
                        <div class="flex items-center gap-2 text-slate-700">
                            <span class="font-medium truncate max-w-[120px]" :title="log.source_account">{{ log.source_account }}</span>
                            <ArrowRight class="w-3 h-3 text-slate-300 flex-shrink-0" />
                            <span class="font-medium truncate max-w-[120px]" :title="log.target_account">{{ log.target_account }}</span>
                        </div>
                    </td>
                    <td class="px-6 py-3 text-right font-bold text-slate-900 font-mono">
                        {{ formatAmount(log.amount) }}
                    </td>
                    <td class="px-6 py-3 text-slate-500 text-xs italic truncate max-w-xs" :title="log.reason">
                        {{ log.reason }}
                    </td>
                </tr>
            </tbody>
        </table>
    </div>
</template>
