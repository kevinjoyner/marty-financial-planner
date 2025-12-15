<script setup>
import { onMounted, ref } from 'vue'
import { useSimulationStore } from '../stores/simulation'
import { CreditCard, Repeat, Pencil } from 'lucide-vue-next'
import PinToggle from '../components/PinToggle.vue'
import Drawer from '../components/Drawer.vue'

const store = useSimulationStore()
const editingItem = ref(null)
const form = ref({})

onMounted(() => {
    if (!store.scenario) store.init()
})

const formatCurrency = (val) => new Intl.NumberFormat('en-GB', { style: 'currency', currency: 'GBP' }).format(val / 100)

const openEdit = (item) => {
    editingItem.value = item
    form.value = { ...item, value: item.value / 100 }
}

const save = async () => {
    const success = await store.saveEntity('cost', editingItem.value.id, form.value)
    if (success) editingItem.value = null
}
</script>

<template>
    <div class="flex flex-col h-full max-w-5xl mx-auto w-full">
        <header class="mb-8">
            <h1 class="text-2xl font-semibold text-slate-900 tracking-tight">Expenses</h1>
            <p class="text-sm text-slate-500 mt-1">Recurring costs and lifestyle spending.</p>
        </header>

        <div v-if="!store.scenario" class="text-slate-400 italic">Loading...</div>

        <div v-else class="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
            <table class="w-full text-left text-sm">
                <thead class="bg-slate-50 border-b border-slate-200 text-slate-500">
                    <tr>
                        <th class="px-6 py-3 font-medium">Description</th>
                        <th class="px-6 py-3 font-medium">Frequency</th>
                        <th class="px-6 py-3 font-medium text-right">Amount</th>
                        <th class="px-6 py-3 font-medium text-center w-24">Actions</th>
                    </tr>
                </thead>
                <tbody class="divide-y divide-slate-100">
                    <tr v-for="cost in store.scenario.costs" :key="cost.id" class="group hover:bg-slate-50/50 transition-colors">
                        <td class="px-6 py-4">
                            <div class="flex items-center gap-3">
                                <div class="w-8 h-8 rounded-full bg-slate-100 text-slate-600 flex items-center justify-center">
                                    <CreditCard class="w-4 h-4" />
                                </div>
                                <div>
                                    <div class="font-medium text-slate-900">{{ cost.name }}</div>
                                    <div v-if="cost.is_recurring" class="text-xs text-slate-400 flex items-center gap-1">
                                        <Repeat class="w-3 h-3" /> Recurring
                                    </div>
                                </div>
                            </div>
                        </td>
                        <td class="px-6 py-4 capitalize text-slate-600">{{ cost.cadence }}</td>
                        <td class="px-6 py-4 text-right font-bold text-slate-700">{{ formatCurrency(cost.value) }}</td>
                        <td class="px-6 py-4 text-center">
                            <div class="flex justify-center gap-2">
                                <PinToggle :item="{ id: `cost-${cost.id}`, realId: cost.id, type: 'cost', field: 'value', label: cost.name, value: cost.value / 100, format: 'currency' }" />
                                <button @click="openEdit(cost)" class="p-1.5 text-slate-300 hover:text-primary hover:bg-slate-100 rounded-md transition-all"><Pencil class="w-4 h-4" /></button>
                            </div>
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>

        <Drawer 
            :isOpen="!!editingItem" 
            :title="editingItem?.name || 'Edit Expense'" 
            @close="editingItem = null" 
            @save="save"
        >
            <div v-if="editingItem" class="space-y-4">
                <div><label class="block text-sm font-medium text-slate-700 mb-1">Description</label><input type="text" v-model="form.name" class="w-full border border-slate-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary"></div>
                <div>
                    <label class="block text-sm font-medium text-slate-700 mb-1">Amount</label>
                    <div class="relative"><span class="absolute left-3 top-2 text-slate-400">£</span><input type="number" v-model="form.value" class="w-full border border-slate-300 rounded-md pl-7 pr-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary"></div>
                </div>
            </div>
        </Drawer>
    </div>
</template>
