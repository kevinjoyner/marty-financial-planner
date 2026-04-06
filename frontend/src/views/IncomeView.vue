<script setup>
import { onMounted, computed, ref } from 'vue'
import { useSimulationStore } from '../stores/simulation'
import { Briefcase, Calendar, Pencil, Plus } from 'lucide-vue-next'
import PinToggle from '../components/PinToggle.vue'
import Drawer from '../components/Drawer.vue'
import { formatCurrency } from '../utils/format'

const store = useSimulationStore()
const editingItem = ref(null)
const form = ref({})

onMounted(() => {
    if (!store.scenario) store.init()
})

const incomeByOwner = computed(() => {
    if (!store.scenario) return []
    return store.scenario.owners.map(owner => ({
        id: owner.id, name: owner.name, sources: owner.income_sources
    })).filter(o => o.sources.length > 0)
})

const accountOptions = computed(() => store.scenario?.accounts.map(a => ({ id: a.id, name: a.name })) || [])
const ownerOptions = computed(() => store.scenario?.owners.map(o => ({ id: o.id, name: o.name })) || [])
const formatPounds = (val) => formatCurrency(val)

// Format a number as an integer with thousands separators
const fmt = (val) => Math.round(val || 0).toLocaleString('en-GB')

const openEdit = (item) => {
    editingItem.value = item
    form.value = {
        ...item,
        net_value: item.net_value / 100,
        salary_sacrifice_value: (item.salary_sacrifice_value || 0) / 100,
        taxable_benefit_value: (item.taxable_benefit_value || 0) / 100,
        employer_pension_contribution: (item.employer_pension_contribution || 0) / 100,
        // Percent fields — stored as plain percentages (e.g. 35.0 = 35%), no conversion needed
        salary_sacrifice_percent: item.salary_sacrifice_percent ?? null,
        employer_match_percent: item.employer_match_percent ?? null,
        employer_ni_supplement: item.employer_ni_supplement ?? false,
        // employer_ni_rate stored as plain percentage; null means "use backend default of 15%"
        employer_ni_rate: item.employer_ni_rate ?? null
    }
}

const openCreate = () => {
    const defaultOwnerId = store.scenario.owners.length > 0 ? store.scenario.owners[0].id : null
    const newItem = {
        id: 'new',
        name: 'New Income Source',
        owner_id: defaultOwnerId,
        net_value: 2000,
        cadence: 'monthly',
        start_date: new Date().toISOString().split('T')[0],
        end_date: null,
        is_pre_tax: false,
        salary_sacrifice_value: 0,
        taxable_benefit_value: 0,
        employer_pension_contribution: 0,
        salary_sacrifice_account_id: null,
        salary_sacrifice_percent: null,
        employer_match_percent: null,
        employer_ni_supplement: false,
        employer_ni_rate: null
    }
    editingItem.value = newItem
    form.value = { ...newItem }
}

const save = async () => {
    const payload = { ...form.value }
    // salary_sacrifice_percent, employer_match_percent, employer_ni_rate are plain floats —
    // the store's saveEntity converts named pence fields; these pass through untouched.
    const success = await store.saveEntity('income', editingItem.value.id, payload, `Saved ${form.value.name}`)
    if (success) editingItem.value = null
}

const remove = async () => {
    const success = await store.deleteEntity('income', editingItem.value.id)
    if (success) editingItem.value = null
}

// --- Pension input mode ---
const isPercentMode = computed(() =>
    form.value.salary_sacrifice_percent !== null && form.value.salary_sacrifice_percent !== undefined
)

const setPensionInputMode = (mode) => {
    if (mode === 'percent') {
        if (form.value.salary_sacrifice_percent === null || form.value.salary_sacrifice_percent === undefined) {
            form.value.salary_sacrifice_percent = 0
        }
        if (form.value.employer_match_percent === null || form.value.employer_match_percent === undefined) {
            form.value.employer_match_percent = 0
        }
    } else {
        form.value.salary_sacrifice_percent = null
        form.value.employer_match_percent = null
    }
}

// --- Live pension contribution calculator ---
const annualFactor = computed(() => {
    switch (form.value.cadence) {
        case 'annually': return 1
        case 'quarterly': return 4
        default: return 12
    }
})

