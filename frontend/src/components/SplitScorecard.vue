<script setup>
import { computed } from 'vue'
import { TrendingUp, TrendingDown, Minus } from 'lucide-vue-next'
import { formatCurrency, formatPercent } from '../utils/format'
const props = defineProps({ label: String, baseline: Number, projected: Number, format: { type: String, default: 'currency' } })
const formatVal = (val) => { if (props.format === 'percent') return formatPercent(val); return formatCurrency(val); }
const getSizeClass = (val) => { const str = formatVal(val); if (str.length > 12) return 'text-sm'; if (str.length > 9) return 'text-lg'; return 'text-2xl'; }
const baselineSize = computed(() => { const str = formatVal(props.baseline); if (str.length > 9) return 'text-base'; return 'text-xl'; })
const delta = computed(() => props.projected - props.baseline)
const isPositive = computed(() => delta.value > 0)
const isZero = computed(() => Math.abs(delta.value) < 1) 
</script>
<template><div class="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden flex h-full"><div class="flex-1 bg-slate-50 border-r border-dashed border-slate-200 p-4 flex flex-col justify-center min-w-0"><span class="text-xs font-bold text-slate-400 uppercase tracking-wider mb-1">Baseline</span><span :class="['font-semibold text-slate-600', baselineSize]" :title="formatVal(baseline)">{{ formatVal(baseline) }}</span></div><div class="flex-1 bg-white p-4 flex flex-col justify-center relative overflow-hidden min-w-0"><span class="text-xs font-bold text-primary uppercase tracking-wider mb-1 flex items-center gap-1">Projected<span v-if="!isZero" :class="isPositive ? 'text-emerald-500' : 'text-rose-500'">({{ isPositive ? '+' : '' }}{{ formatVal(delta) }})</span></span><div class="flex items-center gap-2"><span :class="['font-bold text-slate-900', getSizeClass(projected)]" :title="formatVal(projected)">{{ formatVal(projected) }}</span><div v-if="!isZero"><TrendingUp v-if="isPositive" class="w-5 h-5 text-emerald-500" /><TrendingDown v-else class="w-5 h-5 text-rose-500" /></div><Minus v-else class="w-5 h-5 text-slate-300" /></div></div></div></template>
