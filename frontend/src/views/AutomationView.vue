<script setup>
import { onMounted, ref, computed } from 'vue'
import { useSimulationStore } from '../stores/simulation'
import { GitCommit, ArrowRight, Trash2, Plus, GripVertical, ShieldCheck, PlayCircle, ToggleLeft, ToggleRight } from 'lucide-vue-next'
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

const openCreate = () => {
    const newRule = { 
        id: 'new', 
        name: 'New Rule', 
        rule_type: 'sweep',
        trigger_value: 100000, 
        priority: 10
    }
    editingRule.value = newRule;
    form.value = { ...newRule };
}

const openEdit = (rule) => {
    editingRule.value = rule
    form.value = { ...rule, trigger_value: rule.trigger_value / 100, transfer_value: rule.transfer_value ? rule.transfer_value / 100 : null }
}

const save = async () => {
    const payload = {
        ...form.value,
        trigger_value: form.value.trigger_value * 100,
        transfer_value: form.value.transfer_value ? form.value.transfer_value * 100 : null
    }
    await store.saveEntity('automation_rule', editingRule.value.id, payload, `Saved Rule`)
    editingRule.value = null
}

const remove = async () => {
    await store.deleteEntity('automation_rule', editingRule.value.id)
    editingRule.value = null
}

const addStrategy = async () => {
    const payload = {
        scenario_id: store.scenario.id,
        name: "Automated Decumulation",
        strategy_type: "automated",
        enabled: true
    }
    await store.saveEntity('decumulation_strategy', 'new', payload, "Enabled Decumulation")
    // Force refresh to get the new ID and ensure UI state is synced
    await store.init() 
}

const removeStrategy = async (id) => {
    await store.deleteEntity('decumulation_strategy', id)
}

const toggleStrategy = async (s) => {
    // 1. Calculate new state
    const newState = !s.enabled;
    
    // 2. Optimistic UI update (forces reactivity)
    s.enabled = newState;

    // 3. API Call
    try {
        const payload = { ...s, enabled: newState };
        // We clone s to avoid sending a reactive proxy if that's causing issues
        await store.saveEntity('decumulation_strategy', s.id, payload, newState ? "Resumed Decumulation" : "Paused Decumulation");
    } catch (e) {
        console.error("Toggle failed", e);
        s.enabled = !newState; // Revert
    }
}

const updatePriorities = async () => {
    store.scenario.automation_rules.forEach((r, idx) => {
        if (r.priority !== idx) {
             store.saveEntity('automation_rule', r.id, { ...r, priority: idx }, null, true) 
        }
    })
}
</script>

