# ═══════════════════════════════════════════════════
# database.py — SQLite Logger
# บันทึกผลการทำนายทุกครั้งลง SQLite
# ═══════════════════════════════════════════════════

import sqlite3
import os
from datetime import datetime

DB_PATH = "C:/Users/teent/Documents/sqli_logs.db"

# ── สร้าง Database และ Tables ────────────────────
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()

    # ตารางหลัก: บันทึกผลทุก prediction
    cur.execute("""
        CREATE TABLE IF NOT EXISTS predictions (
            id                INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp         TEXT    NOT NULL,
            user_inputs       TEXT,
            query_template_id TEXT,
            is_threat         INTEGER,
            is_anomaly        INTEGER,
            anomaly_score     REAL,
            binary_label      INTEGER,
            attack_prob       REAL,
            attack_technique  TEXT
        )
    """)

    # ตาราง stats: สรุปรายชั่วโมง
    cur.execute("""
        CREATE TABLE IF NOT EXISTS hourly_stats (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            hour          TEXT    NOT NULL,
            total         INTEGER DEFAULT 0,
            threats       INTEGER DEFAULT 0,
            safe          INTEGER DEFAULT 0,
            anomalies     INTEGER DEFAULT 0,
            top_technique TEXT
        )
    """)

    conn.commit()
    conn.close()
    print(f"✅ Database initialized → {DB_PATH}")

# ── บันทึก Prediction ────────────────────────────
def log_prediction(data: dict):
    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()
    cur.execute("""
        INSERT INTO predictions (
            timestamp, user_inputs, query_template_id,
            is_threat, is_anomaly, anomaly_score,
            binary_label, attack_prob, attack_technique
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        data.get("user_inputs", ""),
        data.get("query_template_id", ""),
        int(data.get("is_threat",    False)),
        int(data.get("is_anomaly",   False)),
        float(data.get("anomaly_score", 0)),
        int(data.get("binary_label", 0)),
        float(data.get("attack_prob", 0)),
        data.get("attack_technique", "none")
    ))
    conn.commit()
    conn.close()

# ── ดึง Logs ล่าสุด ──────────────────────────────
def get_recent_logs(limit: int = 20):
    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()
    cur.execute("""
        SELECT timestamp, user_inputs, query_template_id,
               is_threat, is_anomaly, anomaly_score,
               binary_label, attack_prob, attack_technique
        FROM predictions
        ORDER BY id DESC
        LIMIT ?
    """, (limit,))
    rows = cur.fetchall()
    conn.close()
    return [
        {
            "timestamp":         r[0],
            "user_inputs":       r[1],
            "query_template_id": r[2],
            "is_threat":         bool(r[3]),
            "is_anomaly":        bool(r[4]),
            "anomaly_score":     r[5],
            "binary_label":      r[6],
            "attack_prob":       r[7],
            "attack_technique":  r[8],
        }
        for r in rows
    ]

# ── ดึง Stats ทั้งหมด ─────────────────────────────
def get_stats():
    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()

    # รวมทั้งหมด
    cur.execute("SELECT COUNT(*) FROM predictions")
    total = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM predictions WHERE is_threat=1")
    threats = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM predictions WHERE is_anomaly=1")
    anomalies = cur.fetchone()[0]

    cur.execute("SELECT COUNT(DISTINCT query_template_id) FROM predictions WHERE is_threat=1")
    unique_templates = cur.fetchone()[0]

    # Top technique
    cur.execute("""
        SELECT attack_technique, COUNT(*) as cnt
        FROM predictions
        WHERE is_threat=1
        GROUP BY attack_technique
        ORDER BY cnt DESC
        LIMIT 1
    """)
    top_row = cur.fetchone()
    top_technique = top_row[0] if top_row else "none"
    top_count     = top_row[1] if top_row else 0

    # Technique distribution
    cur.execute("""
        SELECT attack_technique, COUNT(*) as cnt
        FROM predictions
        WHERE is_threat=1
        GROUP BY attack_technique
        ORDER BY cnt DESC
    """)
    techniques = [{"technique": r[0], "count": r[1]} for r in cur.fetchall()]

    # Template distribution
    cur.execute("""
        SELECT query_template_id, attack_technique, COUNT(*) as cnt
        FROM predictions
        WHERE is_threat=1
        GROUP BY query_template_id, attack_technique
        ORDER BY cnt DESC
        LIMIT 8
    """)
    treemap = [{"template": r[0], "technique": r[1], "count": r[2]} for r in cur.fetchall()]

    # Trend ตาม 12 นาทีล่าสุด
    cur.execute("""
        SELECT strftime('%H:%M', timestamp) as minute,
               COUNT(*) as cnt
        FROM predictions
        WHERE is_threat=1
          AND timestamp >= datetime('now', '-12 minutes')
        GROUP BY minute
        ORDER BY minute ASC
    """)
    trend = [{"time": r[0], "count": r[1]} for r in cur.fetchall()]

    # Anomaly vs Supervised
    supervised = threats - anomalies
    high_conf  = 0
    cur.execute("SELECT COUNT(*) FROM predictions WHERE is_threat=1 AND attack_prob > 0.8")
    high_conf = cur.fetchone()[0]

    conn.close()

    return {
        "total":            total,
        "threats":          threats,
        "safe":             total - threats,
        "anomalies":        anomalies,
        "unique_templates": unique_templates,
        "top_technique":    top_technique,
            "top_count":        top_count,
        "top_pct":          round(top_count / max(threats, 1) * 100),
        "techniques":       techniques,
        "treemap":          treemap,
        "trend":            trend,
        "anomaly_count":    anomalies,
        "supervised_count": supervised,
        "high_conf_count":  high_conf,
        "anomaly_pct":      round(anomalies / max(threats, 1) * 100),
        "supervised_pct":   round(supervised / max(threats, 1) * 100),
    }

# ── ล้าง Database ────────────────────────────────
def clear_db():
    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()
    cur.execute("DELETE FROM predictions")
    cur.execute("DELETE FROM hourly_stats")
    conn.commit()
    conn.close()
    print("🗑️  Database cleared")

# ── รันตรงๆ เพื่อทดสอบ ──────────────────────────
if __name__ == "__main__":
    init_db()
    # ทดสอบบันทึก
    log_prediction({
        "user_inputs":       "test payload",
        "query_template_id": "airport-I1",
        "is_threat":         True,
        "is_anomaly":        False,
        "anomaly_score":     0.05,
        "binary_label":      1,
        "attack_prob":       0.95,
        "attack_technique":  "boolean"
    })
    print("📋 Recent logs:", get_recent_logs(1))
    print("📊 Stats:",       get_stats())