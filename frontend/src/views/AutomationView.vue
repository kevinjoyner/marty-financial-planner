<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import draggable from 'vuedraggable'
import { Workflow, GripVertical, ArrowRight, Plus, Pencil, FileText, Home } from 'lucide-vue-next'
import { useSimulationStore } from '../stores/simulation'
import Drawer from '../components/Drawer.vue'
import Modal from '../components/Modal.vue'
import PinToggle from '../components/PinToggle.vue'
import AutomationAudit from '../components/AutomationAudit.vue'
import MortgageAnalysis from '../components/MortgageAnalysis.vue'
import { formatCurrency } from '../utils/format'

const store = useSimulationStore()
const editingItem = ref(null)
const showAudit = ref(false)
const showMortgage = ref(false)
const form = ref({})
const localRules = ref([])

onMounted(async () => {
    if (!store.scenario) await store.init()
    if (store.scenario) localRules.value = [...store.scenario.automation_rules].sort((a,b) => a.priority - b.priority)
})

watch(() => store.scenario, (newScenario) => {
    if (newScenario) {
        localRules.value = [...newScenario.automation_rules].sort((a,b) => a.priority - b.priority)
    }
})

const accountOptions = computed(() => store.scenario?.accounts.map(a => ({ id: a.id, name: a.name })) || [])
const getAccountName = (id) => { const acc = accountOptions.value.find(a => a.id === id); return acc ? acc.name : '?' }

const openEdit = (rule) => { 
    editingItem.value = rule; 
    form.value = { 
        ...rule, 
        trigger_value: rule.trigger_value / 100, 
        transfer_value: rule.transfer_value ? rule.transfer_value / 100 : 0 
    }; 
}

const openNew = () => { 
    editingItem.value = { id: 'new' }; 
    form.value = { 
        name: 'New Rule', 
        rule_type: 'sweep', 
        trigger_value: 0, 
        cadence: 'monthly', 
        priority: localRules.value.length,
        start_date: new Date().toISOString().split('T')[0], // Default to today
        end_date: null
    }; 
}

const save = async () => {
    const payload = { ...form.value }
    // Store handles conversion
    payload.trigger_value = payload.trigger_value ? parseFloat(payload.trigger_value) : 0;
    
    if (payload.rule_type === 'mortgage_smart') {
         payload.transfer_value = payload.transfer_value ? parseFloat(payload.transfer_value) : 0;
    } else {
         payload.transfer_value = payload.transfer_value ? parseFloat(payload.transfer_value) : 0;
    }
    
    await store.saveEntity('rule', editingItem.value.id, payload)
    editingItem.value = null
}

const remove = async () => {
    const success = await store.deleteEntity('rule', editingItem.value.id);
    if (success) editingItem.value = null;
}
</script>

