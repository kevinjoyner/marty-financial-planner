<script setup>
import { computed, watch, ref } from 'vue'
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, Filler } from 'chart.js'
import { Line } from 'vue-chartjs'
import annotationPlugin from 'chartjs-plugin-annotation'
import { useSimulationStore } from '../stores/simulation'
import { formatCurrency } from '../utils/format'
import { getAccountColor, getCategoryColor } from '../utils/colors'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, Filler, annotationPlugin)

const props = defineProps({ 
    data: Object, 
    visibleAccountIds: { type: Array, default: () => [] }, 
    freezeAxis: { type: Boolean, default: false },
    aggregationMode: { type: String, default: 'account' } 
})

const store = useSimulationStore(); 
const yMin = ref(null); 
const yMax = ref(null);

// --- 1. Custom Gantt Label Plugin ---
const ganttLabelPlugin = {
    id: 'ganttLabels',
    afterDatasetsDraw: (chart) => {
        const { ctx, scales, chartArea } = chart;
        const annotations = chart.config.options.plugins.ganttData || [];
        
        if (annotations.length === 0) return;

        const lanes = []; 
        const ROW_HEIGHT = 26;
        const BASE_Y = scales.y.bottom + 50; 
        const PADDING_X = 8;
        const MARGIN = 4;

        const sortedAnns = [...annotations].sort((a,b) => new Date(a.date) - new Date(b.date));
        const drawItems = [];

        sortedAnns.forEach(ann => {
            const xPos = scales.x.getPixelForValue(ann.date);
            if (xPos === undefined || isNaN(xPos) || xPos < chartArea.left || xPos > chartArea.right) return;

            ctx.font = "bold 10px Inter, sans-serif"; 
            const textWidth = ctx.measureText(ann.label).width;
            const boxWidth = textWidth + (PADDING_X * 2);
            
            let laneIndex = 0;
            while (true) {
                if (!lanes[laneIndex] || xPos > (lanes[laneIndex] + MARGIN)) {
                    lanes[laneIndex] = xPos + boxWidth; 
                    break;
                }
                laneIndex++;
            }
            lanes[laneIndex] = xPos + boxWidth; 

            const yPos = BASE_Y + (laneIndex * ROW_HEIGHT);
            
            let bgColor, borderColor, textColor, lineDash;
            if (ann.isBaseline) {
                bgColor = '#f1f5f9'; borderColor = '#94a3b8'; textColor = '#64748b'; lineDash = [3, 3];
            } else {
                if (ann.type === 'milestone') bgColor = '#16a34a';
                else if (ann.type === 'transaction') bgColor = '#635bff';
                else if (ann.type === 'insolvency') bgColor = '#dc2626';
                else bgColor = '#94a3b8';
                borderColor = bgColor; textColor = '#ffffff'; lineDash = [];
            }

            drawItems.push({ x: xPos, y: yPos, w: boxWidth, h: ROW_HEIGHT - 4, bgColor, borderColor, textColor, lineDash, label: ann.label, isBaseline: ann.isBaseline });
        });

        ctx.save();
        ctx.lineWidth = 1;
        drawItems.forEach(item => {
            ctx.beginPath();
            ctx.setLineDash([2, 2]);
            ctx.strokeStyle = item.borderColor;
            ctx.globalAlpha = item.isBaseline ? 0.5 : 1.0; 
            ctx.moveTo(item.x, item.y);
            ctx.lineTo(item.x, chartArea.top);
            ctx.stroke();
        });
        ctx.setLineDash([]); 
        ctx.globalAlpha = 1.0;

        ctx.font = "bold 10px Inter, sans-serif";
        ctx.textAlign = "left";
        ctx.textBaseline = "middle";

        drawItems.forEach(item => {
            let boxX = item.x;
            if ((boxX + item.w) > chartArea.right) boxX = item.x - item.w;

            ctx.fillStyle = item.bgColor;
            if (item.isBaseline) {
                ctx.beginPath(); ctx.lineWidth = 1; ctx.setLineDash([2, 2]); ctx.strokeStyle = item.borderColor;
                ctx.roundRect(boxX, item.y, item.w, item.h, 4); ctx.stroke(); ctx.fill(); 
            } else {
                ctx.beginPath(); ctx.roundRect(boxX, item.y, item.w, item.h, 4); ctx.fill();
            }
            ctx.fillStyle = item.textColor;
            ctx.fillText(item.label, boxX + PADDING_X, item.y + (item.h)/2);
        });
        ctx.restore();
    }
};

const plugins = [ganttLabelPlugin];

