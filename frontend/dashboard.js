// ═══════════════════════════════════════════════════
// dashboard.js v2 — ดึงข้อมูลจาก /stats และ /logs
// ไม่ต้องแก้ไฟล์นี้ แก้ที่ config.js แทน
// ═══════════════════════════════════════════════════

// ── STATE ────────────────────────────────────────
let donutChart = null;
let lineChart  = null;
let stageChart = null;
let trendData  = [];

// ── CLOCK ────────────────────────────────────────
function updateClock() {
  document.getElementById("clock").textContent =
    new Date().toLocaleTimeString("th-TH", { hour12: false });
}
setInterval(updateClock, 1000);
updateClock();

// ── API STATUS ───────────────────────────────────
function setAPIStatus(ok) {
  const el = document.getElementById("api-status");
  if (ok) {
    el.textContent = "● API Connected";
    el.className   = "api-ok";
  } else {
    el.textContent = "● API Disconnected";
    el.className   = "api-fail";
  }
}

// ── FETCH STATS ──────────────────────────────────
async function fetchStats() {
  try {
    const res  = await fetch(CONFIG.API_BASE + CONFIG.API_STATS);
    if (!res.ok) throw new Error();
    const data = await res.json();
    setAPIStatus(true);
    updateKPI(data);
    updateTreemap(data.treemap || []);
    updateDonut(data.techniques || [], data.threats || 0);
    updateTrend(data.trend || []);
    updateMiniBars(data.techniques || [], data.threats || 0);
    updateStageChart(data);
  } catch {
    setAPIStatus(false);
  }
}

// ── FETCH LOGS ───────────────────────────────────
async function fetchLogs() {
  try {
    const res  = await fetch(
      CONFIG.API_BASE + CONFIG.API_LOGS + "?limit=" + CONFIG.LOGS_LIMIT
    );
    if (!res.ok) throw new Error();
    const data = await res.json();
    updateTable(data);
    document.getElementById("rec-count").textContent =
      data.length > 0 ? data[0].id || "—" : 0;
  } catch {}
}

// ── KPI ──────────────────────────────────────────
function updateKPI(s) {
  // Total threats
  document.getElementById("kpi-total").textContent = s.threats || 0;

  // Attack rate (threats per hour ประมาณจาก total)
  const rate = s.total > 0
    ? ((s.threats / s.total) * 100).toFixed(1)
    : "0.0";
  document.getElementById("kpi-rate").textContent = rate;

  // Top technique
  document.getElementById("kpi-top-tec").textContent =
    (s.top_technique || "—").toUpperCase();
  document.getElementById("kpi-top-pct").textContent =
    (s.top_pct || 0) + "% of total attacks";

  // Unique templates
  document.getElementById("kpi-templates").textContent =
    s.unique_templates || 0;

  // Anomaly vs Supervised %
  document.getElementById("pct-recon").textContent  = (s.anomaly_pct    || 0) + "%";
  document.getElementById("pct-exec").textContent   = (s.supervised_pct || 0) + "%";
  document.getElementById("bar-recon").style.width  = (s.anomaly_pct    || 0) + "%";
  document.getElementById("bar-exec").style.width   = (s.supervised_pct || 0) + "%";

  // Delta simulate
  const delta = Math.floor(Math.random() * 20 + 5);
  document.getElementById("kpi-delta").textContent = `↑ +${delta}%`;

  // rec-count
  document.getElementById("rec-count").textContent = s.total || 0;
}

// ── TREEMAP ──────────────────────────────────────
function updateTreemap(treemap) {
  if (!treemap.length) return;
  document.getElementById("treemap").innerHTML = treemap
    .slice(0, 8)
    .map((c, i) => `
      <div class="tm-cell"
           style="background:${CONFIG.TREEMAP_COLORS[i % CONFIG.TREEMAP_COLORS.length]}">
        <div class="tm-val">${c.count}</div>
        <div class="tm-title">${c.template}</div>
        <div class="tm-sub">${c.technique}</div>
      </div>`)
    .join("");
}

// ── TABLE ────────────────────────────────────────
function updateTable(rows) {
  if (!rows.length) return;
  document.getElementById("logBody").innerHTML = rows
    .map(p => `
      <tr>
        <td><span class="payload">${String(p.user_inputs).substring(0, 22)}...</span></td>
        <td style="color:#94a3b8;font-size:10px;">${p.query_template_id}</td>
        <td><span class="tag tag-${p.attack_technique}">${p.attack_technique}</span></td>
        <td style="color:var(--text);font-size:11px;">${Math.round((p.attack_prob || 0) * 100)}%</td>
        <td><span class="threat-badge ${p.is_threat ? 'threat-yes' : 'threat-no'}">
          ${p.is_threat ? "THREAT" : "SAFE"}
        </span></td>
      </tr>`)
    .join("");
}

