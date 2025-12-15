// Shared state for the frontend

// Chart/Projection settings (years, mode, etc.)
export let globalState = {
    years: 10,
    mode: 'aggregate',
    selectedAccounts: [],
    freezeAxis: false,
    axisMax: null
};

// The currently loaded scenario data (Owners, Accounts, etc.)
export let currentScenarioData = null;

// The results of the last projection run (for CSV export)
export let lastProjectionData = null;

// --- Setters ---

export function setGlobalState(newState) {
    // Update properties of the existing object so imports elsewhere see changes
    Object.assign(globalState, newState);
}

export function setScenarioData(data) {
    currentScenarioData = data;
}

export function setLastProjectionData(data) {
    lastProjectionData = data;
}