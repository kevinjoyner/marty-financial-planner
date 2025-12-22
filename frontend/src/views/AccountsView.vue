<script setup>
import { onMounted, computed, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useSimulationStore } from '../stores/simulation'
import { Landmark, Home, Pencil, Plus, Users, UserPlus, Lock, Gift, Trash2 } from 'lucide-vue-next'
import PinToggle from '../components/PinToggle.vue'
import Drawer from '../components/Drawer.vue'
import { formatCurrency } from '../utils/format'

const store = useSimulationStore()
const router = useRouter()
const editingAccount = ref(null)
const form = ref({}) 
const vestingSchedule = ref([]) 

onMounted(() => { if (!store.scenario) store.init() })

const owners = computed(() => store.scenario?.owners || [])
const hasOwners = computed(() => owners.value.length > 0)

const isJointAccount = computed(() => form.value.owner_ids && form.value.owner_ids.length > 1)

watch(() => form.value.owner_ids, (newIds) => {
    if (newIds && newIds.length > 1) {
        if (form.value.tax_wrapper !== 'None') {
            form.value.tax_wrapper = 'None';
        }
    }
})

const accountsByType = computed(() => {
    if (!store.scenario) return {}
    const accs = store.scenario.accounts
    
    const isLiability = (a) => a.account_type === 'Mortgage' || a.account_type === 'Loan' || a.starting_balance < 0;
    
    return {
        assets: accs.filter(a => !isLiability(a) && a.account_type !== 'RSU Grant'),
        liabilities: accs.filter(a => isLiability(a)),
        rsu: accs.filter(a => a.account_type === 'RSU Grant')
    }
})

const accountOptions = computed(() => store.scenario?.accounts.map(a => ({ id: a.id, name: a.name })) || [])
const formatPounds = (val) => formatCurrency(val)

const openEdit = (acc) => {
    editingAccount.value = acc
    const currentOwnerIds = acc.owners ? acc.owners.map(o => o.id) : []
    
    let vs = [];
    if (acc.vesting_schedule) {
        vs = Array.isArray(acc.vesting_schedule) ? acc.vesting_schedule : JSON.parse(acc.vesting_schedule);
    }
    vestingSchedule.value = vs;

    form.value = { 
        ...acc, 
        starting_balance: acc.starting_balance / 100, 
        original_loan_amount: acc.original_loan_amount ? acc.original_loan_amount / 100 : null,
        owner_ids: currentOwnerIds,
        unit_price: acc.unit_price ? acc.unit_price / 100 : 0,
        vesting_cadence: acc.vesting_cadence || 'monthly'
    }
}

const openCreate = () => {
    const newAcc = { 
        id: 'new', 
        name: 'New Account', 
        account_type: 'Cash', 
        tax_wrapper: 'None', 
        starting_balance: 0, 
        interest_rate: 0, 
        currency: 'GBP',
        owner_ids: [],
        grant_date: new Date().toISOString().split('T')[0],
        unit_price: 0,
        vesting_cadence: 'monthly'
    }
    if (owners.value.length === 1) {
        newAcc.owner_ids = [owners.value[0].id]
    }
    vestingSchedule.value = [{ year: 1, percent: 25 }, { year: 2, percent: 25 }, { year: 3, percent: 25 }, { year: 4, percent: 25 }];
    editingAccount.value = newAcc
    form.value = { ...newAcc }
}

const addTranche = () => {
    const nextYear = vestingSchedule.value.length + 1;
    vestingSchedule.value.push({ year: nextYear, percent: 0 });
}

const removeTranche = (index) => {
    vestingSchedule.value.splice(index, 1);
}

const save = async () => {
    const payload = { ...form.value }
    if (payload.account_type === 'RSU Grant') {
        payload.vesting_schedule = vestingSchedule.value; 
        if (payload.unit_price) payload.unit_price = Math.round(payload.unit_price * 100);
    }
    
    await store.saveEntity('account', editingAccount.value.id, payload, `Saved ${form.value.name}`)
    editingAccount.value = null 
}

const remove = async () => {
    const success = await store.deleteEntity('account', editingAccount.value.id);
    if (success) editingAccount.value = null;
}

const goToPeople = () => router.push('/tax')
</script>

