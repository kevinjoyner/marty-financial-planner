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

onMounted(() => { if (!store.scenario) store.init() })

const incomeByOwner = computed(() => {
    if (!store.scenario) return []
    return store.scenario.owners.map(owner => ({ id: owner.id, name: owner.name, sources: owner.income_sources })).filter(o => o.sources.length > 0)
})
const accountOptions = computed(() => store.scenario?.accounts.map(a => ({ id: a.id, name: a.name })) || [])
const ownerOptions = computed(() => store.scenario?.owners.map(o => ({ id: o.id, name: o.name })) || [])
const formatPounds = (val) => formatCurrency(val)

const openEdit = (item) => {
    editingItem.value = item
    form.value = { ...item, net_value: item.net_value / 100, salary_sacrifice_value: (item.salary_sacrifice_value || 0) / 100, taxable_benefit_value: (item.taxable_benefit_value || 0) / 100, employer_pension_contribution: (item.employer_pension_contribution || 0) / 100 }
}
const openCreate = () => {
    const defaultOwnerId = store.scenario.owners.length > 0 ? store.scenario.owners[0].id : null;
    const newItem = { id: 'new', name: 'New Income Source', owner_id: defaultOwnerId, net_value: 2000, cadence: 'monthly', start_date: new Date().toISOString().split('T')[0], end_date: null, is_pre_tax: false, salary_sacrifice_value: 0, taxable_benefit_value: 0, employer_pension_contribution: 0 }
    editingItem.value = newItem; form.value = { ...newItem }
}
const save = async () => {
    const payload = { ...form.value };
    if (payload.salary_sacrifice_value) payload.salary_sacrifice_value = Math.round(payload.salary_sacrifice_value * 100);
    if (payload.taxable_benefit_value) payload.taxable_benefit_value = Math.round(payload.taxable_benefit_value * 100);
    if (payload.employer_pension_contribution) payload.employer_pension_contribution = Math.round(payload.employer_pension_contribution * 100);
    const success = await store.saveEntity('income', editingItem.value.id, payload, `Saved ${form.value.name}`)
    if (success) editingItem.value = null
}
const remove = async () => { const success = await store.deleteEntity('income', editingItem.value.id); if (success) editingItem.value = null; }
</script>

