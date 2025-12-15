<script setup>
import { onMounted, ref, computed } from 'vue'
import { useSimulationStore } from '../stores/simulation'
import { Repeat, Pencil, ArrowRight, Calendar, Plus, TrendingUp, TrendingDown, ArrowRightLeft } from 'lucide-vue-next'
import Drawer from '../components/Drawer.vue'
import { formatCurrency } from '../utils/format'

const store = useSimulationStore()
const editingItem = ref(null)
const form = ref({})

// Sorting State
const sortKey = ref('dateLabel') 
const sortDesc = ref(true)

const sort = (key) => {
    if (sortKey.value === key) {
        sortDesc.value = !sortDesc.value
    } else {
        sortKey.value = key
        sortDesc.value = true
    }
}

onMounted(() => {
    if (!store.scenario) store.init()
})

const formatPence = (val) => formatCurrency(Math.abs(val || 0))

const getAccountName = (id) => {
    if (!store.scenario) return `Acc ${id}`
    const acc = store.scenario.accounts.find(a => a.id === id)
    return acc ? acc.name : `Acc ${id}`
}

const applySort = (list) => {
    return list.sort((a, b) => {
        let valA = a[sortKey.value]
        let valB = b[sortKey.value]
        if (sortKey.value === 'dateLabel' || sortKey.value === 'event_date') {
             valA = new Date(a.dateLabel || a.event_date || '1970-01-01').getTime()
             valB = new Date(b.dateLabel || b.event_date || '1970-01-01').getTime()
        }
        else if (typeof valA === 'string') {
            valA = valA.toLowerCase()
            valB = valB.toLowerCase()
        }
        if (valA < valB) return sortDesc.value ? 1 : -1
        if (valA > valB) return sortDesc.value ? -1 : 1
        return 0
    })
}

const allItems = computed(() => {
    if (!store.scenario) return []
    const costs = store.scenario.costs.map(c => ({
        ...c, 
        type: 'cost', 
        displayType: 'Recurring', 
        dateLabel: c.start_date,
        effectiveValue: -c.value 
    }))
    
    const events = store.scenario.financial_events
        .filter(e => e.event_type === 'income_expense')
        .map(e => ({
            ...e, 
            type: 'event', 
            displayType: 'One-off', 
            cadence: 'Once', 
            dateLabel: e.event_date,
            effectiveValue: e.value
        }))
        
    return [...costs, ...events]
})

const outgoing = computed(() => {
    return applySort(allItems.value.filter(i => i.effectiveValue <= 0))
})

const incoming = computed(() => {
    return applySort(allItems.value.filter(i => i.effectiveValue > 0))
})

const transfers = computed(() => {
    if (!store.scenario) return []
    const recurring = store.scenario.transfers.map(t => ({...t, type: 'transfer', displayType: 'Recurring', fromName: getAccountName(t.from_account_id), toName: getAccountName(t.to_account_id), dateLabel: t.start_date}))
    const oneOffs = store.scenario.financial_events
        .filter(e => e.event_type === 'transfer')
        .map(e => ({...e, type: 'event', displayType: 'One-off', cadence: 'Once', fromName: getAccountName(e.from_account_id), toName: getAccountName(e.to_account_id), dateLabel: e.event_date}))
        
    return applySort([...oneOffs, ...recurring])
})

const accountOptions = computed(() => store.scenario?.accounts || [])

// --- FORM LOGIC ---

const openEdit = (item) => {
    editingItem.value = item
    
    let flowType = 'expense';
    if (item.type === 'transfer' || (item.type === 'event' && item.event_type === 'transfer')) {
        flowType = 'transfer';
    } else {
        if (item.type === 'cost') {
            flowType = item.value > 0 ? 'expense' : 'income';
        } else {
            flowType = item.value < 0 ? 'expense' : 'income';
        }
    }

    form.value = { 
        ...item, 
        account_id: item.account_id || item.from_account_id,
        value: Math.abs(item.value / 100), 
        start_date: item.start_date || item.event_date,
        flowType: flowType,
        frequencyMode: (item.type === 'cost' || item.type === 'transfer') ? item.cadence : 'once',
        show_on_chart: item.show_on_chart || false // NEW Field
    }
}

