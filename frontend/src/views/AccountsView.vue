<script setup>
import { onMounted, computed, ref } from 'vue'
import { useSimulationStore } from '../stores/simulation'
import { Landmark, TrendingUp, PiggyBank, Home, Pencil, Plus } from 'lucide-vue-next'
import PinToggle from '../components/PinToggle.vue'
import Drawer from '../components/Drawer.vue'
import { formatCurrency } from '../utils/format'

const store = useSimulationStore()
const editingAccount = ref(null)
const form = ref({}) 

onMounted(() => { if (!store.scenario) store.init() })

const accountsByType = computed(() => {
    if (!store.scenario) return {}
    const accs = store.scenario.accounts
    
    // Logic: Explicit types are Liabilities. Negative balances are also Liabilities.
    const isLiability = (a) => a.account_type === 'Mortgage' || a.account_type === 'Loan' || a.starting_balance < 0;
    
    return {
        assets: accs.filter(a => !isLiability(a) && a.account_type !== 'RSU Grant'),
        liabilities: accs.filter(a => isLiability(a)),
        rsu: accs.filter(a => a.account_type === 'RSU Grant')
    }
})

// Helper for Dropdowns
const accountOptions = computed(() => store.scenario?.accounts.map(a => ({ id: a.id, name: a.name })) || [])

const formatPounds = (val) => formatCurrency(val)

const openEdit = (acc) => {
    editingAccount.value = acc
    form.value = { ...acc, starting_balance: acc.starting_balance / 100, original_loan_amount: acc.original_loan_amount ? acc.original_loan_amount / 100 : null }
}

const openCreate = () => {
    const newAcc = { 
        id: 'new', 
        name: 'New Account', 
        account_type: 'Cash', 
        tax_wrapper: 'None', 
        starting_balance: 0, 
        interest_rate: 0, 
        currency: 'GBP' 
    }
    editingAccount.value = newAcc
    form.value = { ...newAcc }
}

const save = async () => {
    const payload = { ...form.value }
    await store.saveEntity('account', editingAccount.value.id, payload, `Saved ${form.value.name}`)
    editingAccount.value = null 
}

const remove = async () => {
    const success = await store.deleteEntity('account', editingAccount.value.id);
    if (success) editingAccount.value = null;
}
</script>

