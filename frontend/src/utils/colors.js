const PALETTE = [
    '#2563eb', // Blue
    '#16a34a', // Green
    '#dc2626', // Red
    '#d97706', // Amber
    '#9333ea', // Purple
    '#0891b2', // Cyan
    '#db2777', // Pink
    '#4f46e5', // Indigo
    '#059669', // Emerald
    '#b91c1c'  // Dark Red
];

export function getAccountColor(id) {
    const idx = typeof id === 'number' ? id : 0;
    return PALETTE[idx % PALETTE.length];
}

export const CATEGORY_COLORS = {
    'liquid': '#16a34a',      // Green (Assets)
    'illiquid': '#2563eb',    // Blue (Pension/Locked)
    'liabilities': '#dc2626', // Red (Debt)
    'unvested': '#9333ea'     // Purple (RSU)
};

export function getCategoryColor(categoryKey) {
    return CATEGORY_COLORS[categoryKey] || '#64748b';
}