const pensionCalc = computed(() => {
    if (!form.value.is_pre_tax) return null

    const af = annualFactor.value
    const grossMonthly = Number(form.value.net_value) || 0
    const annualGross = grossMonthly * af

    let sacrifice, employerMatch
    if (isPercentMode.value) {
        const sacPct = Number(form.value.salary_sacrifice_percent) || 0
        const matchPct = Math.min(sacPct, Number(form.value.employer_match_percent) || 0)
        sacrifice = grossMonthly * sacPct / 100
        employerMatch = grossMonthly * matchPct / 100
    } else {
        sacrifice = Number(form.value.salary_sacrifice_value) || 0
        employerMatch = Number(form.value.employer_pension_contribution) || 0
    }

    const niRatePct = Number(form.value.employer_ni_rate) || 15
    const niSupp = form.value.employer_ni_supplement ? sacrifice * niRatePct / 100 : 0

    const totalMonthly = sacrifice + employerMatch + niSupp
    const totalAnnual = totalMonthly * af
    const sacrificeAnnual = sacrifice * af
    const employerAnnual = (employerMatch + niSupp) * af
    const postSacrifice = annualGross - sacrificeAnnual

    // Annual Allowance
    const STANDARD_AA = 60000
    const aaPercent = Math.min(100, Math.round((totalAnnual / STANDARD_AA) * 100))
    const exceedsAA = totalAnnual > STANDARD_AA
    const aaExcess = Math.max(0, totalAnnual - STANDARD_AA)

    // Personal Allowance recovery note
    let paNote = null
    if (annualGross > 100000) {
        if (postSacrifice < 100000) {
            const paRestored = Math.min(12570, Math.round((125140 - postSacrifice) / 2))
            const saving = Math.round(paRestored * 0.4)
            paNote = {
                type: 'full',
                text: `Sacrifice takes income below £100k — full Personal Allowance restored, saving ~£${fmt(saving)}/yr`
            }
        } else if (postSacrifice < 125140) {
            const paRestored = Math.round(Math.min(12570, (annualGross - postSacrifice) / 2))
            const saving = Math.round(paRestored * 0.4)
            paNote = {
                type: 'partial',
                text: `Recovers ~£${fmt(paRestored)} of Personal Allowance (~£${fmt(saving)}/yr saved). Sacrifice more to fully escape the 60% zone.`
            }
        }
    }

    // Approximate marginal tax+NI saving on sacrifice
    let marginalRate
    if (annualGross > 125140) marginalRate = 47         // 45% IT + 2% NI
    else if (annualGross > 100000) marginalRate = 62    // 60% effective (PA taper zone)
    else if (annualGross > 50270) marginalRate = 42     // 40% IT + 2% NI
    else if (annualGross > 12570) marginalRate = 28     // 20% IT + 8% NI
    else marginalRate = 0
    const taxSaving = Math.round(sacrificeAnnual * marginalRate / 100)

    return {
        sacrifice, employerMatch, niSupp,
        totalMonthly, totalAnnual,
        sacrificeAnnual, employerAnnual,
        annualGross, postSacrifice,
        aaPercent, exceedsAA, aaExcess,
        paNote, taxSaving, marginalRate,
        showPanel: totalMonthly > 0 || sacrifice > 0
    }
})
</script>

