<script setup>
import { computed } from 'vue'
import { Pin } from 'lucide-vue-next'
import { useSimulationStore } from '../stores/simulation'

const props = defineProps({
  item: Object // { id, realId, type, field, label, value, format, inputType, options }
})

const store = useSimulationStore()

const isPinned = computed(() => {
  return store.pinnedItems.some(i => i.id === props.item.id)
})

const togglePin = () => {
  if (isPinned.value) {
    store.unpinItem(props.item.id)
  } else {
    store.pinItem(props.item)
  }
}
</script>

<template>
  <button 
    @click="togglePin" 
    class="p-1 rounded-md transition-all duration-200 focus:outline-none"
    :class="isPinned ? 'text-primary bg-primary/10' : 'text-slate-300 hover:text-slate-500 hover:bg-slate-100'"
    :title="isPinned ? 'Unpin from Modelling Bar' : 'Pin to Modelling Bar'"
  >
    <Pin class="w-3.5 h-3.5 fill-current" />
  </button>
</template>
