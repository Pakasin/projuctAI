# ═══════════════════════════════════════════════════
# client.py v2 — SQLi Attacker Script (Balanced)
# ═══════════════════════════════════════════════════

import pandas as pd
import requests
import time
import random
from datetime import datetime

# ── CONFIG ───────────────────────────────────────
API_URL      = "http://127.0.0.1:8000/predict"
INTERVAL     = 2        # ส่งทุกกี่วินาที
SAMPLE_SIZE  = 500      # จำนวน rows ที่สุ่ม
ATTACK_RATIO = 0.5      # สัดส่วน Attack (0.5 = 50:50)
DATASET_PATH = "dataset.csv"
SHOW_DETAIL  = True

# ── COLORS ───────────────────────────────────────
RESET  = "\033[0m"
RED    = "\033[91m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
GRAY   = "\033[90m"
BOLD   = "\033[1m"

# ── LOAD & BALANCE DATASET ───────────────────────
print(f"{CYAN}📂 Loading dataset...{RESET}")
df = pd.read_csv(DATASET_PATH, low_memory=False)
df = df[['user_inputs', 'query_template_id', 'label', 'attack_technique']].copy()
df['attack_technique']  = df['attack_technique'].fillna('none')
df['query_template_id'] = df['query_template_id'].fillna('unknown')
df['user_inputs']       = df['user_inputs'].fillna('unknown')
df['label']             = df['label'].astype(int)

# Balance ตาม ATTACK_RATIO
n_attack = int(SAMPLE_SIZE * ATTACK_RATIO)
n_normal = SAMPLE_SIZE - n_attack

df_attack = df[df['label'] == 1].sample(n=min(n_attack, (df['label']==1).sum()), random_state=42)
df_normal = df[df['label'] == 0].sample(n=min(n_normal, (df['label']==0).sum()), random_state=42)
df_sample = pd.concat([df_attack, df_normal]).sample(frac=1, random_state=42).reset_index(drop=True)

print(f"{GREEN}✅ Loaded {len(df_sample)} payloads{RESET}")
print(f"   {RED}Attack : {(df_sample['label']==1).sum()}{RESET}")
print(f"   {GREEN}Normal : {(df_sample['label']==0).sum()}{RESET}")
print(f"\n{BOLD}🚀 Starting attack simulation → {API_URL}{RESET}")
print("─" * 65)

# ── STATS ─────────────────────────────────────────
stats = {
    "total":     0,
    "threat":    0,
    "safe":      0,
    "anomaly":   0,
    "correct":   0,
    "incorrect": 0,
    "errors":    0,
}

# ── MAIN LOOP ─────────────────────────────────────
idx = 0
while True:
    if idx >= len(df_sample):
        idx = 0
        df_sample = df_sample.sample(frac=1).reset_index(drop=True)
        print(f"\n{YELLOW}🔄 Reshuffled — starting new round{RESET}\n")

    row = df_sample.iloc[idx]
    idx += 1

    payload = {
        "user_inputs":       str(row['user_inputs']),
        "query_template_id": str(row['query_template_id'])
    }

    try:
        res    = requests.post(API_URL, json=payload, timeout=5)
        result = res.json()

        stats["total"] += 1

        is_threat  = result.get("is_threat", False)
        is_anomaly = result.get("is_anomaly", False)
        technique  = result.get("attack_technique", "none")
        prob       = result.get("attack_prob", 0)
        actual_lbl = int(row['label'])
        actual_tec = str(row['attack_technique'])

        # นับ stats
        if is_threat:
            stats["threat"] += 1
        else:
            stats["safe"] += 1
        if is_anomaly:
            stats["anomaly"] += 1

        # เช็ค correct/incorrect
        predicted_lbl = 1 if is_threat else 0
        if predicted_lbl == actual_lbl:
            stats["correct"] += 1
        else:
            stats["incorrect"] += 1

        if SHOW_DETAIL:
            ts           = datetime.now().strftime("%H:%M:%S")
            status_color = RED if is_threat else GREEN
            status_text  = "🔴 THREAT" if is_threat else "🟢 SAFE  "
            anomaly_text = f" {YELLOW}[ANOMALY]{RESET}" if is_anomaly else ""
            correct_icon = "✓" if predicted_lbl == actual_lbl else "✗"
            correct_color= GREEN if predicted_lbl == actual_lbl else RED
            actual_text  = "ATTACK" if actual_lbl == 1 else "NORMAL"

            print(
                f"{GRAY}[{ts}]{RESET} "
                f"{status_color}{status_text}{RESET} "
                f"{CYAN}{technique:<10}{RESET} "
                f"prob:{BOLD}{prob:.2f}{RESET} "
                f"actual:{actual_text:<6} "
                f"{correct_color}[{correct_icon}]{RESET}"
                f"{anomaly_text} "
                f"{GRAY}{str(row['user_inputs'])[:35]}...{RESET}"
            )

        # Summary ทุก 10 requests
        if stats["total"] % 10 == 0:
            acc      = stats["correct"] / max(stats["total"], 1) * 100
            det_rate = stats["threat"]  / max(stats["total"], 1) * 100
            print(f"\n{'─'*65}")
            print(f"  {BOLD}📊 Summary [{stats['total']} requests]{RESET}")
            print(f"     {RED}Threats   : {stats['threat']} ({det_rate:.1f}%){RESET}")
            print(f"     {GREEN}Safe      : {stats['safe']}{RESET}")
            print(f"     {YELLOW}Anomalies : {stats['anomaly']}{RESET}")
            print(f"     {CYAN}Accuracy  : {acc:.1f}%{RESET}")
            print(f"     Correct   : {stats['correct']} | Incorrect: {stats['incorrect']}")
            print(f"     Errors    : {stats['errors']}")
            print(f"{'─'*65}\n")

    except requests.exceptions.ConnectionError:
        stats["errors"] += 1
        print(f"{RED}❌ [{datetime.now().strftime('%H:%M:%S')}] Cannot connect → {API_URL}{RESET}")
        print(f"   รัน server ก่อน: uvicorn server:app --reload")
        time.sleep(5)
        continue

    except Exception as e:
        stats["errors"] += 1
        print(f"{YELLOW}⚠️  Error: {e}{RESET}")

    time.sleep(INTERVAL)