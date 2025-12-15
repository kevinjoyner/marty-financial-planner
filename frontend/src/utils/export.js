import { formatCurrency } from './format'

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

export function exportBalancesToCSV(simulationData, scenario) {
    if (!simulationData || !scenario) return;

    const rows = [];
    // Header: Date, Account Names..., Total
    const accountIds = scenario.accounts.map(a => a.id);
    const header = ['Date', ...scenario.accounts.map(a => `"${a.name}"`), 'Total Net Worth'];
    rows.push(header.join(','));

    simulationData.data_points.forEach(dp => {
        let row = [dp.date];
        let total = 0;
        
        accountIds.forEach(id => {
            const val = dp.account_balances[id] || 0;
            row.push(val.toFixed(2));
            total += val;
        });
        
        // Use the simulation total (which might differ slightly due to rounding or unincluded assets)
        // or recalculate. Let's use the row sum for consistency in the CSV.
        row.push(total.toFixed(2));
        rows.push(row.join(','));
    });

    const dateStr = new Date().toISOString().slice(0,10);
    downloadCSV(rows.join("\n"), `aura_balances_${dateStr}.csv`);
}

export function exportFlowsToCSV(simulationData, scenario) {
    if (!simulationData || !scenario) return;

    const rows = [];
    const header = [
        'Date', 
        'Account Name', 
        'Income', 
        'Income Tax & NI', 
        'Capital Gains Tax', 
        'Employer Contrib', 
        'Costs', 
        'Transfers In', 
        'Transfers Out', 
        'Mortgage Pay (Out)', 
        'Mortgage Principal (In)', 
        'Interest', 
        'Events', 
        'Ending Balance'
    ];
    rows.push(header.join(','));

    simulationData.data_points.forEach(dp => {
        if (!dp.flows || Object.keys(dp.flows).length === 0) return;

        Object.keys(dp.flows).forEach(accIdStr => {
            const accId = parseInt(accIdStr);
            const f = dp.flows[accIdStr];
            
            // Calculate total activity to filter out dormant rows
            const totalActivity = Math.abs(f.income) + Math.abs(f.costs) + 
                                  Math.abs(f.transfers_in) + Math.abs(f.transfers_out) + 
                                  Math.abs(f.mortgage_payments_out) + Math.abs(f.mortgage_repayments_in) + 
                                  Math.abs(f.interest) + Math.abs(f.events) + 
                                  Math.abs(f.tax) + Math.abs(f.cgt || 0) + 
                                  Math.abs(f.employer_contribution || 0);
            
            if (totalActivity > 0.01) { 
                const acc = scenario.accounts.find(a => a.id === accId);
                const name = acc ? acc.name : `Account ${accId}`;
                const endBal = dp.account_balances[accIdStr] || 0;
                
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
