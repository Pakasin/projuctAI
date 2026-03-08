// ═══════════════════════════════════════════════════
// config.js v2 — ปรับแต่งทุกอย่างได้ที่นี่
// ═══════════════════════════════════════════════════

const CONFIG = {

  // ── API ENDPOINTS ────────────────────────────
  API_BASE:    "http://127.0.0.1:8000",   // Base URL ของ FastAPI server
  API_PREDICT: "/predict",                 // POST — ทำนาย
  API_STATS:   "/stats",                   // GET  — สถิติทั้งหมด
  API_LOGS:    "/logs",                    // GET  — log ล่าสุด
  API_CLEAR:   "/clear",                   // GET  — ล้าง DB

  // ── REFRESH INTERVAL ────────────────────────
  STATS_INTERVAL: 3000,    // ดึง /stats ทุกกี่ ms
  LOGS_INTERVAL:  3000,    // ดึง /logs  ทุกกี่ ms
  LOGS_LIMIT:     8,       // จำนวน log ที่ดึงมาแสดง

  // ── CHART ────────────────────────────────────
  TREND_MAX_POINTS: 12,    // จำนวนจุดใน Line Chart

  // ── COLORS ───────────────────────────────────
  TECHNIQUE_COLORS: {
    boolean: "#6366f1",
    union:   "#06b6d4",
    error:   "#f43f5e",
    time:    "#a855f7",
    stacked: "#f59e0b",
    inline:  "#10b981",
    insider: "#94a3b8",
    none:    "#64748b",
  },

  TREEMAP_COLORS: [
    "rgba(99,102,241,.6)",
    "rgba(6,182,212,.55)",
    "rgba(244,63,94,.5)",
    "rgba(245,158,11,.5)",
    "rgba(16,185,129,.45)",
    "rgba(168,85,247,.5)",
    "rgba(99,102,241,.4)",
    "rgba(6,182,212,.35)",
  ],

  DONUT_COLORS: [
    "#6366f1","#06b6d4","#f59e0b",
    "#10b981","#f43f5e","#a855f7",
  ],

  POLAR_COLORS: [
    "rgba(244,63,94,.5)",
    "rgba(245,158,11,.5)",
    "rgba(99,102,241,.5)",
  ],
  POLAR_BORDERS: ["#f43f5e","#f59e0b","#6366f1"],
};