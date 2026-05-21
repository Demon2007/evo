/* ====================================================
   EduNova — Charts (Canvas-based, no dependencies)
   ==================================================== */

const CHART_COLORS = {
  purple:  '#8b5cf6',
  blue:    '#3b82f6',
  green:   '#10b981',
  yellow:  '#f59e0b',
  red:     '#ef4444',
  pink:    '#ec4899',
  cyan:    '#06b6d4',
  orange:  '#f97316',
};

const GRADE_COLORS = {
  '5': '#10b981',
  '4': '#3b82f6',
  '3': '#f59e0b',
  '2': '#ef4444',
  '1': '#dc2626',
};

// ── Bar Chart ────────────────────────────────────────
function drawBarChart(canvasId, labels, values, options = {}) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  const W = canvas.width  = canvas.offsetWidth;
  const H = canvas.height = canvas.offsetHeight || 220;

  const padding = { top: 20, right: 20, bottom: 40, left: 40 };
  const chartW = W - padding.left - padding.right;
  const chartH = H - padding.top - padding.bottom;

  ctx.clearRect(0, 0, W, H);

  const max = Math.max(...values, 1);
  const barW = chartW / labels.length * 0.6;
  const gap   = chartW / labels.length;
  const colors = options.colors || Object.values(CHART_COLORS);

  // Grid lines
  ctx.strokeStyle = 'rgba(15,23,42,0.08)';
  ctx.lineWidth = 1;
  for (let i = 0; i <= 4; i++) {
    const y = padding.top + (chartH / 4) * i;
    ctx.beginPath();
    ctx.moveTo(padding.left, y);
    ctx.lineTo(padding.left + chartW, y);
    ctx.stroke();

    ctx.fillStyle = '#94a3b8';
    ctx.font = '11px Inter, sans-serif';
    ctx.textAlign = 'right';
    ctx.fillText(Math.round(max - (max / 4) * i), padding.left - 6, y + 4);
  }

  // Bars
  labels.forEach((label, i) => {
    const x = padding.left + i * gap + (gap - barW) / 2;
    const barH = (values[i] / max) * chartH;
    const y = padding.top + chartH - barH;
    const color = Array.isArray(options.colors) ? options.colors[i % options.colors.length] : colors[i % colors.length];

    const grad = ctx.createLinearGradient(0, y, 0, y + barH);
    grad.addColorStop(0, color);
    grad.addColorStop(1, color + '44');

    ctx.fillStyle = grad;
    ctx.beginPath();
    ctx.roundRect ? ctx.roundRect(x, y, barW, barH, [4, 4, 0, 0]) : ctx.rect(x, y, barW, barH);
    ctx.fill();

    // Value
    if (values[i] > 0) {
      ctx.fillStyle = '#1e293b';
      ctx.font = 'bold 11px Inter, sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText(values[i], x + barW / 2, y - 6);
    }

    // Label
    ctx.fillStyle = '#64748b';
    ctx.font = '11px Inter, sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText(label, x + barW / 2, padding.top + chartH + 18);
  });
}

// ── Donut Chart ──────────────────────────────────────
function drawDonutChart(canvasId, labels, values, colors) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  const W = canvas.width  = canvas.offsetWidth;
  const H = canvas.height = canvas.offsetHeight || 220;

  ctx.clearRect(0, 0, W, H);

  const cx = W * 0.38;
  const cy = H / 2;
  const radius = Math.min(cx, cy) * 0.75;
  const innerR = radius * 0.6;

  const total = values.reduce((a, b) => a + b, 0);
  if (total === 0) return;

  let angle = -Math.PI / 2;

  values.forEach((val, i) => {
    const slice = (val / total) * Math.PI * 2;
    ctx.beginPath();
    ctx.moveTo(cx, cy);
    ctx.arc(cx, cy, radius, angle, angle + slice);
    ctx.closePath();
    ctx.fillStyle = colors[i % colors.length];
    ctx.fill();
    angle += slice;
  });

  // Inner circle (hole)
  ctx.beginPath();
  ctx.arc(cx, cy, innerR, 0, Math.PI * 2);
  ctx.fillStyle = '#ffffff';
  ctx.fill();

  // Center label
  ctx.fillStyle = '#0f172a';
  ctx.font = 'bold 20px Inter, sans-serif';
  ctx.textAlign = 'center';
  ctx.fillText(total, cx, cy + 7);
  ctx.fillStyle = 'rgba(160,156,184,0.7)';
  ctx.font = '11px Inter, sans-serif';
  ctx.fillText('всего', cx, cy + 22);

  // Legend
  const legendX = W * 0.68;
  let legendY = cy - (labels.length * 22) / 2 + 8;

  labels.forEach((label, i) => {
    if (values[i] === 0) return;
    ctx.fillStyle = colors[i % colors.length];
    ctx.beginPath();
    ctx.roundRect ? ctx.roundRect(legendX, legendY - 7, 10, 10, 2) : ctx.rect(legendX, legendY - 7, 10, 10);
    ctx.fill();

    ctx.fillStyle = '#334155';
    ctx.font = '12px Inter, sans-serif';
    ctx.textAlign = 'left';
    ctx.fillText(`${label} (${values[i]})`, legendX + 16, legendY + 3);

    legendY += 22;
  });
}

