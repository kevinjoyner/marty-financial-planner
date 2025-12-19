<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../services/api'
import { useSimulationStore } from '../stores/simulation'
import { Folder, Copy, FileUp, Plus, ArrowRight, Trash2, Download, Pencil } from 'lucide-vue-next'
import Drawer from '../components/Drawer.vue'

const router = useRouter()
const store = useSimulationStore()
const scenarios = ref([])
const fileInput = ref(null)

const editingScenario = ref(null)
const form = ref({})

const loadList = async () => {
    try { scenarios.value = await api.getScenarios() } catch (e) { console.error(e) }
}

onMounted(() => { loadList() })

// FIX: Added 'async' and 'await' to ensure data is loaded before navigation
const openScenario = async (id) => { 
    await store.loadActiveScenario(id); 
    router.push('/') 
}

const duplicate = async (id) => { await api.duplicateScenario(id); await loadList() }

const deleteScen = async (id, name) => {
    if(!confirm(`Delete scenario "${name}"? This cannot be undone.`)) return;
    try {
        await api.deleteScenario(id);
        if(store.activeScenarioId === id) store.loadActiveScenario(null);
        await loadList();
    } catch (e) { alert("Delete failed: " + e.message); }
}

const exportScen = async (id, name) => {
    try {
        const data = await api.getScenario(id);
        const jsonStr = JSON.stringify(data, null, 2);
        const blob = new Blob([jsonStr], { type: "application/json" });
        const url = URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.href = url;
        link.download = `marty_scenario_${name.replace(/[^a-z0-9]/gi, '_').toLowerCase()}.json`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    } catch (e) { alert("Export failed"); console.error(e); }
}

const triggerImport = () => { fileInput.value.click() }

const handleFileUpload = async (event) => {
    const file = event.target.files[0]; if (!file) return;
    const reader = new FileReader();
    reader.onload = async (e) => {
        try {
            const json = JSON.parse(e.target.result);
            if (!json.name) json.name = "Imported Scenario";
            await api.importNewScenario(json);
            await loadList();
        } catch (err) { alert("Failed to import scenario: " + err.message) }
    };
    reader.readAsText(file);
}

const createNew = async () => { 
    await api.createScenario({ name: "New Scenario", start_date: new Date().toISOString().split('T')[0] }); 
    await loadList(); 
}

// --- Edit Logic ---
const openEdit = (s) => {
    editingScenario.value = s;
    form.value = { ...s };
}

const saveEdit = async () => {
    try {
        // Ensure numbers are floats
        const payload = {
            ...form.value,
            gbp_to_usd_rate: parseFloat(form.value.gbp_to_usd_rate)
        };
        await api.updateScenario(editingScenario.value.id, payload);
        editingScenario.value = null;
        await loadList();
        // Reload active if we just edited it
        if (store.activeScenarioId === payload.id) await store.loadScenario();
    } catch (e) { alert("Update failed"); console.error(e); }
}
</script>

<template>
    <div class="max-w-5xl mx-auto w-full pb-24">
        <header class="mb-8 flex justify-between items-center">
            <div><h1 class="text-2xl font-semibold text-slate-900 tracking-tight">Scenarios</h1><p class="text-sm text-slate-500 mt-1">Manage and compare different financial futures.</p></div>
            <div class="flex gap-3"><input type="file" ref="fileInput" class="hidden" accept=".json" @change="handleFileUpload" /><button @click="triggerImport" class="flex items-center gap-2 px-4 py-2 bg-white border border-slate-300 text-slate-700 text-sm font-medium rounded-md hover:bg-slate-50 transition-colors"><FileUp class="w-4 h-4" /> Import JSON</button><button @click="createNew" class="flex items-center gap-2 px-4 py-2 bg-slate-900 text-white text-sm font-medium rounded-md hover:bg-slate-800 transition-colors"><Plus class="w-4 h-4" /> New Scenario</button></div>
        </header>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <div v-for="s in scenarios" :key="s.id" class="bg-white border border-slate-200 rounded-xl p-6 shadow-sm hover:shadow-md transition-shadow group relative flex flex-col">
                <div class="flex justify-between items-start mb-4">
                    <div class="w-10 h-10 rounded-full bg-blue-50 text-blue-600 flex items-center justify-center"><Folder class="w-5 h-5" /></div>
                    <div class="opacity-0 group-hover:opacity-100 transition-opacity flex gap-1">
                        <button @click.stop="openEdit(s)" class="text-slate-400 hover:text-blue-600 p-2" title="Edit Settings"><Pencil class="w-4 h-4" /></button>
                        <button @click.stop="exportScen(s.id, s.name)" class="text-slate-400 hover:text-blue-600 p-2" title="Export JSON"><Download class="w-4 h-4" /></button>
                        <button @click.stop="duplicate(s.id)" class="text-slate-400 hover:text-blue-600 p-2" title="Duplicate"><Copy class="w-4 h-4" /></button>
                        <button @click.stop="deleteScen(s.id, s.name)" class="text-slate-400 hover:text-red-600 p-2" title="Delete"><Trash2 class="w-4 h-4" /></button>
                    </div>
                </div>
                <div class="mb-6 flex-1">
                    <div class="flex items-center gap-2 mb-1">
                        <h3 class="text-lg font-semibold text-slate-900 truncate" :title="s.name">{{ s.name }}</h3>
                        <span v-if="s.id === store.activeScenarioId" class="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-bold bg-green-100 text-green-700 uppercase tracking-wide">Active</span>
                    </div>
                    <p class="text-xs text-slate-500 line-clamp-2 mb-2">{{ s.description }}</p>
                    <div class="flex gap-4 text-xs text-slate-400 font-mono">
                        <span>Start: {{ s.start_date }}</span>
                        <span>Rate: {{ s.gbp_to_usd_rate }}</span>
                    </div>
                </div>
                <button @click="openScenario(s.id)" class="w-full py-2 flex items-center justify-center gap-2 bg-slate-50 text-slate-700 font-medium text-sm rounded-lg hover:bg-slate-100 transition-colors group-hover:bg-blue-600 group-hover:text-white mt-auto">Open Scenario <ArrowRight class="w-4 h-4" /></button>
            </div>
        </div>

        <Drawer :isOpen="!!editingScenario" title="Edit Scenario" @close="editingScenario = null" @save="saveEdit">
            <div v-if="editingScenario" class="space-y-4">
                <div><label class="block text-sm font-medium text-slate-700 mb-1">Scenario Name</label><input type="text" v-model="form.name" class="w-full border border-slate-300 rounded-md px-3 py-2 text-sm"></div>
                <div><label class="block text-sm font-medium text-slate-700 mb-1">Description</label><input type="text" v-model="form.description" class="w-full border border-slate-300 rounded-md px-3 py-2 text-sm"></div>
                <div class="grid grid-cols-2 gap-4">
                    <div><label class="block text-sm font-medium text-slate-700 mb-1">Start Date</label><input type="date" v-model="form.start_date" class="w-full border border-slate-300 rounded-md px-3 py-2 text-sm"></div>
                    <div><label class="block text-sm font-medium text-slate-700 mb-1">GBP/USD Rate</label><input type="number" step="0.01" v-model="form.gbp_to_usd_rate" class="w-full border border-slate-300 rounded-md px-3 py-2 text-sm"></div>
                </div>
                <div><label class="block text-sm font-medium text-slate-700 mb-1">Notes</label><textarea v-model="form.notes" rows="4" class="w-full border border-slate-300 rounded-md px-3 py-2 text-sm"></textarea></div>
            </div>
        </Drawer>
    </div>
</template>