<template>
    <div class="flex flex-col h-full max-w-4xl mx-auto w-full pb-24">
        <header class="mb-8 flex justify-between items-center">
            <div><h1 class="text-2xl font-semibold text-slate-900 tracking-tight">Automation Rules</h1><p class="text-sm text-slate-500 mt-1">Drag to prioritize logic.</p></div>
            <div class="flex gap-2">
                <button @click="showMortgage = true" class="flex items-center gap-2 px-4 py-2 bg-white border border-slate-200 text-slate-600 text-sm font-medium rounded-md hover:bg-slate-50 transition-colors shadow-sm"><Home class="w-4 h-4" /> Mortgage Report</button>
                <button @click="showAudit = true" class="flex items-center gap-2 px-4 py-2 bg-white border border-slate-200 text-slate-600 text-sm font-medium rounded-md hover:bg-slate-50 transition-colors shadow-sm"><FileText class="w-4 h-4" /> Audit Log</button>
                <button @click="openNew" class="flex items-center gap-2 px-4 py-2 bg-slate-900 text-white text-sm font-medium rounded-md hover:bg-slate-800 transition-colors"><Plus class="w-4 h-4" /> New Rule</button>
            </div>
        </header>
        <div v-if="localRules.length === 0" class="text-center py-12 text-slate-400 italic">No automation rules defined.</div>
        <div v-else class="bg-slate-50 border border-slate-200 rounded-xl p-1">
            <draggable v-model="localRules" item-key="id" class="space-y-2" ghost-class="opacity-50">
                <template #item="{element}">
                    <div class="bg-white border border-slate-200 p-4 rounded-lg shadow-sm flex items-center gap-4 group cursor-grab active:cursor-grabbing hover:border-primary/50 transition-colors">
                        <div class="text-slate-300 group-hover:text-slate-500"><GripVertical class="w-5 h-5" /></div>
                        <div class="w-10 h-10 rounded-full bg-indigo-50 text-indigo-600 flex items-center justify-center flex-shrink-0"><Workflow class="w-5 h-5" /></div>
                        <div class="flex-1 min-w-0"><h3 class="text-sm font-semibold text-slate-900">{{ element.name }}</h3><div class="flex items-center gap-2 text-xs text-slate-500 mt-0.5"><span class="bg-slate-100 px-1.5 py-0.5 rounded text-slate-600 font-mono uppercase">{{ element.rule_type }}</span><span>{{ getAccountName(element.source_account_id) }}</span><ArrowRight class="w-3 h-3" /><span>{{ getAccountName(element.target_account_id) }}</span></div></div>
                        <div class="text-right flex items-center gap-4"><div><div class="text-xs text-slate-400 uppercase font-bold tracking-wide">Trigger</div><div class="text-sm font-mono text-slate-700">{{ formatCurrency(element.trigger_value) }}</div></div><button @click="openEdit(element)" class="p-1.5 text-slate-300 hover:text-primary hover:bg-slate-100 rounded-md transition-all"><Pencil class="w-4 h-4" /></button></div>
                    </div>
                </template>
            </draggable>
        </div>
        <div class="mt-4 text-xs text-slate-400 text-center">Rules execute top-to-bottom every month.</div>
        
        <Drawer :isOpen="!!editingItem" :title="editingItem?.name || 'Edit Rule'" @close="editingItem = null" @save="save">
            <div v-if="editingItem" class="space-y-4">
                <div><label class="block text-sm font-medium text-slate-700 mb-1">Rule Name</label><input type="text" v-model="form.name" class="w-full border border-slate-300 rounded-md px-3 py-2 text-sm"></div>
                
                <div><label class="block text-sm font-medium text-slate-700 mb-1">Type</label><select v-model="form.rule_type" class="w-full border border-slate-300 rounded-md px-3 py-2 text-sm bg-white"><option value="sweep">Sweep (Overflow)</option><option value="top_up">Top-up (Rescue)</option><option value="transfer">Smart Transfer</option><option value="mortgage_smart">Mortgage Overpay</option></select></div>
                
                <div class="grid grid-cols-2 gap-4">
                    <div><div class="flex justify-between items-center mb-1"><label class="block text-sm font-medium text-slate-700">Source</label><PinToggle v-if="editingItem.id !== 'new'" :item="{ id: `rule-${editingItem.id}-src`, realId: editingItem.id, type: 'rule', field: 'source_account_id', label: `${editingItem.name} Src`, value: editingItem.source_account_id, inputType: 'select', options: accountOptions }" /></div><select v-model="form.source_account_id" class="w-full border border-slate-300 rounded-md px-3 py-2 text-sm bg-white"><option v-for="a in accountOptions" :key="a.id" :value="a.id">{{ a.name }}</option></select></div>
                    <div><div class="flex justify-between items-center mb-1"><label class="block text-sm font-medium text-slate-700">Target</label><PinToggle v-if="editingItem.id !== 'new'" :item="{ id: `rule-${editingItem.id}-tgt`, realId: editingItem.id, type: 'rule', field: 'target_account_id', label: `${editingItem.name} Tgt`, value: editingItem.target_account_id, inputType: 'select', options: accountOptions }" /></div><select v-model="form.target_account_id" class="w-full border border-slate-300 rounded-md px-3 py-2 text-sm bg-white"><option v-for="a in accountOptions" :key="a.id" :value="a.id">{{ a.name }}</option></select></div>
                </div>
                
                <div class="grid grid-cols-2 gap-4">
                     <div><div class="flex justify-between items-center mb-1"><label class="block text-sm font-medium text-slate-700">Trigger (£)</label><PinToggle v-if="editingItem.id !== 'new'" :item="{ id: `rule-${editingItem.id}-trig`, realId: editingItem.id, type: 'rule', field: 'trigger_value', label: `${editingItem.name} Trigger`, value: editingItem.trigger_value / 100, format: 'currency' }" /></div><input type="number" v-model="form.trigger_value" class="w-full border border-slate-300 rounded-md px-3 py-2 text-sm"></div>
                     <div v-if="form.rule_type !== 'sweep' && form.rule_type !== 'top_up'"><div class="flex justify-between items-center mb-1"><label class="block text-sm font-medium text-slate-700">Value / %</label><PinToggle v-if="editingItem.id !== 'new'" :item="{ id: `rule-${editingItem.id}-val`, realId: editingItem.id, type: 'rule', field: 'transfer_value', label: `${editingItem.name} Value`, value: editingItem.transfer_value ? editingItem.transfer_value / 100 : 0, format: 'currency' }" /></div><input type="number" v-model="form.transfer_value" class="w-full border border-slate-300 rounded-md px-3 py-2 text-sm"></div>
                </div>

                <div class="grid grid-cols-2 gap-4 pt-2 border-t border-slate-100">
                    <div>
                        <div class="flex justify-between items-center mb-1"><label class="block text-sm font-medium text-slate-700">Start Date</label><PinToggle v-if="editingItem.id !== 'new'" :item="{ id: `rule-${editingItem.id}-start`, realId: editingItem.id, type: 'rule', field: 'start_date', label: `${editingItem.name} Start`, value: editingItem.start_date, inputType: 'date' }" /></div>
                        <input type="date" v-model="form.start_date" class="w-full border border-slate-300 rounded-md px-3 py-2 text-sm">
                    </div>
                    <div>
                        <div class="flex justify-between items-center mb-1"><label class="block text-sm font-medium text-slate-700">End Date (Optional)</label><PinToggle v-if="editingItem.id !== 'new'" :item="{ id: `rule-${editingItem.id}-end`, realId: editingItem.id, type: 'rule', field: 'end_date', label: `${editingItem.name} End`, value: editingItem.end_date, inputType: 'date' }" /></div>
                        <input type="date" v-model="form.end_date" class="w-full border border-slate-300 rounded-md px-3 py-2 text-sm">
                    </div>
                </div>

                <div><label class="block text-sm font-medium text-slate-700 mb-1">Notes</label><textarea v-model="form.notes" rows="3" class="w-full border border-slate-300 rounded-md px-3 py-2 text-sm"></textarea></div>
                <div class="pt-6 border-t border-slate-100">
                    <button type="button" @click="remove" class="w-full py-2 bg-red-50 text-red-600 hover:bg-red-100 rounded-md font-medium text-sm transition-colors">Delete Rule</button>
                </div>
            </div>
        </Drawer>

        <Modal :isOpen="showAudit" title="Automation Audit Log" @close="showAudit = false">
            <AutomationAudit />
        </Modal>

        <Modal :isOpen="showMortgage" title="Mortgage Analysis" @close="showMortgage = false">
            <MortgageAnalysis />
        </Modal>
    </div>
</template>
