export const ACCOUNT_TYPES = [
    "Cash",
    "Investment",
    "Property",
    "Mortgage",
    "Loan",
    "RSU Grant"
];

export function formatCurrency(pence, currency = 'GBP') {
    if (pence === undefined || pence === null) return '£0.00';
    const value = pence / 100;
    const formatter = new Intl.NumberFormat('en-GB', {
        style: 'currency',
        currency: currency || 'GBP',
    });
    return formatter.format(value);
}

export function formatDate(dateString) {
    if (!dateString) return '';
    return new Date(dateString).toLocaleDateString('en-GB');
}

// UPDATED: Now accepts wrapper to check for Pensions/Locked wrappers
export function isAccountTypeLocked(type, wrapper) {
    const lockedTypes = ["Property", "Mortgage", "Loan", "RSU Grant"];
    const lockedWrappers = ["Pension", "Junior ISA", "Lifetime ISA"]; // LISA usually treated as locked for retirement or house
    
    if (lockedTypes.includes(type)) return true;
    if (wrapper && lockedWrappers.includes(wrapper)) return true;
    
    return false;
}

export function calculatePMT(principal, annualRate, years) {
    if (years === 0) return 0;
    if (annualRate === 0) return principal / (years * 12);
    const monthlyRate = annualRate / 100 / 12;
    const numPayments = years * 12;
    const numerator = principal * (monthlyRate * Math.pow(1 + monthlyRate, numPayments));
    const denominator = Math.pow(1 + monthlyRate, numPayments) - 1;
    return numerator / denominator;
}

export function calculateRemainingBalance(principal, annualRate, totalYears, yearsElapsed) {
    const monthlyRate = annualRate / 100 / 12;
    const numPayments = totalYears * 12;
    const paymentsMade = yearsElapsed * 12;
    const pmt = calculatePMT(principal, annualRate, totalYears);
    if (monthlyRate === 0) return principal - (pmt * paymentsMade);
    const futureValue = principal * Math.pow(1 + monthlyRate, paymentsMade);
    const paymentsValue = (pmt * (Math.pow(1 + monthlyRate, paymentsMade) - 1)) / monthlyRate;
    return futureValue - paymentsValue;
}

export function escapeAttr(str) {
    if (!str) return '';
    return str.replace(/"/g, '&quot;');
}