const openNew = () => {
    editingItem.value = { id: 'new' } 
    form.value = { 
        name: 'New Transaction', 
        value: 0, 
        flowType: 'expense', 
        frequencyMode: 'once', 
        start_date: new Date().toISOString().split('T')[0],
        show_on_chart: false
    }
}

const save = async () => {
    const data = form.value;
    const isRecurring = data.frequencyMode !== 'once';
    const isTransfer = data.flowType === 'transfer';
    
    let type = '';
    let payload = {
        name: data.name,
        currency: 'GBP', 
        start_date: data.start_date,
    };

    if (isTransfer) {
        payload.from_account_id = data.from_account_id;
        payload.to_account_id = data.to_account_id;
        payload.value = data.value; 
        payload.show_on_chart = data.show_on_chart;
        
        if (isRecurring) {
            type = 'transfer';
            payload.cadence = data.frequencyMode;
        } else {
            type = 'event';
            payload.event_type = 'transfer';
            payload.event_date = data.start_date;
            payload.cadence = 'once'; 
        }
    } else {
        const isExpense = data.flowType === 'expense';
        payload.account_id = isExpense ? data.account_id : data.from_account_id; 
        
        if (isRecurring) {
            type = 'cost';
            payload.cadence = data.frequencyMode;
            payload.is_recurring = true;
            payload.account_id = isExpense ? data.account_id : data.from_account_id; 
            payload.value = isExpense ? data.value : -data.value;
        } else {
            type = 'event';
            payload.event_type = 'income_expense';
            payload.event_date = data.start_date;
            payload.from_account_id = isExpense ? data.account_id : data.from_account_id; 
            payload.value = isExpense ? -data.value : data.value;
            payload.show_on_chart = data.show_on_chart;
        }
    }

    if (editingItem.value.id !== 'new') {
        const oldType = editingItem.value.type;
        if (oldType !== type) {
            await store.deleteEntity(oldType, editingItem.value.id);
            await store.saveEntity(type, 'new', payload, `Updated ${data.name} (Changed Type)`); 
            editingItem.value = null;
            return;
        }
    }

    const verb = editingItem.value.id === 'new' ? 'Created' : 'Updated';
    const desc = `${verb} ${isTransfer ? 'Transfer' : (data.flowType === 'income' ? 'Income' : 'Expense')}: ${data.name}`;

    await store.saveEntity(type, editingItem.value.id, payload, desc)
    editingItem.value = null
}

const remove = async () => {
    const success = await store.deleteEntity(editingItem.value.type, editingItem.value.id);
    if (success) editingItem.value = null;
}

const flowLabel = computed(() => {
    if (form.value.flowType === 'income') return { text: 'Incoming (Income)', class: 'text-emerald-600 bg-emerald-50 border-emerald-100' };
    if (form.value.flowType === 'expense') return { text: 'Outgoing (Expense)', class: 'text-rose-600 bg-rose-50 border-rose-100' };
    return { text: 'Transfer', class: 'text-blue-600 bg-blue-50 border-blue-100' };
})
</script>