<template>
    <div class="flex flex-col min-h-full pb-24 max-w-5xl mx-auto w-full relative pb-24">
        <header class="mb-8 flex justify-between items-center">
            <div>
                <h1 class="text-2xl font-semibold text-slate-900 tracking-tight">Accounts</h1>
                <p class="text-sm text-slate-500 mt-1">Assets, liabilities, and equity.</p>
            </div>
            
            <button v-if="hasOwners" @click="openCreate" class="flex items-center gap-2 bg-slate-900 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-slate-800 transition-colors shadow-sm">
                <Plus class="w-4 h-4" /> Add Account
            </button>
        </header>
        
        <div v-if="!store.scenario" class="text-slate-400 italic">Loading...</div>
        
        <div v-else-if="!hasOwners" class="flex flex-col items-center justify-center py-20 bg-slate-50 rounded-xl border border-dashed border-slate-300 text-center">
            <div class="w-16 h-16 bg-slate-100 rounded-full flex items-center justify-center mb-4">
                <Users class="w-8 h-8 text-slate-400" />
            </div>
            <h3 class="text-lg font-bold text-slate-900 mb-2">Who does this plan belong to?</h3>
            <p class="text-slate-500 max-w-md mb-6">Before you can add accounts or income, you need to define the people in this scenario.</p>
            <button @click="goToPeople" class="flex items-center gap-2 bg-primary text-white px-6 py-3 rounded-md font-bold shadow-md hover:bg-primary/90 transition-all">
                <UserPlus class="w-5 h-5" /> Add a Person
            </button>
        </div>

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

            <div v-if="accountsByType.rsu && accountsByType.rsu.length > 0">
                <h3 class="text-sm font-bold text-[#635bff] uppercase tracking-wider mb-3 px-1">Stock Grants (Unvested)</h3>
                <div class="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
                    <table class="w-full text-left text-sm">
                        <thead class="bg-slate-50 border-b border-slate-200 text-slate-500">
                            <tr><th class="px-6 py-3 font-medium">Grant Name</th><th class="px-6 py-3 font-medium">Currency</th><th class="px-6 py-3 font-medium text-right">Units</th><th class="px-6 py-3 font-medium text-center w-16"></th></tr>
                        </thead>
                        <tbody class="divide-y divide-slate-100">
                            <tr v-for="acc in accountsByType.rsu" :key="acc.id" class="group hover:bg-slate-50/50 transition-colors">
                                <td class="px-6 py-4"><div class="flex items-center gap-3"><div class="w-8 h-8 rounded-full bg-indigo-100 text-[#635bff] flex items-center justify-center"><Gift class="w-4 h-4" /></div><div class="font-medium text-slate-900">{{ acc.name }}</div></div></td>
                                <td class="px-6 py-4 text-slate-500 font-mono">{{ acc.currency }}</td>
                                <td class="px-6 py-4 text-right font-bold text-slate-700">{{ (acc.starting_balance / 100).toLocaleString() }}</td>
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
                
                <div class="bg-slate-50 p-3 rounded-md border border-slate-200">
                    <label class="block text-xs font-bold text-slate-500 uppercase mb-2">Assigned To (Ownership)</label>
                    <div class="space-y-2">
                        <label v-for="owner in owners" :key="owner.id" class="flex items-center gap-2 cursor-pointer">
                            <input type="checkbox" :value="owner.id" v-model="form.owner_ids" class="rounded border-slate-300 text-primary focus:ring-primary">
                            <span class="text-sm text-slate-700">{{ owner.name }}</span>
                        </label>
                    </div>
                    <div v-if="isJointAccount" class="mt-2 text-amber-600 text-xs flex items-center gap-1.5">
                        <Users class="w-3.5 h-3.5" />
                        <span>Joint Account: Tax Wrappers are disabled.</span>
                    </div>
                </div>

                <div class="grid grid-cols-2 gap-4">
                    <div>
                        <label class="block text-sm font-medium text-slate-700 mb-1">Type</label>
                        <select v-model="form.account_type" class="w-full border border-slate-300 rounded-md px-3 py-2 text-sm">
                            <option value="Cash">Cash</option>
                            <option value="Investment">Investment</option>
                            <option value="Main Residence">Main Residence</option>
                            <option value="Property">Property</option>
                            <option value="Mortgage">Mortgage / Loan</option>
                            <option value="RSU Grant">RSU Grant</option>
                        </select>
                    </div>
                    <div v-if="form.account_type !== 'RSU Grant'">
                        <label class="block text-sm font-medium text-slate-700 mb-1">Tax Wrapper</label>
                        <div class="relative">
                            <select v-model="form.tax_wrapper" :disabled="isJointAccount" :class="['w-full border rounded-md px-3 py-2 text-sm', isJointAccount ? 'bg-slate-100 text-slate-400 border-slate-200' : 'border-slate-300 bg-white']">
                                <option value="None">None</option>
                                <option value="ISA">ISA</option><option value="Pension">Pension</option><option value="Lifetime ISA">Lifetime ISA</option>
                            </select>
                            <Lock v-if="isJointAccount" class="w-3.5 h-3.5 text-slate-400 absolute right-3 top-3" />
                        </div>
                    </div>
                    <div v-else>
                        <label class="block text-sm font-medium text-slate-700 mb-1">Currency</label>
                        <select v-model="form.currency" class="w-full border border-slate-300 rounded-md px-3 py-2 text-sm">
                            <option value="GBP">GBP (£)</option>
                            <option value="USD">USD ($)</option>
                        </select>
                    </div>
                </div>

                <div v-if="form.account_type === 'RSU Grant'" class="space-y-6 pt-2">
                    <div class="p-4 bg-indigo-50 rounded-lg border border-indigo-100 space-y-4">
                        <h4 class="text-xs font-bold text-indigo-500 uppercase tracking-wide">Grant Details</h4>
                        
                        <div class="grid grid-cols-2 gap-4">
                            <div><div class="flex justify-between items-center mb-1"><label class="block text-sm font-medium text-slate-700">Grant Date</label><PinToggle v-if="editingAccount.id !== 'new'" :item="{ id: `acc-${editingAccount.id}-grant`, realId: editingAccount.id, type: 'account', field: 'grant_date', label: `${editingAccount.name} Grant`, value: editingAccount.grant_date, inputType: 'date' }" /></div><input type="date" v-model="form.grant_date" class="w-full border border-slate-300 rounded-md px-3 py-2 text-sm"></div>
                            <div><div class="flex justify-between items-center mb-1"><label class="block text-sm font-medium text-slate-700">Original Units</label><PinToggle v-if="editingAccount.id !== 'new'" :item="{ id: `acc-${editingAccount.id}-units`, realId: editingAccount.id, type: 'account', field: 'starting_balance', label: `${editingAccount.name} Units`, value: editingAccount.starting_balance / 100, format: 'number' }" /></div><input type="number" v-model="form.starting_balance" class="w-full border border-slate-300 rounded-md px-3 py-2 text-sm font-mono"></div>
                        </div>

                        <div class="grid grid-cols-2 gap-4">
                            <div><div class="flex justify-between items-center mb-1"><label class="block text-sm font-medium text-slate-700">Grant Price</label><PinToggle v-if="editingAccount.id !== 'new'" :item="{ id: `acc-${editingAccount.id}-price`, realId: editingAccount.id, type: 'account', field: 'unit_price', label: `${editingAccount.name} Price`, value: editingAccount.unit_price / 100, format: 'currency' }" /></div><div class="relative"><span class="absolute left-3 top-2 text-slate-400">{{ form.currency === 'USD' ? '$' : '£' }}</span><input type="number" v-model="form.unit_price" class="w-full border border-slate-300 rounded-md pl-7 pr-3 py-2 text-sm"></div></div>
                            <div><div class="flex justify-between items-center mb-1"><label class="block text-sm font-medium text-slate-700">Growth Rate (%)</label><PinToggle v-if="editingAccount.id !== 'new'" :item="{ id: `acc-${editingAccount.id}-rate`, realId: editingAccount.id, type: 'account', field: 'interest_rate', label: `${editingAccount.name} Growth`, value: editingAccount.interest_rate, format: 'percent' }" /></div><input type="number" v-model="form.interest_rate" class="w-full border border-slate-300 rounded-md px-3 py-2 text-sm"></div>
                        </div>

                        <div class="grid grid-cols-2 gap-4">
                            <div>
                                <label class="block text-sm font-medium text-slate-700 mb-1">Vesting Cadence</label>
                                <select v-model="form.vesting_cadence" class="w-full border border-slate-300 rounded-md px-3 py-2 text-sm bg-white">
                                    <option value="monthly">Monthly</option>
                                    <option value="quarterly">Quarterly</option>
                                </select>
                            </div>
                            <div>
                                <div class="flex justify-between items-center mb-1"><label class="block text-sm font-medium text-slate-700">Payout To (After Tax)</label><PinToggle v-if="editingAccount.id !== 'new'" :item="{ id: `acc-${editingAccount.id}-target`, realId: editingAccount.id, type: 'account', field: 'rsu_target_account_id', label: `${editingAccount.name} Target`, value: editingAccount.rsu_target_account_id, inputType: 'select', options: accountOptions }" /></div>
                                <select v-model="form.rsu_target_account_id" class="w-full border border-slate-300 rounded-md px-3 py-2 text-sm"><option :value="null">-- None --</option><option v-for="a in accountOptions" :key="a.id" :value="a.id">{{ a.name }}</option></select>
                            </div>
                        </div>
                    </div>

                    <div>
                        <div class="flex justify-between items-center mb-2">
                            <label class="block text-sm font-medium text-slate-700">Vesting Schedule (Annual % - Vests <span class="capitalize font-bold text-indigo-600">{{ form.vesting_cadence }}</span>)</label>
                            <button type="button" @click="addTranche" class="text-xs text-indigo-600 hover:text-indigo-800 font-medium flex items-center gap-1"><Plus class="w-3 h-3" /> Add Year</button>
                        </div>
                        <div class="space-y-2">
                            <div v-for="(tranche, idx) in vestingSchedule" :key="idx" class="flex items-center gap-2">
                                <span class="text-xs text-slate-500 w-12">Year {{ tranche.year }}</span>
                                <input type="number" v-model="tranche.percent" class="w-20 border border-slate-300 rounded px-2 py-1 text-sm text-right" placeholder="25">
                                <span class="text-slate-400 text-sm">%</span>
                                <button type="button" @click="removeTranche(idx)" class="ml-auto text-slate-300 hover:text-red-500"><Trash2 class="w-4 h-4" /></button>
                            </div>
                            <div v-if="vestingSchedule.length === 0" class="text-center py-4 text-xs text-slate-400 italic bg-slate-50 rounded border border-dashed border-slate-200">No vesting schedule defined.</div>
                        </div>
                    </div>
                </div>

                <div v-else-if="form.account_type === 'Mortgage'" class="space-y-6 pt-2">
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