// --- 2. Data Processing ---
const chartData = computed(() => {
  // CRITICAL FIX: Return empty structure if data is missing
  if (!props.data || !props.data.data_points || props.data.data_points.length === 0) {
      return { labels: [], datasets: [] }
  }
  const simPoints = props.data.data_points; 
  const basePoints = store.baselineData ? store.baselineData.data_points : null;
  const labels = simPoints.map(p => p.date); 
  const datasets = [];
  const showGhost = store.activeOverrideCount > 0 && basePoints && basePoints.length > 0;

  if (props.aggregationMode === 'total') {
      datasets.push({ label: 'Net Worth', data: simPoints.map(p => p.balance), borderColor: '#0f172a', borderWidth: 3, tension: 0.2, pointRadius: 0 });
      if (showGhost) datasets.push({ label: 'Net Worth (Base)', data: basePoints.map(p => p.balance), borderColor: '#94a3b8', borderWidth: 2, borderDash: [5, 5], tension: 0.2, pointRadius: 0 });
  } else if (props.aggregationMode === 'category') {
      const categories = ['liquid', 'illiquid', 'liabilities', 'unvested'];
      const catMap = store.accountsByCategory; 
      categories.forEach(cat => {
          const accs = catMap[cat];
          if (!accs || accs.length === 0) return;
          const validIds = accs.map(a => a.id).filter(id => props.visibleAccountIds.includes(id));
          if (validIds.length === 0) return;
          const color = getCategoryColor(cat);
          const label = cat.charAt(0).toUpperCase() + cat.slice(1);
          datasets.push({ label: label, data: simPoints.map(p => validIds.reduce((sum, id) => sum + (p.account_balances[id] || 0), 0)), borderColor: color, borderWidth: 2, tension: 0.2, pointRadius: 0 });
          if (showGhost) datasets.push({ label: `${label} (Base)`, data: basePoints.map(p => validIds.reduce((sum, id) => sum + (p.account_balances[id] || 0), 0)), borderColor: color, borderWidth: 1, borderDash: [4, 4], tension: 0.2, pointRadius: 0, opacity: 0.6 });
      });
  } else {
      props.visibleAccountIds.forEach(accId => {
          const acc = store.scenario?.accounts.find(a => a.id === accId); 
          const name = acc ? acc.name : `Acc ${accId}`; 
          const color = getAccountColor(accId);
          datasets.push({ label: name, data: simPoints.map(p => (p.account_balances[accId] || 0)), borderColor: color, borderWidth: 2, pointRadius: 0, tension: 0.2 });
          if (showGhost) datasets.push({ label: `${name} (Base)`, data: basePoints.map(p => (p.account_balances[accId] || 0)), borderColor: color, borderWidth: 1, borderDash: [4, 4], pointRadius: 0, tension: 0.2 });
      });
  }
  return { labels, datasets }
})

const preparedData = computed(() => {
    // CRITICAL FIX: Return default state if data is missing
    if (!props.data || !props.data.data_points || props.data.data_points.length === 0) {
        return { annotations: [], laneCount: 0 };
    }
    const availableDates = props.data.data_points.map(p => p.date);
    const annotations = [];
    const processList = (list, isBaseline) => {
        if (!list) return;
        list.forEach(a => {
            const annDate = new Date(a.date);
            const matchedLabel = availableDates.find(dStr => {
                const d = new Date(dStr);
                return d.getFullYear() === annDate.getFullYear() && d.getMonth() === annDate.getMonth();
            });
            if (matchedLabel) annotations.push({ ...a, date: matchedLabel, isBaseline });
        });
    };
    processList(props.data.annotations, false);
    if (store.activeOverrideCount > 0 && store.baselineData && store.baselineData.annotations) {
        processList(store.baselineData.annotations, true);
    }
    const sorted = [...annotations].sort((a,b) => new Date(a.date) - new Date(b.date));
    const lanes = [];
    const startDate = new Date(availableDates[0]).getTime();
    const endDate = new Date(availableDates[availableDates.length - 1]).getTime();
    const totalDuration = endDate - startDate;
    const LABEL_BUFFER_MS = totalDuration * 0.12; 
    sorted.forEach(ann => {
        const annTime = new Date(ann.date).getTime();
        let laneIndex = 0;
        while (true) {
             if (!lanes[laneIndex] || annTime > (lanes[laneIndex] + LABEL_BUFFER_MS)) {
                 lanes[laneIndex] = annTime; break;
             }
             laneIndex++;
        }
    });
    return { annotations: sorted, laneCount: Math.max(0, lanes.length) };
});

const containerHeight = computed(() => {
    const laneCount = preparedData.value.laneCount || 0;
    return 350 + 20 + (50 + (laneCount * 28) + 10);
})

const chartOptions = computed(() => {
    const laneCount = preparedData.value.laneCount || 0;
    const bottomPadding = 50 + (laneCount * 28) + 10; 
    return { 
        responsive: true, 
        maintainAspectRatio: false, 
        interaction: { mode: 'index', intersect: false }, 
        clip: false, 
        layout: { padding: { bottom: bottomPadding, top: 20 } },
        plugins: { legend: { display: false }, annotation: { annotations: {} }, ganttData: preparedData.value.annotations, tooltip: { itemSort: (a, b) => b.raw - a.raw } }, 
        scales: { 
            y: { min: yMin.value, max: yMax.value, grid: { color: '#f1f5f9' }, ticks: { callback: (val) => '£' + (val/1000).toFixed(0) + 'k' } }, 
            x: { grid: { display: false }, ticks: { maxTicksLimit: 8, maxRotation: 0 } } 
        } 
    }
})

watch(() => props.freezeAxis, (isFrozen) => { 
    if (isFrozen) {
        if (!chartData.value.datasets || chartData.value.datasets.length === 0) return;
        let globalMax = -Infinity; let globalMin = Infinity;
        chartData.value.datasets.forEach(ds => {
            if (!ds.data) return;
            const dsMax = Math.max(...ds.data); const dsMin = Math.min(...ds.data);
            if (dsMax > globalMax) globalMax = dsMax; if (dsMin < globalMin) globalMin = dsMin;
        });
        const range = globalMax - globalMin; const padding = range * 0.1 || 1000;
        yMax.value = globalMax + padding; yMin.value = globalMin - padding;
    } else { yMin.value = null; yMax.value = null; }
});
</script>

<template>
    <div class="relative w-full transition-[height] duration-300 ease-in-out" :style="{ height: containerHeight + 'px' }">
        <Line v-if="chartData.datasets.length > 0" :data="chartData" :options="chartOptions" :plugins="plugins" />
        <div v-else class="absolute inset-0 flex items-center justify-center text-slate-400 text-sm">
            Select accounts to view projection.
        </div>
    </div>
</template>