// ── MINI BARS ────────────────────────────────────
function updateMiniBars(techniques, total) {
  if (!techniques.length) return;
  const max = techniques[0]?.count || 1;
  document.getElementById("miniBars").innerHTML = techniques
    .map(t => `
      <div class="mini-bar-row">
        <div class="mini-bar-label">${t.technique}</div>
        <div class="mini-bar-track">
          <div class="mini-bar-fill"
            style="width:${Math.round(t.count / max * 100)}%;
                   background:${CONFIG.TECHNIQUE_COLORS[t.technique] || '#6366f1'}">
          </div>
        </div>
        <div class="mini-bar-count">${t.count}</div>
      </div>`)
    .join("");
}

// ── DONUT ────────────────────────────────────────
function updateDonut(techniques, total) {
  if (!techniques.length) return;
  const labels = techniques.map(t => t.technique);
  const vals   = techniques.map(t => t.count);

  document.getElementById("donut-center").textContent = labels.length;
  document.getElementById("donut-legend").innerHTML   = labels
    .map((l, i) => `
      <div class="legend-item">
        <div class="legend-dot"
             style="background:${CONFIG.DONUT_COLORS[i % CONFIG.DONUT_COLORS.length]}">
        </div>
        <span>${l}</span>
        <span class="legend-pct">${Math.round(vals[i] / Math.max(total,1) * 100)}%</span>
      </div>`)
    .join("");

  if (donutChart) donutChart.destroy();
  donutChart = new Chart(document.getElementById("donutChart"), {
    type: "doughnut",
    data: {
      labels,
      datasets: [{
        data:            vals,
        backgroundColor: CONFIG.DONUT_COLORS.slice(0, labels.length),
        borderWidth:     2,
        borderColor:     "#111118",
        hoverOffset:     4,
      }],
    },
    options: {
      cutout:  "70%",
      plugins: { legend: { display: false } },
      animation: { duration: 400 },
    },
  });
}

// ── LINE CHART (Trend) ───────────────────────────
function updateTrend(trend) {
  // ถ้า API ส่ง trend มา ใช้เลย ถ้าไม่มีใช้ timestamp ปัจจุบัน
  if (trend.length > 0) {
    trendData = trend.slice(-CONFIG.TREND_MAX_POINTS);
  } else {
    const now   = new Date();
    const label = now.toLocaleTimeString("th-TH", {
      hour: "2-digit", minute: "2-digit", hour12: false,
    });
    trendData.push({ time: label, count: 0 });
    if (trendData.length > CONFIG.TREND_MAX_POINTS) trendData.shift();
  }

  if (lineChart) lineChart.destroy();
  lineChart = new Chart(document.getElementById("lineChart"), {
    type: "line",
    data: {
      labels:   trendData.map(d => d.time),
      datasets: [{
        data:                 trendData.map(d => d.count),
        borderColor:          "#10b981",
        backgroundColor:      "rgba(16,185,129,.08)",
        borderWidth:          2,
        pointRadius:          3,
        pointBackgroundColor: "#10b981",
        tension:              0.4,
        fill:                 true,
      }],
    },
    options: {
      plugins: { legend: { display: false } },
      scales: {
        x: {
          grid:   { color: "rgba(30,30,46,.6)" },
          ticks:  { color: "#64748b", font: { size: 9 } },
          border: { color: "transparent" },
        },
        y: {
          grid:   { color: "rgba(30,30,46,.6)" },
          ticks:  { color: "#64748b", font: { size: 9 } },
          border: { color: "transparent" },
        },
      },
      animation: { duration: 300 },
    },
  });
}

// ── POLAR CHART ──────────────────────────────────
function updateStageChart(s) {
  const anomaly    = s.anomaly_count    || 1;
  const supervised = s.supervised_count || 1;
  const highConf   = s.high_conf_count  || 1;

  if (stageChart) stageChart.destroy();
  stageChart = new Chart(document.getElementById("stageChart"), {
    type: "polarArea",
    data: {
      labels:   ["Anomaly", "Supervised", "High Conf"],
      datasets: [{
        data:            [anomaly, supervised, highConf],
        backgroundColor: CONFIG.POLAR_COLORS,
        borderColor:     CONFIG.POLAR_BORDERS,
        borderWidth:     2,
      }],
    },
    options: {
      plugins: {
        legend: {
          labels:   { color: "#94a3b8", font: { size: 9 } },
          position: "bottom",
        },
      },
      scales: {
        r: {
          grid:  { color: "rgba(30,30,46,.7)" },
          ticks: { display: false },
        },
      },
      animation: { duration: 300 },
    },
  });
}

// ── START ────────────────────────────────────────
fetchStats();
fetchLogs();
setInterval(fetchStats, CONFIG.STATS_INTERVAL);
setInterval(fetchLogs,  CONFIG.LOGS_INTERVAL);