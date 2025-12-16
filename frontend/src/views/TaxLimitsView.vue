<script setup>
import { onMounted, ref } from 'vue'
import { useSimulationStore } from '../stores/simulation'
import { Scale, Users, Pencil, Check, Plus } from 'lucide-vue-next'
import Drawer from '../components/Drawer.vue'
import PinToggle from '../components/PinToggle.vue'
import { formatCurrency } from '../utils/format'

const store = useSimulationStore()
const editingItem = ref(null)
const form = ref({})

onMounted(() => {
    if (!store.scenario) store.init()
})

const formatPounds = (val) => formatCurrency(val)

const openEdit = (item, type) => {
    editingItem.value = { ...item, type }
    if (type === 'tax_limit') {
        form.value = { 
            ...item, 
            amount: item.amount / 100,
            wrappers: item.wrappers ? [...item.wrappers] : [],
            account_types: item.account_types ? [...item.account_types] : []
        }
    } else {
        form.value = { ...item }
    }
}

const openCreatePerson = () => {
    const newOwner = { id: 'new', name: 'New Person', type: 'owner' }
    editingItem.value = newOwner;
    form.value = { ...newOwner };
}

const openCreateLimit = () => {
    const newLimit = { 
        id: 'new', 
        name: 'New Allowance', 
        amount: 20000, // Default £20k
        wrappers: [],
        account_types: [],
        type: 'tax_limit',
        start_date: new Date().toISOString().split('T')[0]
    }
    editingItem.value = newLimit;
    form.value = { ...newLimit };
}

const save = async () => {
    const type = editingItem.value.type
    await store.saveEntity(type, editingItem.value.id, form.value, `Saved ${form.value.name}`)
    editingItem.value = null
}

const remove = async () => {
    const success = await store.deleteEntity(editingItem.value.type, editingItem.value.id);
    if (success) editingItem.value = null;
}

const WRAPPERS = ["ISA", "Lifetime ISA", "Pension", "General"]
const ACCT_TYPES = ["Cash", "Investment", "Property", "Mortgage", "Loan", "RSU Grant"]
</script>

