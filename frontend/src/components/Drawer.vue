<script setup>
import { X } from 'lucide-vue-next'

defineProps({
  isOpen: Boolean,
  title: String,
  actions: {
    type: Boolean,
    default: true
  }
})

const emit = defineEmits(['close', 'save'])
</script>

<template>
  <Teleport to="body">
    <div v-if="isOpen" class="fixed inset-0 z-[100] flex justify-end overflow-hidden">
        
        <div class="absolute inset-0 bg-slate-900/5 transition-opacity" @click="$emit('close')"></div>

        <div class="relative w-full max-w-md bg-white h-full shadow-2xl flex flex-col border-l border-slate-200 transform transition-transform duration-300 ease-in-out">
            
            <div class="flex items-center justify-between p-6 border-b border-slate-100 bg-slate-50/50">
                <h2 class="text-lg font-semibold text-slate-900">{{ title }}</h2>
                <button @click="$emit('close')" class="text-slate-400 hover:text-slate-700 p-1 rounded-md hover:bg-slate-200 transition-colors">
                    <X class="w-5 h-5" />
                </button>
            </div>

            <div class="flex-1 overflow-y-auto p-6">
                <slot></slot>
            </div>

            <div v-if="actions" class="p-6 border-t border-slate-100 bg-slate-50 flex justify-end gap-3">
                <button @click="$emit('close')" class="px-4 py-2 text-sm font-medium text-slate-600 hover:text-slate-900 hover:bg-slate-200 rounded-md transition-colors">Cancel</button>
                <button @click="$emit('save')" class="px-4 py-2 text-sm font-medium text-white bg-primary hover:bg-secondary rounded-md shadow-sm transition-colors">Save Changes</button>
            </div>
        </div>
    </div>
  </Teleport>
</template>