<template>
    <div class="flex flex-col min-h-full pb-24 max-w-5xl mx-auto w-full relative pb-24">
        <header class="mb-8 flex justify-between items-center">
            <div>
                <h1 class="text-2xl font-semibold text-slate-900 tracking-tight">Accounts</h1>
                <p class="text-sm text-slate-500 mt-1">Assets, liabilities, and equity.</p>
            </div>
            <button @click="openCreate" class="flex items-center gap-2 bg-slate-900 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-slate-800 transition-colors shadow-sm">
                <Plus class="w-4 h-4" /> Add Account
            </button>
        </header>
        
        <div v-if="!store.scenario" class="text-slate-400 italic">Loading...</div>
        <div v-else class="space-y-8">
            <div v-if="accountsByType.liabilities && accountsByType.liabilities.length > 0">
                <h3 class="text-sm font-bold text-red-600 uppercase tracking-wider mb-3 px-1">Liabilities</h3>
                <div class="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
                    <table class="w-full text-left text-sm">
                        <thead class="bg-slate-50 border-b border-slate-200 text-slate-500">
                            <tr><th class="px-6 py-3 font-medium">Account Name</th><th class="px-6 py-3 font-medium">Type</th><th class="px-6 py-3 font-medium text-right">Balance</th><th class="px-6 py-3 font-medium text-right">Rate</th><th class="px-6 py-3 font-medium text-center w-16"></th></tr>
                        </thead>
                        <tbody class="divide-y divide-slate-100">
                            <tr v-for="acc in accountsByType.liabilities" :key="acc.id" class="group hover:bg-slate-50/50 transition-colors">
                                <td class="px-6 py-4"><div class="flex items-center gap-3"><div class="w-8 h-8 rounded-full bg-red-100 text-red-600 flex items-center justify-center"><Home class="w-4 h-4" /></div><div class="font-medium text-slate-900">{{ acc.name }}</div></div></td>
                                <td class="px-6 py-4 text-slate-500">{{ acc.account_type === 'Mortgage' ? 'Mortgage / Loan' : acc.account_type }}</td>
                                <td class="px-6 py-4 text-right font-bold text-slate-700">{{ formatPounds(acc.starting_balance) }}</td>
                                <td class="px-6 py-4 text-right font-mono text-slate-600">{{ acc.interest_rate }}%</td>
                                <td class="px-6 py-4 text-center"><button @click="openEdit(acc)" class="p-1.5 text-slate-300 hover:text-primary hover:bg-slate-100 rounded-md transition-all"><Pencil class="w-4 h-4" /></button></td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
            <div>
                <h3 class="text-sm font-bold text-emerald-600 uppercase tracking-wider mb-3 px-1">Assets</h3>
                <div class="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
                    <table class="w-full text-left text-sm">
                        <thead class="bg-slate-50 border-b border-slate-200 text-slate-500">
                            <tr><th class="px-6 py-3 font-medium">Account Name</th><th class="px-6 py-3 font-medium">Type</th><th class="px-6 py-3 font-medium text-right">Balance</th><th class="px-6 py-3 font-medium text-center w-16"></th></tr>
                        </thead>
                        <tbody class="divide-y divide-slate-100">
                            <tr v-for="acc in accountsByType.assets" :key="acc.id" class="group hover:bg-slate-50/50 transition-colors">
                                <td class="px-6 py-4"><div class="flex items-center gap-3"><div class="w-8 h-8 rounded-full bg-emerald-100 text-emerald-600 flex items-center justify-center"><Landmark class="w-4 h-4" /></div><div class="font-medium text-slate-900">{{ acc.name }}</div></div></td>
                                <td class="px-6 py-4 text-slate-500">{{ acc.account_type }} <span v-if="acc.tax_wrapper && acc.tax_wrapper !== 'None'" class="ml-1 text-xs bg-slate-100 px-1.5 py-0.5 rounded text-slate-600">{{ acc.tax_wrapper }}</span></td>
                                <td class="px-6 py-4 text-right font-bold text-slate-700">{{ formatPounds(acc.starting_balance) }}</td>
                                <td class="px-6 py-4 text-center"><button @click="openEdit(acc)" class="p-1.5 text-slate-300 hover:text-primary hover:bg-slate-100 rounded-md transition-all"><Pencil class="w-4 h-4" /></button></td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <Drawer :isOpen="!!editingAccount" :title="editingAccount?.name || 'New Account'" @close="editingAccount = null" @save="save">
            <div v-if="editingAccount" class="space-y-6">
                <div><label class="block text-sm font-medium text-slate-700 mb-1">Account Name</label><input type="text" v-model="form.name" class="w-full border border-slate-300 rounded-md px-3 py-2 text-sm"></div>
                
                <div class="grid grid-cols-2 gap-4">
                    <div>
                        <label class="block text-sm font-medium text-slate-700 mb-1">Type</label>
                        <select v-model="form.account_type" class="w-full border border-slate-300 rounded-md px-3 py-2 text-sm">
                            <option value="Cash">Cash</option>
                            <option value="Investment">Investment</option>
                            <option value="Main Residence">Main Residence</option>
                            <option value="Property">Property</option>
                            <option value="Mortgage">Mortgage / Loan</option>
                        </select>
                    </div>
                    <div><label class="block text-sm font-medium text-slate-700 mb-1">Tax Wrapper</label><select v-model="form.tax_wrapper" class="w-full border border-slate-300 rounded-md px-3 py-2 text-sm"><option value="None">None</option><option value="ISA">ISA</option><option value="Pension">Pension</option><option value="Lifetime ISA">Lifetime ISA</option></select></div>
                </div>

                <div v-if="form.account_type === 'Mortgage'" class="space-y-6 pt-2">
                    <div class="p-4 bg-slate-50 rounded-lg border border-slate-200 space-y-4"><h4 class="text-xs font-bold text-slate-500 uppercase tracking-wide">Loan Details</h4>
                        <div class="grid grid-cols-2 gap-4">
                            <div><div class="flex justify-between items-center mb-1"><label class="block text-sm font-medium text-slate-700">Interest (%)</label><PinToggle v-if="editingAccount.id !== 'new'" :item="{ id: `acc-${editingAccount.id}-rate`, realId: editingAccount.id, type: 'account', field: 'interest_rate', label: `${editingAccount.name} Rate`, value: editingAccount.interest_rate, format: 'percent' }" /></div><input type="number" v-model="form.interest_rate" class="w-full border border-slate-300 rounded-md px-3 py-2 text-sm"></div>
                            <div><div class="flex justify-between items-center mb-1"><label class="block text-sm font-medium text-slate-700">Term (Years)</label><PinToggle v-if="editingAccount.id !== 'new'" :item="{ id: `acc-${editingAccount.id}-term`, realId: editingAccount.id, type: 'account', field: 'amortisation_period_years', label: `${editingAccount.name} Term`, value: editingAccount.amortisation_period_years, format: 'number' }" /></div><input type="number" v-model="form.amortisation_period_years" class="w-full border border-slate-300 rounded-md px-3 py-2 text-sm"></div>
                        </div>
                        <div class="grid grid-cols-2 gap-4">
                            <div><div class="flex justify-between items-center mb-1"><label class="block text-sm font-medium text-slate-700">Original Loan</label><PinToggle v-if="editingAccount.id !== 'new'" :item="{ id: `acc-${editingAccount.id}-original`, realId: editingAccount.id, type: 'account', field: 'original_loan_amount', label: `${editingAccount.name} Original`, value: editingAccount.original_loan_amount, format: 'currency' }" /></div><div class="relative"><span class="absolute left-3 top-2 text-slate-400">£</span><input type="number" v-model="form.original_loan_amount" class="w-full border border-slate-300 rounded-md pl-7 pr-3 py-2 text-sm"></div></div>
                            <div><div class="flex justify-between items-center mb-1"><label class="block text-sm font-medium text-slate-700">Current Balance</label><PinToggle v-if="editingAccount.id !== 'new'" :item="{ id: `acc-${editingAccount.id}-balance`, realId: editingAccount.id, type: 'account', field: 'starting_balance', label: `${editingAccount.name} Balance`, value: editingAccount.starting_balance / 100, format: 'currency' }" /></div><div class="relative"><span class="absolute left-3 top-2 text-slate-400">£</span><input type="number" v-model="form.starting_balance" class="w-full border border-slate-300 rounded-md pl-7 pr-3 py-2 text-sm text-red-600 font-medium bg-white"></div></div>
                        </div>
                        <div><div class="flex justify-between items-center mb-1"><label class="block text-sm font-medium text-slate-700">Start Date</label><PinToggle v-if="editingAccount.id !== 'new'" :item="{ id: `acc-${editingAccount.id}-start`, realId: editingAccount.id, type: 'account', field: 'mortgage_start_date', label: `${editingAccount.name} Start`, value: editingAccount.mortgage_start_date, inputType: 'date' }" /></div><input type="date" v-model="form.mortgage_start_date" class="w-full border border-slate-300 rounded-md px-3 py-2 text-sm"></div>
                    </div>
                    <div class="p-4 bg-indigo-50 rounded-lg border border-indigo-100 space-y-4"><h4 class="text-xs font-bold text-indigo-500 uppercase tracking-wide">Fixed Rate Deal</h4>
                        <div class="grid grid-cols-2 gap-4">
                            <div><div class="flex justify-between items-center mb-1"><label class="block text-sm font-medium text-slate-700">Fixed Rate (%)</label><PinToggle v-if="editingAccount.id !== 'new'" :item="{ id: `acc-${editingAccount.id}-fixedrate`, realId: editingAccount.id, type: 'account', field: 'fixed_interest_rate', label: `${editingAccount.name} Fixed Rate`, value: editingAccount.fixed_interest_rate, format: 'percent' }" /></div><input type="number" v-model="form.fixed_interest_rate" class="w-full border border-slate-300 rounded-md px-3 py-2 text-sm"></div>
                            <div><div class="flex justify-between items-center mb-1"><label class="block text-sm font-medium text-slate-700">Fixed Years</label><PinToggle v-if="editingAccount.id !== 'new'" :item="{ id: `acc-${editingAccount.id}-fixedterm`, realId: editingAccount.id, type: 'account', field: 'fixed_rate_period_years', label: `${editingAccount.name} Fixed Term`, value: editingAccount.fixed_rate_period_years, format: 'number' }" /></div><input type="number" v-model="form.fixed_rate_period_years" class="w-full border border-slate-300 rounded-md px-3 py-2 text-sm"></div>
                        </div>
                    </div>
                    <div><div class="flex justify-between items-center mb-1"><label class="block text-sm font-medium text-slate-700">Pay From Account</label><PinToggle v-if="editingAccount.id !== 'new'" :item="{ id: `acc-${editingAccount.id}-payfrom`, realId: editingAccount.id, type: 'account', field: 'payment_from_account_id', label: `${editingAccount.name} Pay From`, value: editingAccount.payment_from_account_id, inputType: 'select', options: accountOptions }" /></div><select v-model="form.payment_from_account_id" class="w-full border border-slate-300 rounded-md px-3 py-2 text-sm"><option :value="null">-- None --</option><option v-for="a in accountOptions" :key="a.id" :value="a.id">{{ a.name }}</option></select></div>
                </div>

                <div v-else class="space-y-4 pt-2">
                    <div><div class="flex justify-between items-center mb-1"><label class="block text-sm font-medium text-slate-700">Balance</label><PinToggle v-if="editingAccount.id !== 'new'" :item="{ id: `acc-${editingAccount.id}-balance`, realId: editingAccount.id, type: 'account', field: 'starting_balance', label: `${editingAccount.name} Balance`, value: editingAccount.starting_balance / 100, format: 'currency' }" /></div><div class="relative"><span class="absolute left-3 top-2 text-slate-400">£</span><input type="number" v-model="form.starting_balance" class="w-full border border-slate-300 rounded-md pl-7 pr-3 py-2 text-sm"></div></div>
                    <div><div class="flex justify-between items-center mb-1"><label class="block text-sm font-medium text-slate-700">Growth / Interest Rate (%)</label><PinToggle v-if="editingAccount.id !== 'new'" :item="{ id: `acc-${editingAccount.id}-rate`, realId: editingAccount.id, type: 'account', field: 'interest_rate', label: `${editingAccount.name} Rate`, value: editingAccount.interest_rate, format: 'percent' }" /></div><input type="number" v-model="form.interest_rate" class="w-full border border-slate-300 rounded-md px-3 py-2 text-sm"></div>
                </div>
                
                <div><label class="block text-sm font-medium text-slate-700 mb-1">Notes</label><textarea v-model="form.notes" rows="3" class="w-full border border-slate-300 rounded-md px-3 py-2 text-sm"></textarea></div>
                <div v-if="editingAccount.id !== 'new'" class="pt-6 border-t border-slate-100">
                    <button type="button" @click="remove" class="w-full py-2 bg-red-50 text-red-600 hover:bg-red-100 rounded-md font-medium text-sm transition-colors">Delete Account</button>
                </div>
            </div>
        </Drawer>
    </div>
</template>
