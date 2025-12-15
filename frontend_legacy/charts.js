import { isAccountTypeLocked, formatCurrency } from './utils.js';

let projectionChart = null;

export function renderProjectionChart(canvasId, projectionData, mode, selectedAccounts, scenarioData, globalState) {
    const ctx = document.getElementById(canvasId).getContext('2d');
    if (projectionChart) projectionChart.destroy();

    const labels = projectionData.data_points.map(dp => dp.date);
    let datasets = [];
    const colors = ['#2563eb', '#dc2626', '#16a34a', '#d97706', '#9333ea', '#0891b2', '#db2777'];

    if (mode === 'aggregate') {
        const data = projectionData.data_points.map(dp => {
            return selectedAccounts.reduce((sum, accId) => sum + (dp.account_balances[accId] || 0), 0);
        });
        datasets.push({
            label: 'Total Net Worth',
            data: data,
            borderColor: colors[0],
            backgroundColor: colors[0] + '20',
            fill: true,
            tension: 0.1
        });
    } else if (mode === 'grouped') {
        const liquidIds = selectedAccounts.filter(id => {
            const acc = scenarioData.accounts.find(a => a.id === id);
            return acc && !isAccountTypeLocked(acc.account_type, acc.tax_wrapper) && acc.account_type !== 'RSU Grant';
        });
        const illiquidIds = selectedAccounts.filter(id => {
            const acc = scenarioData.accounts.find(a => a.id === id);
            return acc && isAccountTypeLocked(acc.account_type, acc.tax_wrapper) && acc.account_type !== 'RSU Grant';
        });
        const rsuIds = selectedAccounts.filter(id => {
            const acc = scenarioData.accounts.find(a => a.id === id);
            return acc && acc.account_type === 'RSU Grant';
        });

        const liquidData = projectionData.data_points.map(dp => {
            return liquidIds.reduce((sum, accId) => sum + (dp.account_balances[accId] || 0), 0);
        });
        datasets.push({
            label: 'Net Liquid Assets',
            data: liquidData,
            borderColor: '#16a34a',
            backgroundColor: '#16a34a10',
            fill: true,
            tension: 0.1
        });

        const illiquidData = projectionData.data_points.map(dp => {
            return illiquidIds.reduce((sum, accId) => sum + (dp.account_balances[accId] || 0), 0);
        });
        datasets.push({
            label: 'Illiquid Assets',
            data: illiquidData,
            borderColor: '#2563eb',
            backgroundColor: '#2563eb10',
            fill: true,
            tension: 0.1
        });

        if (rsuIds.length > 0) {
            const rsuData = projectionData.data_points.map(dp => {
                return rsuIds.reduce((sum, accId) => sum + (dp.account_balances[accId] || 0), 0);
            });
            datasets.push({
                label: 'Unvested RSUs',
                data: rsuData,
                borderColor: '#9333ea',
                backgroundColor: '#9333ea10',
                fill: true,
                tension: 0.1
            });
        }

    } else {
        selectedAccounts.forEach((accId, index) => {
            const account = scenarioData.accounts.find(a => a.id == accId);
            const name = account ? account.name : `Account ${accId}`;
            const data = projectionData.data_points.map(dp => dp.account_balances[accId] || 0);
            datasets.push({ label: name, data: data, borderColor: colors[index % colors.length], tension: 0.1 });
        });
    }

    const options = {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { mode: 'index', intersect: false },
        scales: { y: { beginAtZero: false } },
        plugins: {
            zoom: {
                zoom: { wheel: { enabled: true }, pinch: { enabled: true }, mode: 'x' },
                pan: { enabled: true, mode: 'x' }
            },
            tooltip: {
                // SORT TOOLTIPS BY VALUE (Descending)
                itemSort: (a, b) => b.raw - a.raw,
                callbacks: {
                    label: function(context) {
                        let label = context.dataset.label || '';
                        if (label) { label += ': '; }
                        if (context.parsed.y !== null) {
                            label += new Intl.NumberFormat('en-GB', { style: 'currency', currency: 'GBP' }).format(context.parsed.y);
                        }
                        return label;
                    }
                }
            }
        }
    };

    if (globalState.freezeAxis && globalState.axisMax !== null) {
        options.scales.y.max = globalState.axisMax;
    } else {
        delete options.scales.y.max;
    }

    projectionChart = new Chart(ctx, {
        type: 'line',
        data: { labels, datasets },
        options: options
    });

    let allValues = datasets.flatMap(d => d.data);
    let maxVal = Math.max(...allValues);
    if (!globalState.freezeAxis) {
        globalState.axisMax = maxVal * 1.1;
    }
}

