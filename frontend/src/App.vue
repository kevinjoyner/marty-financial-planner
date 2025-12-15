<script setup>
import { onMounted, ref } from 'vue'
import { RouterLink, RouterView, useRoute } from 'vue-router'
import { LayoutDashboard, Wallet, ArrowRightLeft, Landmark, Zap, Workflow, FolderOpen, History, HelpCircle, Scale } from 'lucide-vue-next'
import ModellingBar from './components/ModellingBar.vue'
import Drawer from './components/Drawer.vue'
import GuideView from './views/GuideView.vue'
import HistoryView from './views/HistoryView.vue'
import { useSimulationStore } from './stores/simulation'

const store = useSimulationStore()
const route = useRoute()
const showGuide = ref(false)
const showHistory = ref(false)

onMounted(() => {
    store.init()
})

const navClass = (name) => {
    const isActive = route.name === name;
    return `w-10 h-10 rounded-lg flex items-center justify-center transition-all duration-200 ${
        isActive ? 'bg-primary/10 text-primary shadow-sm ring-1 ring-primary/20' : 'text-slate-400 hover:bg-slate-50 hover:text-slate-600'
    }`
}
</script>

<template>
  <div class="flex h-screen w-full bg-slate-50 text-slate-800 font-sans">
    
    <nav class="w-[70px] bg-white border-r border-slate-200 flex flex-col items-center py-6 z-20 flex-shrink-0">
        <div class="mb-8 text-primary"><Zap class="w-8 h-8 fill-current" /></div>
        
        <div class="space-y-4 w-full flex flex-col items-center">
            <RouterLink to="/" :class="navClass('dashboard')" title="Dashboard"><LayoutDashboard class="w-5 h-5" /></RouterLink>
            <RouterLink to="/accounts" :class="navClass('accounts')" title="Accounts & Assets"><Landmark class="w-5 h-5" /></RouterLink>
            <RouterLink to="/income" :class="navClass('income')" title="Income"><Wallet class="w-5 h-5" /></RouterLink>
            <RouterLink to="/transactions" :class="navClass('transactions')" title="Transactions"><ArrowRightLeft class="w-5 h-5" /></RouterLink>
            <RouterLink to="/tax" :class="navClass('tax')" title="Tax & People"><Scale class="w-5 h-5" /></RouterLink>
            <RouterLink to="/automation" :class="navClass('automation')" title="Automation Rules"><Workflow class="w-5 h-5" /></RouterLink>

            <button @click="showHistory = true" :class="navClass('history')" title="History">
                <History class="w-5 h-5" />
            </button>
        </div>

        <div class="mt-auto flex flex-col gap-4 items-center">
            <RouterLink to="/scenarios" :class="navClass('scenarios')" title="Scenarios"><FolderOpen class="w-5 h-5" /></RouterLink>
            <button @click="showGuide = true" :class="navClass('guide')" title="Guide"><HelpCircle class="w-5 h-5" /></button>
        </div>
    </nav>

    <main class="flex-1 overflow-y-auto px-8 pt-8 pb-8 relative">
        <RouterView />
    </main>

    <ModellingBar />

    <Drawer :isOpen="showGuide" title="User Guide" :actions="false" @close="showGuide = false">
        <GuideView />
    </Drawer>

    <Drawer :isOpen="showHistory" title="Session History" :actions="false" @close="showHistory = false">
        <HistoryView @rollback="showHistory = false" />
    </Drawer>

  </div>
</template>
