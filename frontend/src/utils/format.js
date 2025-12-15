export const formatCurrency = (pence) => {
    if (pence === undefined || pence === null) return '£0';
    return new Intl.NumberFormat('en-GB', { 
        style: 'currency', 
        currency: 'GBP',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
    }).format(pence / 100);
};
export const formatPercent = (val) => {
    if (val === undefined || val === null) return '0.0%';
    return `${val.toFixed(1)}%`;
};
