<script setup>
import { useSimulationStore } from '../stores/simulation'
import { RotateCcw, Clock } from 'lucide-vue-next'

const store = useSimulationStore()
const emit = defineEmits(['rollback'])

const restore = (snapshot) => {
    // Pass description to store so it appears in new history entry
    store.restoreSnapshot(snapshot.scenarioSnapshot, `Restored: ${snapshot.description}`)
    emit('rollback')
}
</script>

<template>
    <div class="space-y-4">
        <div v-if="store.history.length === 0" class="text-center py-10 text-slate-400 italic">
            No changes made in this session.
        </div>
        
        <div v-for="(snap, idx) in store.history" :key="idx" class="bg-white border border-slate-200 rounded-lg p-3 flex justify-between items-center shadow-sm">
            <div>
                <div class="text-sm font-semibold text-slate-900">{{ snap.description }}</div>
                <div class="text-xs text-slate-500 flex items-center gap-1">
                    <Clock class="w-3 h-3" /> {{ snap.timestamp.toLocaleTimeString() }}
                </div>
            </div>
            <button @click="restore(snap)" class="text-xs bg-slate-100 hover:bg-slate-200 text-slate-700 px-2 py-1.5 rounded flex items-center gap-1 transition-colors">
                <RotateCcw class="w-3 h-3" /> Restore
            </button>
        </div>
    </div>
</template>