<template>
    <div class="flex flex-col h-full max-w-5xl mx-auto w-full pb-24">
        <header class="mb-8 flex justify-between items-center">
            <div><h1 class="text-2xl font-semibold text-slate-900 tracking-tight">Income Sources</h1><p class="text-sm text-slate-500 mt-1">Manage and model your earnings.</p></div>
            <button @click="openCreate" class="flex items-center gap-2 bg-slate-900 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-slate-800 transition-colors shadow-sm"><Plus class="w-4 h-4" /> Add Income</button>
        </header>
        <div v-if="!store.scenario" class="text-slate-400 italic">Loading...</div>
        <div v-else class="space-y-8">
            <div v-for="owner in incomeByOwner" :key="owner.id">
                <h3 class="text-sm font-bold text-slate-400 uppercase tracking-wider mb-3 px-1">{{ owner.name }}</h3>
                <div class="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
                    <table class="w-full text-left text-sm">
                        <thead class="bg-slate-50 border-b border-slate-200 text-slate-500"><tr><th class="px-6 py-3 font-medium w-1/3">Source Name</th><th class="px-6 py-3 font-medium w-1/4">Frequency</th><th class="px-6 py-3 font-medium text-right w-1/4">Value</th><th class="px-6 py-3 font-medium text-center w-16"></th></tr></thead>
                        <tbody class="divide-y divide-slate-100"><tr v-for="inc in owner.sources" :key="inc.id" class="group hover:bg-slate-50/50 transition-colors"><td class="px-6 py-4"><div class="flex items-center gap-3"><div class="w-8 h-8 rounded-full bg-emerald-100 text-emerald-600 flex items-center justify-center flex-shrink-0"><Briefcase class="w-4 h-4" /></div><div class="truncate"><div class="font-medium text-slate-900 truncate" :title="inc.name">{{ inc.name }}</div><div class="text-xs text-slate-400 flex items-center gap-1"><Calendar class="w-3 h-3" /> {{ inc.start_date }} <span v-if="inc.end_date">- {{ inc.end_date }}</span><span v-if="inc.is_pre_tax" class="ml-2 bg-slate-100 px-1 rounded text-slate-500 font-mono text-[10px]">GROSS</span></div></div></div></td><td class="px-6 py-4"><span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-slate-100 text-slate-800 capitalize">{{ inc.cadence }}</span></td><td class="px-6 py-4 text-right font-bold text-slate-700">{{ formatPounds(inc.net_value) }}</td><td class="px-6 py-4 text-center"><button @click="openEdit(inc)" class="p-1.5 text-slate-300 hover:text-primary hover:bg-slate-100 rounded-md transition-all"><Pencil class="w-4 h-4" /></button></td></tr></tbody>
                    </table>
                </div>
            </div>
             <div v-if="incomeByOwner.length === 0" class="text-center py-12 bg-slate-50 rounded-xl border border-dashed border-slate-300"><p class="text-slate-500 mb-4">No income sources defined yet.</p><button @click="openCreate" class="text-primary font-medium hover:underline">Add your first income source</button></div>
        </div>
        <Drawer :isOpen="!!editingItem" :title="editingItem?.name || 'New Income'" @close="editingItem = null" @save="save">
            <div v-if="editingItem" class="space-y-6">
                <div v-if="editingItem.id === 'new'"><label class="block text-sm font-medium text-slate-700 mb-1">Owner</label><select v-model="form.owner_id" class="w-full border border-slate-300 rounded-md px-3 py-2 text-sm bg-white"><option v-for="o in ownerOptions" :key="o.id" :value="o.id">{{ o.name }}</option></select></div>
                <div><label class="block text-sm font-medium text-slate-700 mb-1">Source Name</label><input type="text" v-model="form.name" class="w-full border border-slate-300 rounded-md px-3 py-2 text-sm"></div>
                <div class="p-4 bg-emerald-50 border border-emerald-100 rounded-lg space-y-4">
                    <div class="flex items-center gap-2 mb-2"><input type="checkbox" id="pre_tax" v-model="form.is_pre_tax" class="w-4 h-4 text-emerald-600 rounded border-gray-300 focus:ring-emerald-500"><label for="pre_tax" class="text-sm font-bold text-emerald-800">Pre-Tax (Gross Income)</label></div>
                    <div><div class="flex justify-between items-center mb-1"><label class="block text-sm font-medium text-slate-700">{{ form.is_pre_tax ? 'Gross Amount' : 'Net Amount' }}</label><PinToggle v-if="editingItem.id !== 'new'" :item="{ id: `inc-${editingItem.id}`, realId: editingItem.id, type: 'income', field: 'net_value', label: editingItem.name, value: editingItem.net_value / 100, format: 'currency' }" /></div><div class="relative"><span class="absolute left-3 top-2 text-slate-400">£</span><input type="number" v-model="form.net_value" class="w-full border border-slate-300 rounded-md pl-7 pr-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary"></div></div>
                    <div v-if="form.is_pre_tax" class="space-y-4 pt-2 border-t border-emerald-200/50">
                        <div class="grid grid-cols-2 gap-3">
                            <div><label class="block text-xs font-medium text-slate-600 mb-1">Salary Sacrifice (£)</label><input type="number" v-model="form.salary_sacrifice_value" class="w-full border border-slate-300 rounded-md px-2 py-1.5 text-sm"></div>
                             <div><label class="block text-xs font-medium text-slate-600 mb-1">Into Account</label><select v-model="form.salary_sacrifice_account_id" class="w-full border border-slate-300 rounded-md px-2 py-1.5 text-sm bg-white"><option :value="null">-- None --</option><option v-for="a in accountOptions" :key="a.id" :value="a.id">{{ a.name }}</option></select></div>
                        </div>
                    </div>
                </div>
                <div><div class="flex justify-between items-center mb-1"><label class="block text-sm font-medium text-slate-700">Frequency</label><PinToggle v-if="editingItem.id !== 'new'" :item="{ id: `inc-${editingItem.id}-freq`, realId: editingItem.id, type: 'income', field: 'cadence', label: `${editingItem.name} Freq`, value: editingItem.cadence, inputType: 'select', options: [{id:'monthly',name:'Monthly'},{id:'quarterly',name:'Quarterly'},{id:'annually',name:'Annually'}] }" /></div><select v-model="form.cadence" class="w-full border border-slate-300 rounded-md px-3 py-2 text-sm bg-white"><option value="monthly">Monthly</option><option value="quarterly">Quarterly</option><option value="annually">Annually</option></select></div>
                
                <div class="grid grid-cols-2 gap-4">
                    <div><div class="flex justify-between items-center mb-1"><label class="block text-sm font-medium text-slate-700">Start Date</label><PinToggle v-if="editingItem.id !== 'new'" :item="{ id: `inc-${editingItem.id}-start`, realId: editingItem.id, type: 'income', field: 'start_date', label: `${editingItem.name} Start`, value: editingItem.start_date, inputType: 'date' }" /></div><input type="date" v-model="form.start_date" class="w-full border border-slate-300 rounded-md px-3 py-2 text-sm"></div>
                    <div><div class="flex justify-between items-center mb-1"><label class="block text-sm font-medium text-slate-700">End Date</label><PinToggle v-if="editingItem.id !== 'new'" :item="{ id: `inc-${editingItem.id}-end`, realId: editingItem.id, type: 'income', field: 'end_date', label: `${editingItem.name} End`, value: editingItem.end_date, inputType: 'date' }" /></div><input type="date" v-model="form.end_date" class="w-full border border-slate-300 rounded-md px-3 py-2 text-sm"></div>
                </div>
                
                <div><div class="flex justify-between items-center mb-1"><label class="block text-sm font-medium text-slate-700">Deposit Into</label><PinToggle v-if="editingItem.id !== 'new'" :item="{ id: `inc-${editingItem.id}-dep`, realId: editingItem.id, type: 'income', field: 'account_id', label: `${editingItem.name} Dep`, value: editingItem.account_id, inputType: 'select', options: accountOptions }" /></div><select v-model="form.account_id" class="w-full border border-slate-300 rounded-md px-3 py-2 text-sm bg-white"><option v-for="a in accountOptions" :key="a.id" :value="a.id">{{ a.name }}</option></select></div>
                <div><label class="block text-sm font-medium text-slate-700 mb-1">Notes</label><textarea v-model="form.notes" rows="3" class="w-full border border-slate-300 rounded-md px-3 py-2 text-sm"></textarea></div>
                <div v-if="editingItem.id !== 'new'" class="pt-6 border-t border-slate-100"><button type="button" @click="remove" class="w-full py-2 bg-red-50 text-red-600 hover:bg-red-100 rounded-md font-medium text-sm transition-colors">Delete Income Source</button></div>
            </div>
        </Drawer>
    </div>
</template>
