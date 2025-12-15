<script setup>
import { computed } from 'vue'
import { formatCurrency, formatPercent } from '../utils/format'

const props = defineProps({
    metrics: Object,        // { net_worth, projected_net_worth, contributions, growth, return }
    baselineMetrics: Object,
    isModelling: Boolean    // Triggers the Purple State
})

const formatPence = (val) => formatCurrency(val)

const getDelta = (current, baseline) => {
    if (!baseline) return null
    const diff = current - baseline
    if (Math.abs(diff) < 100) return null 
    return {
        value: diff,
        label: `${diff > 0 ? '+' : ''}${formatPence(diff)}`
    }
}

const getReturnDelta = (current, baseline) => {
    if (!baseline) return null
    const diff = current - baseline
    if (Math.abs(diff) < 0.1) return null
    return {
        value: diff,
        label: `${diff > 0 ? '+' : ''}${diff.toFixed(1)}%`
    }
}

const cards = computed(() => {
    if (!props.metrics) return []
    const m = props.metrics
    const b = props.baselineMetrics || {}
    const active = props.isModelling

    return [
        { 
            label: 'Current Net Worth', 
            subtitle: '(Excl. Unvested RSUs)',
            value: formatPence(m.current_net_worth),
            delta: active ? getDelta(m.current_net_worth, b.current_net_worth) : null
        },
        { 
            label: 'Projected Net Worth', 
            subtitle: null,
            value: formatPence(m.projected_net_worth),
            delta: active ? getDelta(m.projected_net_worth, b.projected_net_worth) : null
        },
        { 
            label: 'Net Contributions', 
            subtitle: 'Active Savings',
            value: (m.net_contributions > 0 ? '+' : '') + formatPence(m.net_contributions),
            delta: active ? getDelta(m.net_contributions, b.net_contributions) : null
        },
        { 
            label: 'Investment Growth', 
            subtitle: 'Passive Return',
            value: (m.investment_growth > 0 ? '+' : '') + formatPence(m.investment_growth),
            delta: active ? getDelta(m.investment_growth, b.investment_growth) : null
        },
        { 
            label: 'Annual Return (Est.)', 
            subtitle: 'Target: >2.0%',
            value: formatPercent(m.annual_return),
            delta: active ? getReturnDelta(m.annual_return, b.annual_return) : null
        }
    ]
})
</script>

<template>
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        <div v-for="(card, idx) in cards" :key="idx" class="bg-white rounded-xl border border-slate-200 p-4 shadow-sm flex flex-col justify-between h-24">
            <div class="flex flex-col">
                <div class="text-xs font-bold text-slate-400 uppercase tracking-wider mb-1">{{ card.label }}</div>
                <div :class="['text-xl font-bold tracking-tight', isModelling ? 'text-[#635bff]' : 'text-slate-900']">
                    {{ card.value }}
                </div>
            </div>
            
            <div class="mt-auto pt-1">
                <div v-if="card.delta" class="text-xs font-medium text-slate-400 flex items-center gap-1">
                    <span>{{ card.delta.label }}</span>
                    <span class="text-[10px] uppercase opacity-70">vs original</span>
                </div>
                <div v-else-if="card.subtitle" class="text-xs text-slate-400">
                    {{ card.subtitle }}
                </div>
            </div>
        </div>
    </div>
</template>