// ── Line Chart ───────────────────────────────────────
function drawLineChart(canvasId, labels, datasets, options = {}) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  const W = canvas.width  = canvas.offsetWidth;
  const H = canvas.height = canvas.offsetHeight || 220;

  const padding = { top: 24, right: 20, bottom: 40, left: 44 };
  const chartW = W - padding.left - padding.right;
  const chartH = H - padding.top - padding.bottom;

  ctx.clearRect(0, 0, W, H);

  const allValues = datasets.flatMap(d => d.values);
  const max = Math.max(...allValues, 1);
  const min = Math.min(...allValues, 0);
  const range = max - min || 1;

  // Grid
  ctx.strokeStyle = 'rgba(15,23,42,0.08)';
  ctx.lineWidth = 1;
  for (let i = 0; i <= 4; i++) {
    const y = padding.top + (chartH / 4) * i;
    ctx.beginPath(); ctx.moveTo(padding.left, y); ctx.lineTo(padding.left + chartW, y); ctx.stroke();
    ctx.fillStyle = '#94a3b8';
    ctx.font = '10px Inter, sans-serif';
    ctx.textAlign = 'right';
    const val = max - (range / 4) * i;
    ctx.fillText(Number.isInteger(val) ? val : val.toFixed(1), padding.left - 6, y + 4);
  }

  // X labels
  const stepX = chartW / (labels.length - 1 || 1);
  ctx.fillStyle = '#64748b';
  ctx.font = '10px Inter, sans-serif';
  ctx.textAlign = 'center';
  labels.forEach((label, i) => {
    ctx.fillText(label, padding.left + i * stepX, padding.top + chartH + 18);
  });

  // Datasets
  datasets.forEach(ds => {
    const points = ds.values.map((v, i) => ({
      x: padding.left + i * stepX,
      y: padding.top + chartH - ((v - min) / range) * chartH,
    }));

    // Area fill
    const grad = ctx.createLinearGradient(0, padding.top, 0, padding.top + chartH);
    grad.addColorStop(0, ds.color + '33');
    grad.addColorStop(1, ds.color + '00');
    ctx.beginPath();
    ctx.moveTo(points[0].x, padding.top + chartH);
    points.forEach(p => ctx.lineTo(p.x, p.y));
    ctx.lineTo(points[points.length - 1].x, padding.top + chartH);
    ctx.closePath();
    ctx.fillStyle = grad;
    ctx.fill();

    // Line
    ctx.beginPath();
    ctx.strokeStyle = ds.color;
    ctx.lineWidth = 2;
    ctx.lineJoin = 'round';
    points.forEach((p, i) => i === 0 ? ctx.moveTo(p.x, p.y) : ctx.lineTo(p.x, p.y));
    ctx.stroke();

    // Dots
    points.forEach(p => {
      ctx.beginPath();
      ctx.arc(p.x, p.y, 4, 0, Math.PI * 2);
      ctx.fillStyle = ds.color;
      ctx.fill();
      ctx.strokeStyle = '#0f0f1e';
      ctx.lineWidth = 2;
      ctx.stroke();
    });
  });
}

// ── Init charts from data attributes ─────────────────
document.addEventListener('DOMContentLoaded', () => {
  initAllCharts();

  // Responsive redraw on resize (no page reload)
  let resizeTimer;
  window.addEventListener('resize', () => {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(initAllCharts, 250);
  }, { passive: true });
});

function initAllCharts() {
  const gradeEl = document.getElementById('grade-dist-data');
  if (gradeEl) {
    try {
      const data = JSON.parse(gradeEl.textContent);
      const labels = ['1','2','3','4','5'];
      drawBarChart('grade-dist-chart', labels, labels.map(l=>data[l]||0), {colors:labels.map(l=>GRADE_COLORS[l])});
    } catch(e) {}
  }
  const attEl = document.getElementById('att-stats-data');
  if (attEl) {
    try {
      const data = JSON.parse(attEl.textContent);
      drawDonutChart('att-chart',
        ['Присутствовал','Не был','Заболел','Отпросился','Опоздал'],
        ['present','absent','sick','excused','late'].map(k=>data[k]||0),
        ['#10b981','#ef4444','#f59e0b','#3b82f6','#8b5cf6']
      );
    } catch(e) {}
  }
  const groupsEl = document.getElementById('groups-data');
  if (groupsEl) {
    try {
      const data = JSON.parse(groupsEl.textContent);
      drawBarChart('groups-chart', data.map(g=>g.name), data.map(g=>g.cnt), {colors:['#3b82f6']});
    } catch(e) {}
  }
  const groupsAvgEl = document.getElementById('groups-avg-data');
  if (groupsAvgEl) {
    try {
      const data = JSON.parse(groupsAvgEl.textContent);
      drawBarChart('groups-avg-chart', data.map(g=>g.name), data.map(g=>+parseFloat(g.avg).toFixed(1)), {colors:['#10b981']});
    } catch(e) {}
  }
  const subjEl = document.getElementById('subject-grades-data');
  if (subjEl) {
    try {
      const data = JSON.parse(subjEl.textContent);
      const labels = Object.keys(data);
      if (labels.length) drawBarChart('subject-grades-chart', labels, Object.values(data).map(Number), {colors:['#3b82f6']});
    } catch(e) {}
  }
}
