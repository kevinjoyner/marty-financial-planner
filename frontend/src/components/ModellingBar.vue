<script setup>
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useSimulationStore } from '../stores/simulation'
import { formatCurrency } from '../utils/format'
import { X, RotateCcw, Save, Copy, ChevronRight, ChevronLeft, SlidersHorizontal } from 'lucide-vue-next'
import { api } from '../services/api'
import Modal from './Modal.vue'

const store = useSimulationStore()
const router = useRouter()
const showForkModal = ref(false)
const newScenarioName = ref('')
const isCollapsed = ref(false)

const formatVal = (item) => {
    if (item.format === 'percent') return item.value + '%';
    if (item.format === 'currency') return formatCurrency(item.value * 100); 
    return item.value;
}

const updateValue = (item, e) => {
    let val = e.target.value;
    if (item.inputType === 'number' || !item.inputType) val = parseFloat(val);
    store.updateOverride(item.id, val);
}

const netWorthDelta = computed(() => (store.projectedNetWorth || 0) - (store.baselineProjectedNetWorth || 0))
const formatPounds = (val) => formatCurrency((val || 0) * 100)
const isModelling = computed(() => store.activeOverrideCount > 0)

const openForkModal = () => {
    if(!store.scenario) return;
    newScenarioName.value = `${store.scenario.name} - new version`;
    showForkModal.value = true;
}

const saveFork = async () => {
    try {
        const overrides = store.getApiOverrides();
        const newScen = await api.forkScenario(store.activeScenarioId, { 
            name: newScenarioName.value, 
            overrides: overrides 
        });
        showForkModal.value = false;
        store.resetOverrides();
        store.pinnedItems = [];
        store.overrides = {};
        await store.loadActiveScenario(newScen.id);
        router.push('/');
        alert("Scenario Saved & Activated!");
    } catch(e) { console.error(e); alert("Failed to save scenario."); }
}
</script>