export function renderComparisonChart(canvasId, dataA, dataB, nameA, nameB) {
    const ctx = document.getElementById(canvasId).getContext('2d');
    if (projectionChart) projectionChart.destroy();
    // ... (Comparison chart logic remains the same)
}

function downloadCSV(content, filename) {
    const csvContent = "data:text/csv;charset=utf-8," + content;
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", filename);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

export function exportChartDataToCSV(projectionData, selectedAccounts, scenarioData) {
    const rows = [];
    const header = ['Date', ...selectedAccounts.map(id => {
        const acc = scenarioData.accounts.find(a => a.id === id);
        return acc ? acc.name : `Account ${id}`;
    }), 'Total'];
    rows.push(header.join(','));

    projectionData.data_points.forEach(dp => {
        let row = [dp.date];
        let total = 0;
        selectedAccounts.forEach(id => {
            const val = dp.account_balances[id] || 0;
            row.push(val.toFixed(2));
            total += val;
        });
        row.push(total.toFixed(2));
        rows.push(row.join(','));
    });

    const dateStr = new Date().toISOString().slice(0,10);
    downloadCSV(rows.join("\n"), `aura_projection_balances_${dateStr}.csv`);
}

export function exportTransactionReportToCSV(projectionData, scenarioData) {
    const rows = [];
    const header = ['Date', 'Account Name', 'Income', 'Income Tax & NI', 'Capital Gains Tax', 'Employer Contrib', 'Costs', 'Transfers In', 'Transfers Out', 'Mortgage Pay (Out)', 'Mortgage Principal (In)', 'Interest', 'Events', 'Ending Balance'];
    rows.push(header.join(','));

    projectionData.data_points.forEach(dp => {
        if (!dp.flows || Object.keys(dp.flows).length === 0) return;

        Object.keys(dp.flows).forEach(accId => {
            const f = dp.flows[accId];
            const totalFlow = Math.abs(f.income) + Math.abs(f.costs) + Math.abs(f.transfers_in) + Math.abs(f.transfers_out) + Math.abs(f.mortgage_payments_out) + Math.abs(f.mortgage_repayments_in) + Math.abs(f.interest) + Math.abs(f.events) + Math.abs(f.tax) + Math.abs(f.cgt || 0) + Math.abs(f.employer_contribution || 0);
            
            if (totalFlow > 0.01) { 
                const acc = scenarioData.accounts.find(a => a.id == accId);
                const name = acc ? acc.name : `Account ${accId}`;
                const endBal = dp.account_balances[accId];
                
                const row = [
                    dp.date,
                    `"${name}"`,
                    f.income.toFixed(2),
                    (f.tax || 0).toFixed(2),
                    (f.cgt || 0).toFixed(2),
                    (f.employer_contribution || 0).toFixed(2),
                    f.costs.toFixed(2),
                    f.transfers_in.toFixed(2),
                    f.transfers_out.toFixed(2),
                    f.mortgage_payments_out.toFixed(2),
                    f.mortgage_repayments_in.toFixed(2),
                    f.interest.toFixed(2),
                    f.events.toFixed(2),
                    endBal.toFixed(2)
                ];
                rows.push(row.join(','));
            }
        });
    });

    const dateStr = new Date().toISOString().slice(0,10);
    downloadCSV(rows.join("\n"), `aura_transaction_report_${dateStr}.csv`);
}