<template>
    <div class="flex flex-col h-full max-w-5xl mx-auto w-full pb-24">
        <header class="mb-8 flex justify-between items-center">
            <div>
                <h1 class="text-2xl font-semibold text-slate-900 tracking-tight">Income Sources</h1>
                <p class="text-sm text-slate-500 mt-1">Manage and model your earnings.</p>
            </div>
            <button @click="openCreate" class="flex items-center gap-2 bg-slate-900 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-slate-800 transition-colors shadow-sm">
                <Plus class="w-4 h-4" /> Add Income
            </button>
        </header>

        <div v-if="!store.scenario" class="text-slate-400 italic">Loading...</div>

        <div v-else class="space-y-8">
            <div v-for="owner in incomeByOwner" :key="owner.id">
                <h3 class="text-sm font-bold text-slate-400 uppercase tracking-wider mb-3 px-1">{{ owner.name }}</h3>
                <div class="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
                    <table class="w-full text-left text-sm">
                        <thead class="bg-slate-50 border-b border-slate-200 text-slate-500">
                            <tr>
                                <th class="px-6 py-3 font-medium w-1/3">Source Name</th>
                                <th class="px-6 py-3 font-medium w-1/4">Frequency</th>
                                <th class="px-6 py-3 font-medium text-right w-1/4">Value</th>
                                <th class="px-6 py-3 font-medium text-center w-16"></th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-slate-100">
                            <tr v-for="inc in owner.sources" :key="inc.id" class="group hover:bg-slate-50/50 transition-colors">
                                <td class="px-6 py-4">
                                    <div class="flex items-center gap-3">
                                        <div class="w-8 h-8 rounded-full bg-emerald-100 text-emerald-600 flex items-center justify-center flex-shrink-0">
                                            <Briefcase class="w-4 h-4" />
                                        </div>
                                        <div class="truncate">
                                            <div class="font-medium text-slate-900 truncate" :title="inc.name">{{ inc.name }}</div>
                                            <div class="text-xs text-slate-400 flex items-center gap-1 flex-wrap">
                                                <Calendar class="w-3 h-3" /> {{ inc.start_date }}
                                                <span v-if="inc.end_date" class="text-slate-300 mx-1">→</span>
                                                <span v-if="inc.end_date">{{ inc.end_date }}</span>
                                                <span v-if="inc.is_pre_tax" class="ml-2 bg-slate-100 px-1 rounded text-slate-500 font-mono text-[10px]">GROSS</span>
                                                <span v-if="inc.salary_sacrifice_percent != null" class="bg-emerald-100 text-emerald-700 px-1 rounded font-mono text-[10px]">{{ inc.salary_sacrifice_percent }}% sacrifice</span>
                                            </div>
                                        </div>
                                    </div>
                                </td>
                                <td class="px-6 py-4"><span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-slate-100 text-slate-800 capitalize">{{ inc.cadence }}</span></td>
                                <td class="px-6 py-4 text-right font-bold text-slate-700">{{ formatPounds(inc.net_value) }}</td>
                                <td class="px-6 py-4 text-center">
                                    <button @click="openEdit(inc)" class="p-1.5 text-slate-300 hover:text-primary hover:bg-slate-100 rounded-md transition-all"><Pencil class="w-4 h-4" /></button>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
            <div v-if="incomeByOwner.length === 0" class="text-center py-12 bg-slate-50 rounded-xl border border-dashed border-slate-300">
                <p class="text-slate-500 mb-4">No income sources defined yet.</p>
                <button @click="openCreate" class="text-primary font-medium hover:underline">Add your first income source</button>
            </div>
        </div>

        <Drawer :isOpen="!!editingItem" :title="editingItem?.name || 'New Income'" @close="editingItem = null" @save="save">
            <div v-if="editingItem" class="space-y-6">

                <!-- Owner selector (create only) -->
                <div v-if="editingItem.id === 'new'">
                    <label class="block text-sm font-medium text-slate-700 mb-1">Owner</label>
                    <select v-model="form.owner_id" class="w-full border border-slate-300 rounded-md px-3 py-2 text-sm bg-white">
                        <option v-for="o in ownerOptions" :key="o.id" :value="o.id">{{ o.name }}</option>
                    </select>
                </div>

                <!-- Name -->
                <div>
                    <label class="block text-sm font-medium text-slate-700 mb-1">Source Name</label>
                    <input type="text" v-model="form.name" class="w-full border border-slate-300 rounded-md px-3 py-2 text-sm">
                </div>

                <!-- Pre-tax section -->
                <div class="p-4 bg-emerald-50 border border-emerald-100 rounded-lg space-y-4">

                    <!-- Pre-tax toggle -->
                    <div class="flex items-center gap-2 mb-2">
                        <input type="checkbox" id="pre_tax" v-model="form.is_pre_tax" class="w-4 h-4 text-emerald-600 rounded border-gray-300 focus:ring-emerald-500">
                        <label for="pre_tax" class="text-sm font-bold text-emerald-800">Pre-Tax (Gross Income)</label>
                    </div>

                    <!-- Gross/Net amount -->
                    <div>
                        <div class="flex justify-between items-center mb-1">
                            <label class="block text-sm font-medium text-slate-700">{{ form.is_pre_tax ? 'Gross Amount' : 'Net Amount' }}</label>
                            <PinToggle v-if="editingItem.id !== 'new'" :item="{ id: `inc-${editingItem.id}`, realId: editingItem.id, type: 'income', field: 'net_value', label: editingItem.name, value: editingItem.net_value / 100, format: 'currency' }" />
                        </div>
                        <div class="relative">
                            <span class="absolute left-3 top-2 text-slate-400">£</span>
                            <input type="number" v-model="form.net_value" class="w-full border border-slate-300 rounded-md pl-7 pr-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary">
                        </div>
                    </div>

                    <!-- Salary sacrifice section (only when pre-tax) -->
                    <div v-if="form.is_pre_tax" class="space-y-4 pt-2 border-t border-emerald-200/50">

                        <!-- Mode toggle -->
                        <div class="flex items-center gap-3">
                            <span class="text-xs font-medium text-slate-600 shrink-0">Pension contributions:</span>
                            <div class="flex rounded-md overflow-hidden border border-slate-300 text-xs shrink-0">
                                <button
                                    type="button"
                                    @click="setPensionInputMode('fixed')"
                                    :class="['px-3 py-1.5 font-medium transition-colors', !isPercentMode ? 'bg-slate-900 text-white' : 'bg-white text-slate-600 hover:bg-slate-50']"
                                >Fixed £</button>
                                <button
                                    type="button"
                                    @click="setPensionInputMode('percent')"
                                    :class="['px-3 py-1.5 font-medium transition-colors border-l border-slate-300', isPercentMode ? 'bg-slate-900 text-white' : 'bg-white text-slate-600 hover:bg-slate-50']"
                                >% of Salary</button>
                            </div>
                        </div>

                        <!-- FIXED MODE -->
                        <template v-if="!isPercentMode">
                            <div class="grid grid-cols-2 gap-3">
                                <div>
                                    <div class="flex justify-between items-center mb-1">
                                        <label class="block text-xs font-medium text-slate-600">Salary Sacrifice (£)</label>
                                        <PinToggle v-if="editingItem.id !== 'new'" :item="{ id: `inc-${editingItem.id}-sac`, realId: editingItem.id, type: 'income', field: 'salary_sacrifice_value', label: `${editingItem.name} Sacrifice`, value: (editingItem.salary_sacrifice_value || 0) / 100, format: 'currency' }" />
                                    </div>
                                    <input type="number" v-model="form.salary_sacrifice_value" class="w-full border border-slate-300 rounded-md px-2 py-1.5 text-sm">
                                </div>
                                <div>
                                    <div class="flex justify-between items-center mb-1">
                                        <label class="block text-xs font-medium text-slate-600">Into Account</label>
                                        <PinToggle v-if="editingItem.id !== 'new'" :item="{ id: `inc-${editingItem.id}-sac-acc`, realId: editingItem.id, type: 'income', field: 'salary_sacrifice_account_id', label: `${editingItem.name} Sac. Acc`, value: editingItem.salary_sacrifice_account_id, inputType: 'select', options: accountOptions }" />
                                    </div>
                                    <select v-model="form.salary_sacrifice_account_id" class="w-full border border-slate-300 rounded-md px-2 py-1.5 text-sm bg-white">
                                        <option :value="null">-- None --</option>
                                        <option v-for="a in accountOptions" :key="a.id" :value="a.id">{{ a.name }}</option>
                                    </select>
                                </div>
                            </div>

                            <div>
                                <div class="flex justify-between items-center mb-1">
                                    <label class="block text-xs font-medium text-slate-600">Employer Contribution (£)</label>
                                    <PinToggle v-if="editingItem.id !== 'new'" :item="{ id: `inc-${editingItem.id}-emp`, realId: editingItem.id, type: 'income', field: 'employer_pension_contribution', label: `${editingItem.name} Employer Contrib`, value: (editingItem.employer_pension_contribution || 0) / 100, format: 'currency' }" />
                                </div>
                                <input type="number" v-model="form.employer_pension_contribution" class="w-full border border-slate-300 rounded-md px-2 py-1.5 text-sm">
                                <p class="text-[10px] text-slate-400 mt-1">Added to pension tax-free.</p>
                            </div>
                        </template>

                        <!-- % MODE -->
                        <template v-else>
                            <div class="grid grid-cols-2 gap-3">
                                <div>
                                    <div class="flex justify-between items-center mb-1">
                                        <label class="block text-xs font-medium text-slate-600">Your Sacrifice (%)</label>
                                        <PinToggle v-if="editingItem.id !== 'new'" :item="{ id: `inc-${editingItem.id}-sac-pct`, realId: editingItem.id, type: 'income', field: 'salary_sacrifice_percent', label: `${editingItem.name} Sacrifice %`, value: editingItem.salary_sacrifice_percent || 0, format: 'percent' }" />
                                    </div>
                                    <div class="relative">
                                        <input type="number" v-model="form.salary_sacrifice_percent" min="0" max="100" step="0.5" class="w-full border border-slate-300 rounded-md px-2 pr-8 py-1.5 text-sm">
                                        <span class="absolute right-2.5 top-2 text-slate-400 text-xs">%</span>
                                    </div>
                                </div>
                                <div>
                                    <div class="flex justify-between items-center mb-1">
                                        <label class="block text-xs font-medium text-slate-600">Into Account</label>
                                        <PinToggle v-if="editingItem.id !== 'new'" :item="{ id: `inc-${editingItem.id}-sac-acc`, realId: editingItem.id, type: 'income', field: 'salary_sacrifice_account_id', label: `${editingItem.name} Sac. Acc`, value: editingItem.salary_sacrifice_account_id, inputType: 'select', options: accountOptions }" />
                                    </div>
                                    <select v-model="form.salary_sacrifice_account_id" class="w-full border border-slate-300 rounded-md px-2 py-1.5 text-sm bg-white">
                                        <option :value="null">-- None --</option>
                                        <option v-for="a in accountOptions" :key="a.id" :value="a.id">{{ a.name }}</option>
                                    </select>
                                </div>
                            </div>

                            <div class="grid grid-cols-2 gap-3">
                                <div>
                                    <div class="flex justify-between items-center mb-1">
                                        <label class="block text-xs font-medium text-slate-600">Employer Match Cap (%)</label>
                                        <PinToggle v-if="editingItem.id !== 'new'" :item="{ id: `inc-${editingItem.id}-emp-pct`, realId: editingItem.id, type: 'income', field: 'employer_match_percent', label: `${editingItem.name} Employer Match %`, value: editingItem.employer_match_percent || 0, format: 'percent' }" />
                                    </div>
                                    <div class="relative">
                                        <input type="number" v-model="form.employer_match_percent" min="0" max="100" step="0.5" class="w-full border border-slate-300 rounded-md px-2 pr-8 py-1.5 text-sm">
                                        <span class="absolute right-2.5 top-2 text-slate-400 text-xs">%</span>
                                    </div>
                                    <p class="text-[10px] text-slate-400 mt-1">Employer matches up to this % of salary.</p>
                                </div>
                                <div class="flex flex-col justify-between">
                                    <label class="block text-xs font-medium text-slate-600 mb-1">Employer NI Supplement</label>
                                    <div class="flex items-center gap-3 py-2">
                                        <button
                                            type="button"
                                            @click="form.employer_ni_supplement = !form.employer_ni_supplement"
                                            :class="['relative inline-flex h-5 w-9 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none', form.employer_ni_supplement ? 'bg-emerald-500' : 'bg-slate-200']"
                                        >
                                            <span :class="['pointer-events-none inline-block h-4 w-4 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out', form.employer_ni_supplement ? 'translate-x-4' : 'translate-x-0']"></span>
                                        </button>
                                        <span class="text-xs text-slate-600">{{ form.employer_ni_supplement ? 'On' : 'Off' }}</span>
                                    </div>
                                    <p class="text-[10px] text-slate-400">Employer routes their NI saving into your pension.</p>
                                </div>
                            </div>

                            <!-- NI rate (shown when supplement enabled) -->
                            <div v-if="form.employer_ni_supplement" class="bg-emerald-100/60 rounded-md p-3">
                                <label class="block text-xs font-medium text-slate-600 mb-1">Employer NI Rate (%)</label>
                                <div class="relative w-32">
                                    <input type="number" v-model="form.employer_ni_rate" min="0" max="30" step="0.1" placeholder="15" class="w-full border border-slate-300 rounded-md px-2 pr-8 py-1.5 text-sm bg-white">
                                    <span class="absolute right-2.5 top-2 text-slate-400 text-xs">%</span>
                                </div>
                                <p class="text-[10px] text-slate-400 mt-1">Employer NI rate on salary sacrifice saving. Default: 15% (April 2025+).</p>
                            </div>
                        </template>

                        <!-- Taxable Benefits (BiK) — always shown in pre-tax mode -->
                        <div>
                            <div class="flex justify-between items-center mb-1">
                                <label class="block text-xs font-medium text-slate-600">Taxable Benefits / BiK (£)</label>
                                <PinToggle v-if="editingItem.id !== 'new'" :item="{ id: `inc-${editingItem.id}-bik`, realId: editingItem.id, type: 'income', field: 'taxable_benefit_value', label: `${editingItem.name} BiK`, value: (editingItem.taxable_benefit_value || 0) / 100, format: 'currency' }" />
                            </div>
                            <input type="number" v-model="form.taxable_benefit_value" class="w-full border border-slate-300 rounded-md px-2 py-1.5 text-sm">
                            <p class="text-[10px] text-slate-400 mt-1">Added to taxable income, not paid as cash.</p>
                        </div>

                        <!-- Live pension contribution calculator -->
                        <div v-if="pensionCalc && pensionCalc.showPanel" class="rounded-lg bg-slate-900 text-white p-4 space-y-2.5">
                            <div class="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-3">Pension Contribution Summary</div>

                            <div class="flex justify-between text-xs">
                                <span class="text-slate-400">
                                    Your sacrifice<span v-if="isPercentMode"> ({{ form.salary_sacrifice_percent }}%)</span>
                                </span>
                                <span class="font-mono">
                                    £{{ fmt(pensionCalc.sacrifice) }}/mo
                                    <span class="text-slate-400"> → £{{ fmt(pensionCalc.sacrificeAnnual) }}/yr</span>
                                </span>
                            </div>

                            <div v-if="pensionCalc.employerMatch > 0" class="flex justify-between text-xs">
                                <span class="text-slate-400">
                                    Employer match<span v-if="isPercentMode"> ({{ Math.min(form.salary_sacrifice_percent || 0, form.employer_match_percent || 0) }}%)</span>
                                </span>
                                <span class="font-mono">£{{ fmt(pensionCalc.employerMatch) }}/mo</span>
                            </div>

                            <div v-if="form.employer_ni_supplement && pensionCalc.niSupp > 0" class="flex justify-between text-xs">
                                <span class="text-slate-400">Employer NI supplement ({{ form.employer_ni_rate || 15 }}%)</span>
                                <span class="font-mono">£{{ fmt(pensionCalc.niSupp) }}/mo</span>
                            </div>

                            <div class="pt-2 border-t border-slate-700 flex justify-between text-xs font-bold">
                                <span>Total pension</span>
                                <span class="text-emerald-400 font-mono">£{{ fmt(pensionCalc.totalAnnual) }}/yr</span>
                            </div>

                            <!-- Annual Allowance bar -->
                            <div class="space-y-1 pt-1">
                                <div class="flex justify-between text-[10px]">
                                    <span class="text-slate-400">Annual Allowance (£60,000)</span>
                                    <span :class="pensionCalc.exceedsAA ? 'text-amber-400 font-bold' : 'text-slate-400'">
                                        {{ pensionCalc.aaPercent }}% used
                                    </span>
                                </div>
                                <div class="h-1.5 bg-slate-700 rounded-full overflow-hidden">
                                    <div
                                        class="h-full rounded-full transition-all duration-300"
                                        :class="pensionCalc.exceedsAA ? 'bg-amber-400' : pensionCalc.aaPercent > 80 ? 'bg-yellow-400' : 'bg-emerald-400'"
                                        :style="{ width: pensionCalc.aaPercent + '%' }"
                                    ></div>
                                </div>
                                <div v-if="pensionCalc.exceedsAA" class="text-amber-400 text-[10px] font-medium leading-snug">
                                    Exceeds AA by £{{ fmt(pensionCalc.aaExcess) }} — carry-forward from prior years may cover this.
                                </div>
                            </div>

                            <!-- Tax saving estimate -->
                            <div v-if="pensionCalc.taxSaving > 0" class="flex justify-between text-[10px]">
                                <span class="text-slate-400">Approx. tax/NI saving (~{{ pensionCalc.marginalRate }}% marginal)</span>
                                <span class="text-emerald-400 font-mono">~£{{ fmt(pensionCalc.taxSaving) }}/yr</span>
                            </div>

                            <!-- Personal Allowance note -->
                            <div v-if="pensionCalc.paNote" class="mt-1 p-2.5 rounded-md text-[10px] leading-snug" :class="pensionCalc.paNote.type === 'full' ? 'bg-indigo-900/60 text-indigo-200' : 'bg-amber-900/40 text-amber-200'">
                                <span class="font-bold">PA:</span> {{ pensionCalc.paNote.text }}
                            </div>
                        </div>

                    </div><!-- end pre-tax inner -->
                </div><!-- end pre-tax card -->

                <!-- Frequency and Start Date -->
                <div class="grid grid-cols-2 gap-4">
                    <div>
                        <div class="flex justify-between items-center mb-1">
                            <label class="block text-sm font-medium text-slate-700">Frequency</label>
                            <PinToggle v-if="editingItem.id !== 'new'" :item="{ id: `inc-${editingItem.id}-freq`, realId: editingItem.id, type: 'income', field: 'cadence', label: `${editingItem.name} Freq`, value: editingItem.cadence, inputType: 'select', options: [{id:'monthly',name:'Monthly'},{id:'quarterly',name:'Quarterly'},{id:'annually',name:'Annually'}] }" />
                        </div>
                        <select v-model="form.cadence" class="w-full border border-slate-300 rounded-md px-3 py-2 text-sm bg-white">
                            <option value="monthly">Monthly</option>
                            <option value="quarterly">Quarterly</option>
                            <option value="annually">Annually</option>
                        </select>
                    </div>
                    <div>
                        <div class="flex justify-between items-center mb-1">
                            <label class="block text-sm font-medium text-slate-700">Start Date</label>
                            <PinToggle v-if="editingItem.id !== 'new'" :item="{ id: `inc-${editingItem.id}-start`, realId: editingItem.id, type: 'income', field: 'start_date', label: `${editingItem.name} Start`, value: editingItem.start_date, inputType: 'date' }" />
                        </div>
                        <input type="date" v-model="form.start_date" class="w-full border border-slate-300 rounded-md px-3 py-2 text-sm">
                    </div>
                </div>

                <!-- End Date -->
                <div>
                    <div class="flex justify-between items-center mb-1">
                        <label class="block text-sm font-medium text-slate-700">End Date (Optional)</label>
                        <PinToggle v-if="editingItem.id !== 'new'" :item="{ id: `inc-${editingItem.id}-end`, realId: editingItem.id, type: 'income', field: 'end_date', label: `${editingItem.name} End`, value: editingItem.end_date, inputType: 'date' }" />
                    </div>
                    <input type="date" v-model="form.end_date" class="w-full border border-slate-300 rounded-md px-3 py-2 text-sm">
                </div>

                <!-- Deposit Into -->
                <div>
                    <div class="flex justify-between items-center mb-1">
                        <label class="block text-sm font-medium text-slate-700">Deposit Into</label>
                        <PinToggle v-if="editingItem.id !== 'new'" :item="{ id: `inc-${editingItem.id}-dep`, realId: editingItem.id, type: 'income', field: 'account_id', label: `${editingItem.name} Dep`, value: editingItem.account_id, inputType: 'select', options: accountOptions }" />
                    </div>
                    <select v-model="form.account_id" class="w-full border border-slate-300 rounded-md px-3 py-2 text-sm bg-white">
                        <option v-for="a in accountOptions" :key="a.id" :value="a.id">{{ a.name }}</option>
                    </select>
                </div>

                <!-- Notes -->
                <div>
                    <label class="block text-sm font-medium text-slate-700 mb-1">Notes</label>
                    <textarea v-model="form.notes" rows="3" class="w-full border border-slate-300 rounded-md px-3 py-2 text-sm"></textarea>
                </div>

                <!-- Delete -->
                <div v-if="editingItem.id !== 'new'" class="pt-6 border-t border-slate-100">
                    <button type="button" @click="remove" class="w-full py-2 bg-red-50 text-red-600 hover:bg-red-100 rounded-md font-medium text-sm transition-colors">Delete Income Source</button>
                </div>

            </div>
        </Drawer>
    </div>
</template>