<template>
    <div class="flex flex-col h-full max-w-5xl mx-auto w-full pb-24">
        <header class="mb-8 flex justify-between items-end">
            <div>
                <h1 class="text-2xl font-semibold text-slate-900 tracking-tight">Automation</h1>
                <p class="text-sm text-slate-500 mt-1">Configure automated money movements and safety nets.</p>
            </div>
            <div class="flex gap-2 bg-slate-100 p-1 rounded-lg">
                <button @click="activeTab='rules'" :class="['px-4 py-1.5 text-sm font-medium rounded-md transition-all', activeTab==='rules' ? 'bg-white text-indigo-600 shadow-sm' : 'text-slate-500 hover:text-slate-700']">Rules</button>
                <button @click="activeTab='strategies'" :class="['px-4 py-1.5 text-sm font-medium rounded-md transition-all', activeTab==='strategies' ? 'bg-white text-indigo-600 shadow-sm' : 'text-slate-500 hover:text-slate-700']">Strategies</button>
            </div>
        </header>
        
        <div v-if="!store.scenario" class="text-slate-400 italic">Loading...</div>
        
        <div v-if="activeTab==='rules' && store.scenario" class="space-y-6">
            <div class="flex justify-end">
                <button @click="openCreate" class="text-sm font-bold text-white bg-indigo-600 hover:bg-indigo-700 px-4 py-2 rounded-lg flex items-center gap-2 shadow-sm transition-all"><Plus class="w-4 h-4"/> New Rule</button>
            </div>
            
            <div v-if="store.scenario.automation_rules.length === 0" class="text-center py-12 bg-slate-50 rounded-xl border border-dashed border-slate-300">
                <GitCommit class="w-12 h-12 text-slate-300 mx-auto mb-3" />
                <p class="text-slate-500">No automation rules defined.</p>
            </div>

            <draggable 
                v-model="store.scenario.automation_rules" 
                item-key="id" 
                class="space-y-3"
                handle=".drag-handle"
                @end="updatePriorities"
            >
                <template #item="{element}">
                    <div class="bg-white border border-slate-200 rounded-xl p-4 shadow-sm flex items-center gap-4 group hover:border-indigo-300 transition-all">
                        <div class="drag-handle cursor-move text-slate-300 hover:text-slate-500"><GripVertical class="w-5 h-5" /></div>
                        <div class="w-10 h-10 rounded-full bg-indigo-50 text-indigo-600 flex items-center justify-center shrink-0">
                            <GitCommit class="w-5 h-5" />
                        </div>
                        <div class="grow">
                            <h3 class="font-semibold text-slate-900">{{ element.name }}</h3>
                            <div class="flex items-center gap-2 text-xs text-slate-500 mt-0.5">
                                <span class="uppercase font-bold tracking-wider text-indigo-500">{{ element.rule_type.replace('_', ' ') }}</span>
                                <span>&bull;</span>
                                <span>Trigger: > £{{ element.trigger_value / 100 }}</span>
                            </div>
                        </div>
                        <button @click="openEdit(element)" class="text-sm text-indigo-600 font-medium hover:underline">Edit</button>
                    </div>
                </template>
            </draggable>
        </div>

        <div v-if="activeTab==='strategies' && store.scenario" class="flex flex-col items-center">
            <div class="w-full max-w-2xl">
                <div v-if="strategies.length === 0" class="flex justify-center mt-8">
                    <button @click="addStrategy" class="border-2 border-dashed border-slate-300 rounded-xl p-8 flex flex-col items-center justify-center text-slate-400 hover:border-indigo-400 hover:text-indigo-600 hover:bg-indigo-50 transition-all group w-full h-full min-h-[200px]">
                        <ShieldCheck class="w-12 h-12 mb-4 group-hover:scale-110 transition-transform" />
                        <span class="font-medium text-lg">Enable Automated Decumulation</span>
                    </button>
                </div>

                <div v-for="s in strategies" :key="s.id" class="bg-white border border-slate-200 rounded-xl p-6 shadow-sm relative overflow-hidden transition-all hover:shadow-md mt-4">
                     <div class="absolute top-0 left-0 w-1 h-full transition-colors duration-300" :class="s.enabled ? 'bg-indigo-500' : 'bg-slate-300'"></div>
                     
                     <div class="flex justify-between items-start mb-6 pl-3">
                        <div class="flex items-center gap-4">
                            <div class="w-12 h-12 rounded-full flex items-center justify-center transition-colors duration-300" :class="s.enabled ? 'bg-indigo-100 text-indigo-600' : 'bg-slate-100 text-slate-400'">
                                <ShieldCheck class="w-7 h-7" />
                            </div>
                            <div>
                                <h3 class="font-semibold text-slate-900 text-lg">{{ s.name }}</h3>
                                <p class="text-sm text-slate-500">Auto-liquidates assets to cover deficits.</p>
                            </div>
                        </div>
                        
                        <div class="flex flex-col items-end gap-1">
                            <div class="flex items-center gap-2 mb-1">
                                <span class="text-xs font-bold uppercase tracking-wider" :class="s.enabled ? 'text-indigo-600' : 'text-slate-400'">{{ s.enabled ? 'Active' : 'Paused' }}</span>
                                <button 
                                    @click="toggleStrategy(s)" 
                                    class="w-12 h-6 rounded-full p-1 transition-colors duration-300 relative focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
                                    :class="s.enabled ? 'bg-indigo-600' : 'bg-slate-200'"
                                >
                                    <div 
                                        class="w-4 h-4 bg-white rounded-full shadow-sm transition-transform duration-300"
                                        :class="s.enabled ? 'translate-x-6' : 'translate-x-0'"
                                    ></div>
                                </button>
                            </div>
                            <PinToggle :item="{ id: 'strat-enable-' + s.id, realId: s.id, type: 'decumulation_strategy', field: 'enabled', label: 'Safety Net', value: s.enabled, format: 'boolean' }" />
                        </div>
                     </div>
                     
                     <div class="pl-3 space-y-4 pr-4">
                        <div class="flex items-center gap-3 text-sm text-slate-600 p-2 rounded-lg" :class="s.enabled ? 'bg-slate-50' : 'opacity-50'">
                            <span class="w-6 h-6 rounded-full bg-white border border-slate-200 flex items-center justify-center text-xs font-bold text-slate-500 shadow-sm">1</span>
                            <span>Sweep Excess Cash</span>
                        </div>
                        <div class="flex items-center gap-3 text-sm text-slate-600 p-2 rounded-lg" :class="s.enabled ? 'bg-slate-50' : 'opacity-50'">
                            <span class="w-6 h-6 rounded-full bg-white border border-slate-200 flex items-center justify-center text-xs font-bold text-slate-500 shadow-sm">2</span>
                            <span>Sell General Investments (GIA)</span>
                        </div>
                        <div class="flex items-center gap-3 text-sm text-slate-600 p-2 rounded-lg" :class="s.enabled ? 'bg-slate-50' : 'opacity-50'">
                            <span class="w-6 h-6 rounded-full bg-white border border-slate-200 flex items-center justify-center text-xs font-bold text-slate-500 shadow-sm">3</span>
                            <span>Sell ISAs</span>
                        </div>
                        <div class="flex items-center gap-3 text-sm text-slate-600 p-2 rounded-lg" :class="s.enabled ? 'bg-slate-50' : 'opacity-50'">
                             <span class="w-6 h-6 rounded-full bg-white border border-slate-200 flex items-center justify-center text-xs font-bold text-slate-500 shadow-sm">4</span>
                            <div class="flex justify-between w-full">
                                <span>Draw Pension</span>
                                <span class="text-xs text-slate-400 bg-white px-2 py-0.5 rounded border border-slate-100">Age 57+</span>
                            </div>
                        </div>
                     </div>

                     <div class="mt-8 pt-4 border-t border-slate-100 flex justify-between items-center pl-3">
                        <div class="text-xs text-slate-400">Strategy Priority</div>
                        <button @click="removeStrategy(s.id)" class="text-xs text-red-500 hover:text-red-700 hover:underline flex items-center gap-1"><Trash2 class="w-3 h-3"/> Delete Strategy</button>
                     </div>
                </div>
            </div>
        </div>

        <Drawer :isOpen="!!editingRule" :title="editingRule?.id === 'new' ? 'New Rule' : 'Edit Rule'" @close="editingRule = null" @save="save">
            <div v-if="editingRule" class="space-y-4">
                <div><label class="block text-sm font-medium text-slate-700 mb-1">Name</label><input type="text" v-model="form.name" class="w-full border border-slate-300 rounded-md px-3 py-2 text-sm"></div>
                
                <div class="grid grid-cols-2 gap-4">
                    <div>
                        <label class="block text-sm font-medium text-slate-700 mb-1">Type</label>
                        <select v-model="form.rule_type" class="w-full border border-slate-300 rounded-md px-3 py-2 text-sm">
                            <option value="sweep">Sweep (Excess)</option>
                            <option value="top_up">Top-up (Deficit)</option>
                            <option value="smart_transfer">Smart Transfer</option>
                            <option value="mortgage_smart">Mortgage Smooth</option>
                        </select>
                    </div>
                     <div>
                        <label class="block text-sm font-medium text-slate-700 mb-1">Cadence</label>
                        <select v-model="form.cadence" class="w-full border border-slate-300 rounded-md px-3 py-2 text-sm">
                            <option value="monthly">Monthly</option>
                            <option value="annually">Annually</option>
                            <option value="once">Once</option>
                        </select>
                    </div>
                </div>

                <div v-if="form.rule_type !== 'mortgage_smart'">
                    <div class="flex justify-between items-center mb-1"><label class="block text-sm font-medium text-slate-700">Trigger Threshold</label><PinToggle v-if="editingRule.id !== 'new'" :item="{ id: `rule-trig-${editingRule.id}`, realId: editingRule.id, type: 'rule', field: 'trigger_value', label: 'Trigger', value: editingRule.trigger_value / 100, format: 'currency' }" /></div>
                    <div class="relative"><span class="absolute left-3 top-2 text-slate-400">£</span><input type="number" v-model="form.trigger_value" class="w-full border border-slate-300 rounded-md pl-7 pr-3 py-2 text-sm"></div>
                </div>

                <div>
                    <label class="block text-sm font-medium text-slate-700 mb-1">Source Account</label>
                    <select v-model="form.source_account_id" class="w-full border border-slate-300 rounded-md px-3 py-2 text-sm">
                        <option v-for="a in store.scenario.accounts" :key="a.id" :value="a.id">{{ a.name }}</option>
                    </select>
                </div>

                <div>
                    <label class="block text-sm font-medium text-slate-700 mb-1">Target Account</label>
                    <select v-model="form.target_account_id" class="w-full border border-slate-300 rounded-md px-3 py-2 text-sm">
                         <option :value="null">External / None</option>
                        <option v-for="a in store.scenario.accounts" :key="a.id" :value="a.id">{{ a.name }}</option>
                    </select>
                </div>

                 <div class="pt-6 border-t border-slate-100" v-if="editingRule.id !== 'new'">
                    <button type="button" @click="remove" class="w-full py-2 bg-red-50 text-red-600 hover:bg-red-100 rounded-md font-medium text-sm transition-colors">Delete Rule</button>
                </div>
            </div>
        </Drawer>
    </div>
</template>
