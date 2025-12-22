<script setup>
import { onMounted, ref, computed } from 'vue'
import { useSimulationStore } from '../stores/simulation'
import { GitCommit, Plus, GripVertical, ShieldCheck } from 'lucide-vue-next'
import Drawer from '../components/Drawer.vue'
import PinToggle from '../components/PinToggle.vue'
import draggable from 'vuedraggable'

const store = useSimulationStore()
const editingRule = ref(null)
const form = ref({})
const activeTab = ref('rules') 

onMounted(() => {
    if (!store.scenario) store.init()
})

const strategies = computed(() => store.scenario?.decumulation_strategies || [])

// Treat as singleton for UI purposes
const currentStrategy = computed(() => {
    if (strategies.value.length > 0) return strategies.value[0];
    return null;
})

const openCreate = () => {
    editingRule.value = { id: 'new', name: 'New Rule', rule_type: 'sweep', trigger_value: 1000, priority: 10 };
    form.value = { ...editingRule.value };
}
const openEdit = (rule) => {
    editingRule.value = rule;
    form.value = { ...rule, trigger_value: rule.trigger_value / 100 };
}
const saveRule = async () => {
    const payload = { ...form.value, trigger_value: form.value.trigger_value * 100 };
    await store.saveEntity('rule', editingRule.value.id, payload);
    editingRule.value = null;
}
const deleteRule = async () => {
    await store.deleteEntity('rule', editingRule.value.id);
    editingRule.value = null;
}

// Unified Toggle Logic
const toggleStrategy = async () => {
    if (!currentStrategy.value) {
        // CREATE if doesn't exist
        await store.saveEntity('decumulation_strategy', 'new', {
            name: "Automated Decumulation",
            strategy_type: "automated",
            enabled: true
        });
    } else {
        // UPDATE if exists
        const s = currentStrategy.value;
        // Optimistic toggle handled by store reload usually, but for speed:
        s.enabled = !s.enabled; 
        try {
            await store.saveEntity('decumulation_strategy', s.id, { ...s, enabled: s.enabled }, "Toggled Strategy", true);
        } catch(e) { s.enabled = !s.enabled; }
    }
}
</script>

<template>
    <div class="flex flex-col h-full max-w-5xl mx-auto w-full pb-24">
        <header class="mb-8 flex justify-between items-end">
            <div><h1 class="text-2xl font-semibold text-slate-900 tracking-tight">Automation</h1><p class="text-sm text-slate-500 mt-1">Configure automated money movements.</p></div>
            <div class="flex gap-2 bg-slate-100 p-1 rounded-lg">
                <button @click="activeTab='rules'" :class="['px-4 py-1.5 text-sm font-medium rounded-md transition-all', activeTab==='rules' ? 'bg-white text-indigo-600 shadow-sm' : 'text-slate-500 hover:text-slate-700']">Rules</button>
                <button @click="activeTab='strategies'" :class="['px-4 py-1.5 text-sm font-medium rounded-md transition-all', activeTab==='strategies' ? 'bg-white text-indigo-600 shadow-sm' : 'text-slate-500 hover:text-slate-700']">Strategies</button>
            </div>
        </header>
        
        <div v-if="activeTab==='rules' && store.scenario" class="space-y-6">
            <div class="flex justify-end"><button @click="openCreate" class="text-sm font-bold text-white bg-indigo-600 hover:bg-indigo-700 px-4 py-2 rounded-lg flex items-center gap-2 shadow-sm"><Plus class="w-4 h-4"/> New Rule</button></div>
            <draggable v-model="store.scenario.automation_rules" item-key="id" class="space-y-3" handle=".drag-handle">
                <template #item="{element}">
                    <div class="bg-white border border-slate-200 rounded-xl p-4 shadow-sm flex items-center gap-4">
                        <div class="drag-handle cursor-move text-slate-300 hover:text-slate-500"><GripVertical class="w-5 h-5" /></div>
                        <div class="grow"><h3 class="font-semibold text-slate-900">{{ element.name }}</h3><div class="text-xs text-slate-500 uppercase font-bold tracking-wider">{{ element.rule_type }}</div></div>
                        <button @click="openEdit(element)" class="text-sm text-indigo-600 font-medium hover:underline">Edit</button>
                    </div>
                </template>
            </draggable>
        </div>

        <div v-if="activeTab==='strategies' && store.scenario" class="flex flex-col items-center">
            <div class="w-full max-w-2xl mt-4">
                
                <div class="bg-white border border-slate-200 rounded-xl p-6 shadow-sm relative overflow-hidden transition-all hover:shadow-md cursor-pointer" @click="toggleStrategy">
                     <div class="absolute top-0 left-0 w-1 h-full transition-colors duration-300" :class="(currentStrategy && currentStrategy.enabled) ? 'bg-indigo-500' : 'bg-slate-300'"></div>
                     
                     <div class="flex justify-between items-start pl-3">
                        <div class="flex items-start gap-4 grow">
                            <div class="w-12 h-12 rounded-full flex items-center justify-center transition-colors duration-300 mt-1" :class="(currentStrategy && currentStrategy.enabled) ? 'bg-indigo-100 text-indigo-600' : 'bg-slate-100 text-slate-400'">
                                <ShieldCheck class="w-7 h-7" />
                            </div>
                            <div>
                                <h3 class="font-semibold text-slate-900 text-lg">Automated Decumulation</h3>
                                <p class="text-sm text-slate-500 mt-1 leading-relaxed max-w-md">
                                    Safeguards your plan by auto-liquidating assets to cover deficits. 
                                    Prioritizes Cash > General Investments > ISAs > Pensions to maximize tax efficiency.
                                </p>
                            </div>
                        </div>
                        
                        <div class="flex flex-col items-end gap-4">
                            <div class="relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none" :class="(currentStrategy && currentStrategy.enabled) ? 'bg-indigo-600' : 'bg-slate-200'">
                                <span class="translate-x-1 inline-block h-4 w-4 transform rounded-full bg-white transition-transform" :class="(currentStrategy && currentStrategy.enabled) ? 'translate-x-6' : 'translate-x-1'"/>
                            </div>
                            
                            <div v-if="currentStrategy" @click.stop>
                                <PinToggle :item="{ id: 'strat-'+currentStrategy.id, realId: currentStrategy.id, type: 'decumulation_strategy', field: 'enabled', label: 'Auto Decumulation', value: currentStrategy.enabled, format: 'boolean', inputType: 'boolean' }" />
                            </div>
                        </div>
                     </div>
                </div>

            </div>
        </div>
        <Drawer :isOpen="!!editingRule" title="Edit Rule" @close="editingRule = null" @save="saveRule">
            <div v-if="editingRule" class="space-y-4">
                <div><label class="block text-sm font-medium mb-1">Name</label><input type="text" v-model="form.name" class="w-full border rounded px-3 py-2"></div>
                <div><label class="block text-sm font-medium mb-1">Type</label><select v-model="form.rule_type" class="w-full border rounded px-3 py-2"><option value="sweep">Sweep</option><option value="top_up">Top Up</option></select></div>
                <div><label class="block text-sm font-medium mb-1">Trigger (£)</label><input type="number" v-model="form.trigger_value" class="w-full border rounded px-3 py-2"></div>
                <div class="pt-4 border-t"><button type="button" @click="deleteRule" class="text-red-600 text-sm">Delete Rule</button></div>
            </div>
        </Drawer>
    </div>
</template>