<template>
    <div class="flex flex-col h-full max-w-5xl mx-auto w-full pb-24">
        <header class="mb-8"><h1 class="text-2xl font-semibold text-slate-900 tracking-tight">Tax & People</h1><p class="text-sm text-slate-500 mt-1">Manage household members and fiscal limits.</p></header>
        <div v-if="!store.scenario" class="text-slate-400 italic">Loading...</div>
        <div v-else class="space-y-10">
            <div>
                <div class="flex justify-between items-center mb-3">
                    <h3 class="text-sm font-bold text-slate-400 uppercase tracking-wider px-1">Household</h3>
                    <button @click="openCreatePerson" class="text-xs font-bold text-primary hover:text-primary-dark flex items-center gap-1"><Plus class="w-3 h-3"/> Add Person</button>
                </div>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div v-for="owner in store.scenario.owners" :key="owner.id" class="bg-white border border-slate-200 rounded-xl p-6 shadow-sm flex items-center justify-between group hover:border-blue-300 transition-colors">
                        <div class="flex items-center gap-4"><div class="w-12 h-12 rounded-full bg-blue-50 text-blue-600 flex items-center justify-center"><Users class="w-6 h-6" /></div><div><h3 class="text-lg font-semibold text-slate-900">{{ owner.name }}</h3><p class="text-xs text-slate-400">Tax Entity</p></div></div>
                        <button @click="openEdit(owner, 'owner')" class="p-2 text-slate-300 hover:text-blue-600 hover:bg-blue-50 rounded-full transition-all"><Pencil class="w-4 h-4" /></button>
                    </div>
                </div>
            </div>
            <div>
                <div class="flex justify-between items-center mb-3">
                    <h3 class="text-sm font-bold text-indigo-600 uppercase tracking-wider px-1">Fiscal Limits (Tax Year)</h3>
                    <button @click="openCreateLimit" class="text-xs font-bold text-indigo-600 hover:text-indigo-800 flex items-center gap-1"><Plus class="w-3 h-3"/> Add Limit</button>
                </div>
                <div class="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden"><table class="w-full text-left text-sm"><thead class="bg-slate-50 border-b border-slate-200 text-slate-500"><tr><th class="px-6 py-3 font-medium">Allowance Name</th><th class="px-6 py-3 font-medium">Tax Wrapper</th><th class="px-6 py-3 font-medium">Account Type</th><th class="px-6 py-3 font-medium text-right">Limit</th><th class="px-6 py-3 font-medium text-center w-16"></th></tr></thead><tbody class="divide-y divide-slate-100">
                    <tr v-for="limit in store.scenario.tax_limits" :key="limit.id" class="group hover:bg-slate-50/50 transition-colors">
                        <td class="px-6 py-4 font-medium text-slate-900"><div class="flex items-center gap-3"><Scale class="w-4 h-4 text-indigo-400" />{{ limit.name }}</div></td>
                        <td class="px-6 py-4 text-slate-500 text-xs"><div class="flex gap-1 flex-wrap"><span v-for="w in limit.wrappers" :key="w" class="bg-slate-100 px-1.5 py-0.5 rounded">{{ w }}</span></div></td>
                        <td class="px-6 py-4 text-slate-500 text-xs"><div class="flex gap-1 flex-wrap"><span v-if="!limit.account_types || limit.account_types.length===0" class="text-slate-400">All</span><span v-else v-for="t in limit.account_types" :key="t" class="bg-slate-100 px-1.5 py-0.5 rounded">{{ t }}</span></div></td>
                        <td class="px-6 py-4 text-right font-bold text-slate-700">{{ formatPounds(limit.amount) }}</td>
                        <td class="px-6 py-4 text-center"><button @click="openEdit(limit, 'tax_limit')" class="p-1.5 text-slate-300 hover:text-primary hover:bg-slate-100 rounded-md transition-all"><Pencil class="w-4 h-4" /></button></td>
                    </tr>
                </tbody></table></div>
            </div>
        </div>
        <Drawer :isOpen="!!editingItem" :title="editingItem?.id === 'new' ? (editingItem.type === 'owner' ? 'New Person' : 'New Limit') : (editingItem?.type === 'owner' ? 'Edit Person' : 'Edit Tax Limit')" @close="editingItem = null" @save="save">
            <div v-if="editingItem" class="space-y-4">
                <div v-if="editingItem.type === 'owner'"><div><label class="block text-sm font-medium text-slate-700 mb-1">Name</label><input type="text" v-model="form.name" class="w-full border border-slate-300 rounded-md px-3 py-2 text-sm"></div></div>
                <div v-else>
                    <div><label class="block text-sm font-medium text-slate-700 mb-1">Allowance Name</label><input type="text" v-model="form.name" class="w-full border border-slate-300 rounded-md px-3 py-2 text-sm"></div>
                    <div>
                        <div class="flex justify-between items-center mb-1"><label class="block text-sm font-medium text-slate-700">Annual Limit</label><PinToggle v-if="editingItem.id !== 'new'" :item="{ id: `tax-${editingItem.id}`, realId: editingItem.id, type: 'tax_limit', field: 'amount', label: editingItem.name, value: editingItem.amount / 100, format: 'currency' }" /></div>
                        <div class="relative"><span class="absolute left-3 top-2 text-slate-400">£</span><input type="number" v-model="form.amount" class="w-full border border-slate-300 rounded-md pl-7 pr-3 py-2 text-sm"></div>
                    </div>
                    
                    <div><label class="block text-sm font-medium text-slate-700 mb-1">Start Date</label><input type="date" v-model="form.start_date" class="w-full border border-slate-300 rounded-md px-3 py-2 text-sm"></div>

                    <div class="pt-2 border-t border-slate-100">
                        <label class="block text-xs font-bold text-slate-500 uppercase mb-2">Tax Wrappers</label>
                        <div class="grid grid-cols-2 gap-2">
                            <div v-for="w in WRAPPERS" :key="w" class="flex items-center gap-2">
                                <input type="checkbox" :value="w" v-model="form.wrappers" class="w-4 h-4 text-primary rounded">
                                <span class="text-sm text-slate-700">{{ w }}</span>
                            </div>
                        </div>
                    </div>
                    
                    <div class="pt-2 border-t border-slate-100">
                        <label class="block text-xs font-bold text-slate-500 uppercase mb-2">Account Types (Optional)</label>
                        <div class="grid grid-cols-2 gap-2">
                            <div v-for="t in ACCT_TYPES" :key="t" class="flex items-center gap-2">
                                <input type="checkbox" :value="t" v-model="form.account_types" class="w-4 h-4 text-primary rounded">
                                <span class="text-sm text-slate-700">{{ t }}</span>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div v-if="editingItem.id !== 'new'" class="pt-6 border-t border-slate-100">
                    <button type="button" @click="remove" class="w-full py-2 bg-red-50 text-red-600 hover:bg-red-100 rounded-md font-medium text-sm transition-colors">Delete {{ editingItem.type === 'owner' ? 'Person' : 'Limit' }}</button>
                </div>
            </div>
        </Drawer>
    </div>
</template>
