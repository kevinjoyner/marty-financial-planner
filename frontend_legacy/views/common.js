export function renderBreadcrumbs(container, crumbs) {
    if (!container) return;
    container.innerHTML = '';
    crumbs.forEach((crumb, index) => {
        if (index > 0) {
            const sep = document.createElement('span');
            sep.className = 'separator';
            sep.innerHTML = '›';
            container.appendChild(sep);
        }
        const span = document.createElement('span');
        if (index === crumbs.length - 1) {
            span.className = 'current';
            span.textContent = crumb.label;
            container.appendChild(span);
        } else {
            const a = document.createElement('a');
            a.href = crumb.path;
            a.textContent = crumb.label;
            container.appendChild(a);
        }
    });
}

export function renderTable(headers, rows, tableId = null) {
    const idAttr = tableId ? `id="${tableId}"` : '';
    const sortClass = tableId ? 'sortable' : ''; 
    const ths = headers.map(h => `<th>${h}</th>`).join('');
    const trs = rows.map(r => `<tr>${r.map(c => `<td>${c}</td>`).join('')}</tr>`).join('');
    return `<table class="data-table ${sortClass}" ${idAttr} data-table-id="${tableId || ''}"><thead><tr>${ths}</tr></thead><tbody>${trs}</tbody></table>`;
}

function parseCellValue(cellText) {
    const clean = cellText.replace(/[£$,%\s]/g, '');
    if (clean !== '' && !isNaN(Number(clean))) return Number(clean);
    if (cellText.match(/^\d{1,2}\/\d{1,2}\/\d{4}$/)) {
        const [d, m, y] = cellText.split('/').map(Number);
        return new Date(y, m - 1, d).getTime();
    }
    const dateAttempt = Date.parse(cellText);
    if (!isNaN(dateAttempt) && (cellText.includes('-') || cellText.includes('/'))) return dateAttempt;
    return cellText.toLowerCase();
}

export function initSortableTables(container) {
    const tables = container.querySelectorAll('table.sortable');
    tables.forEach(table => {
        const tableId = table.dataset.tableId;
        const headers = table.querySelectorAll('th');
        const tbody = table.querySelector('tbody');

        // Restore sort state
        if (tableId) {
            const savedSort = localStorage.getItem(`marty_table_sort_${tableId}`);
            if (savedSort) {
                const { colIndex, dir } = JSON.parse(savedSort);
                if (headers[colIndex]) {
                    sortTable(table, tbody, headers, colIndex, dir);
                }
            }
        }

        headers.forEach((th, columnIndex) => {
            th.addEventListener('click', () => {
                const currentDir = th.classList.contains('th-sort-asc') ? 'asc' : 'desc';
                const newDir = currentDir === 'asc' ? 'desc' : 'asc';
                
                sortTable(table, tbody, headers, columnIndex, newDir);
                
                if (tableId) {
                    localStorage.setItem(`marty_table_sort_${tableId}`, JSON.stringify({ colIndex: columnIndex, dir: newDir }));
                }
            });
        });
    });
}

function sortTable(table, tbody, headers, columnIndex, dir) {
    const rows = Array.from(tbody.querySelectorAll('tr'));
    const multiplier = dir === 'asc' ? 1 : -1;
    
    headers.forEach(h => h.classList.remove('th-sort-asc', 'th-sort-desc'));
    headers[columnIndex].classList.add(`th-sort-${dir}`);

    rows.sort((rowA, rowB) => {
        const cellA = rowA.children[columnIndex].innerText;
        const cellB = rowB.children[columnIndex].innerText;
        const valA = parseCellValue(cellA);
        const valB = parseCellValue(cellB);
        if (valA < valB) return -1 * multiplier;
        if (valA > valB) return 1 * multiplier;
        return 0;
    });

    rows.forEach(row => tbody.appendChild(row));
}
