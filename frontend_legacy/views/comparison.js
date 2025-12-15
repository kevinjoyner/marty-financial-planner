// frontend/views/comparison.js
import { formatCurrency } from '../utils.js';

export function renderComparisonDashboard(container, scenarios) {
    const optionsHtml = scenarios.map(s => `<option value="${s.id}">${s.name}</option>`).join('');

    container.innerHTML = `
        <div class="card">
            <div class="grid grid-3">
                <div class="form-group">
                    <label>Baseline Scenario (A)</label>
                    <select id="scen-a">${optionsHtml}</select>
                </div>
                <div class="form-group">
                    <label>Comparison Scenario (B)</label>
                    <select id="scen-b">${optionsHtml}</select>
                </div>
                <div class="form-group">
                    <label>Duration (Years)</label>
                    <input type="number" id="comp-years" value="20">
                </div>
            </div>
            <button id="run-comp-btn" class="btn btn-primary" style="width:100%">Run Comparison</button>
        </div>

        <div class="card hidden" id="comp-results">
            <h3>Net Worth Comparison</h3>
            <div class="chart-container">
                <canvas id="comp-chart"></canvas>
            </div>
            
            <h3 style="margin-top:30px">Analysis</h3>
            <table class="comp-table">
                <thead>
                    <tr>
                        <th>Metric</th>
                        <th>Baseline (A)</th>
                        <th>Comparison (B)</th>
                        <th>Difference</th>
                    </tr>
                </thead>
                <tbody id="comp-table-body"></tbody>
            </table>
        </div>
    `;
}

export function renderComparisonTable(dataA, dataB) {
    const lastA = dataA.data_points[dataA.data_points.length - 1].balance;
    const lastB = dataB.data_points[dataB.data_points.length - 1].balance;
    const growthA = lastA - dataA.data_points[0].balance;
    const growthB = lastB - dataB.data_points[0].balance;
    const diff = lastB - lastA;
    const diffClass = diff > 0 ? 'delta-pos' : (diff < 0 ? 'delta-neg' : 'delta-neutral');
    const diffSign = diff > 0 ? '+' : '';

    const tbody = document.getElementById('comp-table-body');
    tbody.innerHTML = `
        <tr>
            <td>Final Net Worth</td>
            <td>${formatCurrency(lastA*100)}</td>
            <td>${formatCurrency(lastB*100)}</td>
            <td class="${diffClass}">${diffSign}${formatCurrency(diff*100)}</td>
        </tr>
        <tr>
            <td>Total Growth</td>
            <td>${formatCurrency(growthA*100)}</td>
            <td>${formatCurrency(growthB*100)}</td>
            <td>${formatCurrency((growthB-growthA)*100)}</td>
        </tr>
    `;
}