<template>
    <div class="flex flex-col min-h-full max-w-5xl mx-auto w-full pb-24">
        <header class="mb-8 flex justify-between items-center">
            <div>
                <h1 class="text-2xl font-semibold text-slate-900 tracking-tight">Transactions</h1>
                <p class="text-sm text-slate-500 mt-1">Unified view of all money flows.</p>
            </div>
            <button @click="openNew" class="btn-sm bg-slate-900 text-white hover:bg-slate-800 flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors shadow-sm">
                <Plus class="w-4 h-4" /> Add Transaction
            </button>
        </header>

        <div v-if="!store.scenario" class="text-slate-400 italic">Loading...</div>

        <div v-else class="space-y-10">
            
            <div>
                <h3 class="text-sm font-bold text-emerald-600 uppercase tracking-wider mb-3 px-1">Incoming</h3>
                <div class="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
                    <div v-if="incoming.length === 0" class="p-8 text-center text-slate-400 text-sm italic">No incoming transactions.</div>
                    <table v-else class="w-full text-left text-sm table-fixed">
                        <thead class="bg-slate-50 border-b border-slate-200 text-slate-500">
                            <tr>
                                <th @click="sort('name')" class="px-6 py-3 font-medium cursor-pointer hover:bg-slate-100 w-[45%]">Description</th>
                                <th @click="sort('dateLabel')" class="px-6 py-3 font-medium cursor-pointer hover:bg-slate-100 w-32 text-left">Date/Start</th>
                                <th @click="sort('cadence')" class="px-6 py-3 font-medium cursor-pointer hover:bg-slate-100 w-32">Frequency</th>
                                <th @click="sort('value')" class="px-6 py-3 font-medium text-right cursor-pointer hover:bg-slate-100">Value</th>
                                <th class="px-6 py-3 font-medium text-center w-16"></th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-slate-100">
                            <tr v-for="item in incoming" :key="item.type + item.id" class="group hover:bg-slate-50/50 transition-colors">
                                <td class="px-6 py-4 font-medium text-slate-900 truncate" :title="item.name">{{ item.name }}</td>
                                <td class="px-6 py-4 text-slate-600 whitespace-nowrap text-left">{{ item.dateLabel }}</td>
                                <td class="px-6 py-4 capitalize text-slate-600">{{ item.cadence }}</td>
                                <td class="px-6 py-4 text-right font-bold text-emerald-600">+{{ formatPence(item.value) }}</td>
                                <td class="px-6 py-4 text-center">
                                    <button @click="openEdit(item)" class="p-1.5 text-slate-300 hover:text-primary hover:bg-slate-100 rounded-md transition-all"><Pencil class="w-4 h-4" /></button>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>

            <div>
                <h3 class="text-sm font-bold text-rose-600 uppercase tracking-wider mb-3 px-1">Outgoing</h3>
                <div class="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
                    <div v-if="outgoing.length === 0" class="p-8 text-center text-slate-400 text-sm italic">No outgoing transactions.</div>
                    <table v-else class="w-full text-left text-sm table-fixed">
                        <thead class="bg-slate-50 border-b border-slate-200 text-slate-500">
                            <tr>
                                <th @click="sort('name')" class="px-6 py-3 font-medium cursor-pointer hover:bg-slate-100 w-[45%]">Description</th>
                                <th @click="sort('dateLabel')" class="px-6 py-3 font-medium cursor-pointer hover:bg-slate-100 w-32 text-left">Date/Start</th>
                                <th @click="sort('cadence')" class="px-6 py-3 font-medium cursor-pointer hover:bg-slate-100 w-32">Frequency</th>
                                <th @click="sort('value')" class="px-6 py-3 font-medium text-right cursor-pointer hover:bg-slate-100">Value</th>
                                <th class="px-6 py-3 font-medium text-center w-16"></th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-slate-100">
                            <tr v-for="item in outgoing" :key="item.type + item.id" class="group hover:bg-slate-50/50 transition-colors">
                                <td class="px-6 py-4 font-medium text-slate-900 truncate" :title="item.name">{{ item.name }}</td>
                                <td class="px-6 py-4 text-slate-600 whitespace-nowrap text-left">{{ item.dateLabel }}</td>
                                <td class="px-6 py-4 capitalize text-slate-600">{{ item.cadence }}</td>
                                <td class="px-6 py-4 text-right font-bold text-rose-600">-{{ formatPence(item.value) }}</td>
                                <td class="px-6 py-4 text-center">
                                    <button @click="openEdit(item)" class="p-1.5 text-slate-300 hover:text-primary hover:bg-slate-100 rounded-md transition-all"><Pencil class="w-4 h-4" /></button>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>

            <div v-if="transfers.length > 0">
                <h3 class="text-sm font-bold text-blue-600 uppercase tracking-wider mb-3 px-1">Transfers</h3>
                <div class="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
                    <table class="w-full text-left text-sm table-fixed">
                        <thead class="bg-slate-50 border-b border-slate-200 text-slate-500">
                            <tr>
                                <th @click="sort('name')" class="px-6 py-3 font-medium cursor-pointer hover:bg-slate-100 w-[25%]">Description</th>
                                <th @click="sort('dateLabel')" class="px-6 py-3 font-medium cursor-pointer hover:bg-slate-100 w-32 text-left">Date/Start</th>
                                <th class="px-6 py-3 font-medium w-[35%]">Flow</th>
                                <th @click="sort('cadence')" class="px-6 py-3 font-medium cursor-pointer hover:bg-slate-100 w-28">Frequency</th>
                                <th @click="sort('value')" class="px-6 py-3 font-medium text-right cursor-pointer hover:bg-slate-100 w-32">Value</th>
                                <th class="px-6 py-3 font-medium text-center w-16"></th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-slate-100">
                            <tr v-for="t in transfers" :key="t.type + '-' + t.id" class="group hover:bg-slate-50/50 transition-colors">
                                <td class="px-6 py-4 font-medium text-slate-900 truncate" :title="t.name">{{ t.name }}</td>
                                <td class="px-6 py-4 text-slate-600 whitespace-nowrap text-left">{{ t.dateLabel }}</td>
                                <td class="px-6 py-4 text-slate-600 truncate">
                                    <div class="flex items-center gap-2 text-xs">
                                        <span class="bg-slate-100 px-2 py-1 rounded truncate max-w-[120px]" :title="t.fromName">{{ t.fromName }}</span>
                                        <ArrowRight class="w-3 h-3 text-slate-400 flex-shrink-0" />
                                        <span class="bg-slate-100 px-2 py-1 rounded truncate max-w-[120px]" :title="t.toName">{{ t.toName }}</span>
                                    </div>
                                </td>
                                <td class="px-6 py-4 capitalize text-slate-600">{{ t.cadence }}</td>
                                <td class="px-6 py-4 text-right font-bold text-slate-700">{{ formatPence(t.value) }}</td>
                                <td class="px-6 py-4 text-center">
                                    <button @click="openEdit(t)" class="p-1.5 text-slate-300 hover:text-primary hover:bg-slate-100 rounded-md transition-all"><Pencil class="w-4 h-4" /></button>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>

        </div>

        <Drawer :isOpen="!!editingItem" :title="editingItem?.id === 'new' ? 'New Transaction' : 'Edit Transaction'" @close="editingItem = null" @save="save">
            <div v-if="editingItem" class="space-y-5">
                
                <div class="grid grid-cols-3 bg-slate-100 p-1 rounded-lg">
                    <button @click="form.flowType = 'expense'" :class="['py-1.5 text-sm font-medium rounded-md transition-all', form.flowType === 'expense' ? 'bg-white text-rose-600 shadow-sm' : 'text-slate-500 hover:text-slate-700']">Expense</button>
                    <button @click="form.flowType = 'income'" :class="['py-1.5 text-sm font-medium rounded-md transition-all', form.flowType === 'income' ? 'bg-white text-emerald-600 shadow-sm' : 'text-slate-500 hover:text-slate-700']">Income</button>
                    <button @click="form.flowType = 'transfer'" :class="['py-1.5 text-sm font-medium rounded-md transition-all', form.flowType === 'transfer' ? 'bg-white text-blue-600 shadow-sm' : 'text-slate-500 hover:text-slate-700']">Transfer</button>
                </div>

                <div><label class="block text-xs font-bold text-slate-500 uppercase mb-1">Description</label><input type="text" v-model="form.name" class="w-full border border-slate-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary"></div>
                
                <div>
                    <label class="block text-xs font-bold text-slate-500 uppercase mb-1">Amount</label>
                    <div class="relative">
                        <span class="absolute left-3 top-2 text-slate-400">£</span>
                        <input type="number" v-model="form.value" class="w-full border border-slate-300 rounded-md pl-7 pr-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary" min="0" step="0.01">
                    </div>
                </div>

                <div v-if="form.frequencyMode === 'once' && (form.flowType === 'transfer' || form.flowType === 'income' || form.flowType === 'expense')">
                    <div class="flex items-center gap-2 p-2 bg-slate-50 rounded border border-slate-200">
                        <input type="checkbox" v-model="form.show_on_chart" id="chart-toggle" class="w-4 h-4 text-primary rounded">
                        <label for="chart-toggle" class="text-sm font-medium text-slate-700 cursor-pointer">Show as visual marker on chart</label>
                    </div>
                </div>

                <div>
                    <label class="block text-xs font-bold text-slate-500 uppercase mb-1">Frequency</label>
                    <select v-model="form.frequencyMode" class="w-full border border-slate-300 rounded-md px-3 py-2 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary">
                        <option value="once">One-off (Single Event)</option>
                        <option value="monthly">Monthly (Recurring)</option>
                        <option value="quarterly">Quarterly (Recurring)</option>
                        <option value="annually">Annually (Recurring)</option>
                    </select>
                </div>
                
                <div v-if="form.flowType === 'transfer'" class="grid grid-cols-2 gap-4">
                    <div><label class="block text-xs font-bold text-slate-500 uppercase mb-1">From Account</label><select v-model="form.from_account_id" class="w-full border border-slate-300 rounded-md px-3 py-2 text-sm bg-white"><option v-for="acc in accountOptions" :key="acc.id" :value="acc.id">{{ acc.name }}</option></select></div>
                    <div><label class="block text-xs font-bold text-slate-500 uppercase mb-1">To Account</label><select v-model="form.to_account_id" class="w-full border border-slate-300 rounded-md px-3 py-2 text-sm bg-white"><option v-for="acc in accountOptions" :key="acc.id" :value="acc.id">{{ acc.name }}</option></select></div>
                </div>
                
                <div v-else>
                    <label class="block text-xs font-bold text-slate-500 uppercase mb-1">
                        {{ form.flowType === 'expense' ? 'Pay From Account' : 'Deposit Into Account' }}
                    </label>
                    <select v-model="form.account_id" v-if="form.flowType === 'expense'" class="w-full border border-slate-300 rounded-md px-3 py-2 text-sm bg-white">
                        <option v-for="acc in accountOptions" :key="acc.id" :value="acc.id">{{ acc.name }}</option>
                    </select>
                    <select v-model="form.from_account_id" v-else class="w-full border border-slate-300 rounded-md px-3 py-2 text-sm bg-white">
                        <option v-for="acc in accountOptions" :key="acc.id" :value="acc.id">{{ acc.name }}</option>
                    </select>
                </div>

                <div>
                    <label class="block text-xs font-bold text-slate-500 uppercase mb-1">{{ form.frequencyMode === 'once' ? 'Date' : 'Start Date' }}</label>
                    <input type="date" v-model="form.start_date" class="w-full border border-slate-300 rounded-md px-3 py-2 text-sm">
                </div>
                
                <div><label class="block text-xs font-bold text-slate-500 uppercase mb-1">Notes</label><textarea v-model="form.notes" rows="3" class="w-full border border-slate-300 rounded-md px-3 py-2 text-sm"></textarea></div>
                <div v-if="editingItem.id !== 'new'" class="pt-6 border-t border-slate-100">
                    <button type="button" @click="remove" class="w-full py-2 bg-red-50 text-red-600 hover:bg-red-100 rounded-md font-medium text-sm transition-colors">Delete Transaction</button>
                </div>
            </div>
        </Drawer>
    </div>
</template>