<template>
  <aside :class="['bg-white border-l border-slate-200 flex flex-col z-10 flex-shrink-0 shadow-xl h-full transition-all duration-300 ease-in-out', isCollapsed ? 'w-12' : 'w-80']">
    
    <div v-if="isCollapsed" class="flex flex-col items-center h-full py-4 bg-slate-50/50 cursor-pointer hover:bg-slate-100 transition-colors" @click="isCollapsed = false" title="Expand Modelling Bar">
        <button class="p-1 text-slate-400 hover:text-slate-600 mb-6">
            <ChevronLeft class="w-5 h-5" />
        </button>
        
        <div class="flex-1 flex items-center justify-center">
            <div :class="['transform -rotate-90 whitespace-nowrap text-xs font-bold uppercase tracking-widest flex items-center gap-2', isModelling ? 'text-[#635bff]' : 'text-slate-400']">
                <span>Modelling</span>
                <SlidersHorizontal v-if="!isModelling" class="w-4 h-4" />
                <span v-else class="flex h-2 w-2 relative">
                  <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#635bff] opacity-75"></span>
                  <span class="relative inline-flex rounded-full h-2 w-2 bg-[#635bff]"></span>
                </span>
            </div>
        </div>
    </div>

    <div v-else class="flex flex-col h-full w-full">
        <div class="p-6 border-b border-slate-100 bg-slate-50/50 flex-shrink-0">
            <div class="flex justify-between items-start mb-4">
                <h2 :class="['text-sm font-bold uppercase tracking-wider transition-colors', isModelling ? 'text-[#635bff]' : 'text-slate-900']">
                    Modelling
                </h2>
                <button @click="isCollapsed = true" class="text-slate-400 hover:text-slate-600 -mr-2 -mt-2 p-2 rounded-md hover:bg-slate-200/50 transition-colors">
                    <ChevronRight class="w-4 h-4" />
                </button>
            </div>

            <div class="bg-white border border-slate-200 rounded-lg p-3 shadow-sm">
                <div class="text-xs text-slate-400 font-medium mb-1">Projected Net Worth</div>
                <div class="flex justify-between items-end">
                    <div class="text-lg font-bold text-slate-900 leading-none">{{ formatPounds(store.projectedNetWorth) }}</div>
                    <div v-if="isModelling" class="text-xs font-semibold" :class="netWorthDelta >= 0 ? 'text-emerald-600' : 'text-rose-600'">
                        {{ netWorthDelta >= 0 ? '+' : '' }}{{ formatPounds(netWorthDelta) }}
                    </div>
                </div>
                <div v-if="isModelling" class="text-xs text-slate-400 mt-1 text-right">Base: {{ formatPounds(store.baselineProjectedNetWorth) }}</div>
            </div>
            
            <div v-if="isModelling" class="mt-4">
                 <button @click="openForkModal" class="w-full py-2 bg-[#635bff] text-white text-xs font-bold rounded shadow-sm hover:bg-[#5469d4] flex items-center justify-center gap-2 transition-colors">
                    <Copy class="w-3.5 h-3.5" /> Save as New Scenario
                 </button>
            </div>
        </div>

        <div class="flex-1 overflow-y-auto p-6 space-y-6">
            <div v-if="store.pinnedItems.length === 0" class="text-center py-10">
                <div class="text-slate-300 text-sm italic">Nothing pinned yet.</div>
                <div class="text-slate-400 text-xs mt-2 px-4">Click the Pin icon on any field to experiment.</div>
            </div>

            <div v-else v-for="item in store.pinnedItems" :key="item.id" class="group">
                <div class="flex justify-between items-center mb-1.5">
                    <label class="text-xs font-semibold text-slate-700 truncate pr-2" :title="item.label">{{ item.label }}</label>
                    <div class="flex gap-1">
                        <button @click="store.commitPinnedItem(item)" class="text-slate-300 hover:text-emerald-600 opacity-0 group-hover:opacity-100 transition-opacity" title="Save & Commit">
                            <Save class="w-3.5 h-3.5" />
                        </button>
                        <button @click="store.unpinItem(item.id)" class="text-slate-300 hover:text-rose-500 opacity-0 group-hover:opacity-100 transition-opacity" title="Unpin">
                            <X class="w-3.5 h-3.5" />
                        </button>
                    </div>
                </div>
                
                <div v-if="item.inputType === 'select'">
                    <select :value="store.overrides[item.id]" @change="e => updateValue(item, e)" class="w-full border border-slate-300 rounded px-2 py-1.5 text-xs bg-white focus:border-primary">
                        <option v-for="opt in item.options" :key="opt.id" :value="opt.id">{{ opt.name }}</option>
                    </select>
                </div>
                <div v-else-if="item.inputType === 'date'">
                    <input type="date" :value="store.overrides[item.id]" @input="e => updateValue(item, e)" class="w-full border border-slate-300 rounded px-2 py-1.5 text-xs focus:border-primary">
                </div>
                <div v-else>
                    <input type="number" :value="store.overrides[item.id]" @input="e => updateValue(item, e)" class="w-full border border-slate-300 rounded px-2 py-1.5 text-sm focus:border-primary font-mono text-right">
                    <div class="flex justify-between items-center mt-1 text-[10px] text-slate-400 font-mono"><span>Orig: {{ item.value }}</span></div>
                </div>
            </div>
        </div>

        <div class="p-4 border-t border-slate-100 bg-slate-50 flex justify-between items-center flex-shrink-0">
            <button v-if="isModelling" @click="store.resetOverrides" class="text-xs font-medium text-slate-500 hover:text-slate-800 flex items-center gap-1.5">
                <RotateCcw class="w-3.5 h-3.5" /> Reset All
            </button>
        </div>
    </div>

    <Modal :isOpen="showForkModal" title="Save New Scenario" maxWidth="max-w-md" @close="showForkModal = false">
        <div class="p-6 space-y-4">
            <p class="text-sm text-slate-600">Create a new scenario based on your new modelled values.</p>
            <div>
                <label class="block text-xs font-bold text-slate-500 uppercase mb-1">New Scenario Name</label>
                <input type="text" v-model="newScenarioName" class="w-full border border-slate-300 rounded-md px-3 py-2 text-sm focus:border-primary focus:outline-none">
            </div>
            <div class="pt-4 flex justify-end gap-3">
                <button @click="showForkModal = false" class="px-4 py-2 text-sm font-medium text-slate-600 hover:bg-slate-100 rounded-md">Cancel</button>
                <button @click="saveFork" class="px-4 py-2 text-sm font-medium text-white bg-primary hover:bg-[#5469d4] rounded-md shadow-sm">Create Scenario</button>
            </div>
        </div>
    </Modal>
  </aside>
</template>
