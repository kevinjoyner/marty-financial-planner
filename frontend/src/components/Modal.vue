<script setup>
import { X } from 'lucide-vue-next'

defineProps({
  isOpen: Boolean,
  title: String,
  maxWidth: {
    type: String,
    default: 'max-w-4xl'
  }
})

const emit = defineEmits(['close'])
</script>

<template>
  <Teleport to="body">
    <div v-if="isOpen" class="fixed inset-0 z-[100] flex items-center justify-center p-4">
        
        <div class="absolute inset-0 bg-slate-900/20 backdrop-blur-sm transition-opacity" @click="$emit('close')"></div>

        <div :class="['relative w-full bg-white rounded-xl shadow-2xl flex flex-col max-h-[90vh] overflow-hidden transform transition-all border border-slate-200', maxWidth]">
            
            <div class="flex items-center justify-between px-6 py-4 border-b border-slate-100 bg-slate-50/50">
                <h2 class="text-lg font-semibold text-slate-900">{{ title }}</h2>
                <button @click="$emit('close')" class="text-slate-400 hover:text-slate-700 p-1 rounded-md hover:bg-slate-200 transition-colors">
                    <X class="w-5 h-5" />
                </button>
            </div>

            <div class="flex-1 overflow-y-auto p-0 bg-white">
                <slot></slot>
            </div>
        </div>
    </div>
  </Teleport>
</template>
