<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { ChevronDown, ChevronRight } from 'lucide-vue-next'
import { useSimulationStore } from '../stores/simulation'
import { getAccountColor, getCategoryColor } from '../utils/colors'

const store = useSimulationStore()
const emit = defineEmits(['update:selection'])

const props = defineProps({
    initialSelection: Array
})

// Default expanded state
const expandedGroups = ref({ liquid: true, illiquid: false, liabilities: true, unvested: false })
const selectedIds = ref(new Set())

const toggleGroupExpand = (group) => {
    expandedGroups.value[group] = !expandedGroups.value[group];
}

const toggleAccount = (id) => {
    if (selectedIds.value.has(id)) selectedIds.value.delete(id);
    else selectedIds.value.add(id);
    emitSelection();
}

const toggleGroupSelection = (groupAccounts) => {
    const allSelected = groupAccounts.every(a => selectedIds.value.has(a.id));
    groupAccounts.forEach(a => {
        if (allSelected) selectedIds.value.delete(a.id);
        else selectedIds.value.add(a.id);
    });
    emitSelection();
}

const emitSelection = () => {
    emit('update:selection', Array.from(selectedIds.value));
}

// Watch initialSelection to sync state when parent restores settings
watch(() => props.initialSelection, (newVal) => {
    if (newVal && newVal.length > 0) {
        selectedIds.value = new Set(newVal);
    } else if (store.scenario?.accounts && selectedIds.value.size === 0) {
        // Fallback: Select all if nothing stored
        store.scenario.accounts.forEach(a => selectedIds.value.add(a.id));
        emitSelection();
    }
}, { immediate: true });

const renderGroup = (key, label, accounts) => {
    if (!accounts || accounts.length === 0) return null;
    
    const isExpanded = expandedGroups.value[key];
    const allSelected = accounts.every(a => selectedIds.value.has(a.id));
    const someSelected = !allSelected && accounts.some(a => selectedIds.value.has(a.id));
    
    return {
        key, label, accounts, isExpanded, allSelected, someSelected
    };
}

const groups = computed(() => {
    const cats = store.accountsByCategory || { liquid: [], illiquid: [], liabilities: [], unvested: [] };
    return [
        renderGroup('liquid', 'Liquid Assets', cats.liquid),
        renderGroup('illiquid', 'Illiquid Assets', cats.illiquid),
        renderGroup('liabilities', 'Liabilities', cats.liabilities),
        renderGroup('unvested', 'Unvested RSUs', cats.unvested),
    ].filter(g => g !== null);
});
</script>

<template>
  <div class="h-full overflow-y-auto pr-2 text-sm select-none custom-scrollbar">
    <div v-for="g in groups" :key="g.key" class="mb-3">
        <div class="flex items-center gap-1 mb-1 cursor-pointer group" >
            <button @click.stop="toggleGroupExpand(g.key)" class="text-slate-400 hover:text-slate-600 p-1">
                <ChevronDown v-if="g.isExpanded" class="w-3 h-3" />
                <ChevronRight v-else class="w-3 h-3" />
            </button>
            
            <div @click="toggleGroupSelection(g.accounts)" class="flex items-center gap-2 flex-1 py-1 px-2 rounded hover:bg-slate-50 transition-colors">
                <div :style="(g.allSelected || g.someSelected) ? { backgroundColor: getCategoryColor(g.key), borderColor: getCategoryColor(g.key) } : {}"
                     :class="['w-3.5 h-3.5 border rounded flex items-center justify-center transition-colors', 
                     (g.allSelected || g.someSelected) ? 'text-white' : 'bg-white border-slate-300']">
                    <div v-if="g.someSelected" class="w-1.5 h-1.5 bg-white rounded-sm"></div>
                </div>
                
                <span :class="['text-xs font-medium', (g.allSelected || g.someSelected) ? 'text-slate-900 font-bold' : 'text-slate-500']">{{ g.label }}</span>
                <span class="text-[10px] text-slate-300 ml-auto">{{ g.accounts.length }}</span>
            </div>
        </div>

        <div v-if="g.isExpanded" class="ml-6 space-y-0.5 border-l border-slate-100 pl-2">
            <div v-for="acc in g.accounts" :key="acc.id" 
                 class="flex items-center gap-2 p-1.5 cursor-pointer hover:bg-slate-50 rounded group"
                 @click="toggleAccount(acc.id)">
                
                <div :style="selectedIds.has(acc.id) ? { backgroundColor: getAccountColor(acc.id), borderColor: getAccountColor(acc.id) } : {}"
                     :class="['w-3 h-3 border rounded transition-colors', selectedIds.has(acc.id) ? '' : 'border-slate-300 bg-white']">
                </div>
                
                <span :class="['truncate text-xs', selectedIds.has(acc.id) ? 'text-slate-700 font-medium' : 'text-slate-400']" :title="acc.name">{{ acc.name }}</span>
            </div>
        </div>
    </div>
  </div>
</template>
