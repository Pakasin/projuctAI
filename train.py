# ═══════════════════════════════════════════════════
# SQLi Hybrid Model Training v3 - TF-IDF Edition
# Features: user_inputs (TF-IDF) + query_template_id
# Targets:  label (binary) + attack_technique (multi)
# ═══════════════════════════════════════════════════

import pandas as pd
import numpy as np
import joblib
import os
import warnings
warnings.filterwarnings('ignore')

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing       import LabelEncoder
from sklearn.ensemble            import IsolationForest, RandomForestClassifier
from sklearn.model_selection     import train_test_split
from sklearn.metrics             import classification_report, accuracy_score
from scipy.sparse                import hstack, csr_matrix
from xgboost                     import XGBClassifier

os.makedirs('models', exist_ok=True)

# ─────────────────────────────────────────
# STEP 1: LOAD DATA
# ─────────────────────────────────────────
print("📂 [1/6] Loading dataset...")
df = pd.read_csv('dataset.csv', low_memory=False)
print(f"   Raw rows: {len(df):,}")

# ─────────────────────────────────────────
# STEP 2: CLEAN DATA
# ─────────────────────────────────────────
print("🧹 [2/6] Cleaning data...")

# 2.1 ลบ Duplicates
df = df.drop_duplicates()
print(f"   After drop duplicates: {len(df):,}")

# 2.2 เติม Missing Values
df['attack_technique']  = df['attack_technique'].fillna('none')
df['user_inputs']       = df['user_inputs'].fillna('unknown')
df['query_template_id'] = df['query_template_id'].fillna('unknown')
df['label']             = df['label'].astype(int)

# 2.3 ลบ label=1 ที่ไม่มี attack_technique
df = df[~((df['label'] == 1) & (df['attack_technique'] == 'none'))]
print(f"   After clean: {len(df):,}")

# ─────────────────────────────────────────
# STEP 3: SAMPLE (ประหยัด RAM)
# ─────────────────────────────────────────
print("✂️  [3/6] Sampling for balance...")

df_attack = df[df['label'] == 1]
df_normal = df[df['label'] == 0]

# Sample Normal ให้เท่ากับ Attack เพื่อ balance + ประหยัด RAM
df_normal_sample = df_normal.sample(n=len(df_attack), random_state=42)
df_bal = pd.concat([df_attack, df_normal_sample]).sample(frac=1, random_state=42).reset_index(drop=True)
print(f"   Balanced: {len(df_bal):,} rows")

# ─────────────────────────────────────────
# STEP 4: TF-IDF VECTORIZE
# ─────────────────────────────────────────
print("🔢 [4/6] TF-IDF Vectorizing...")

# TF-IDF บน user_inputs
# analyzer='char_wb' → วิเคราะห์ระดับตัวอักษร จับ SQL pattern ได้ดีกว่า word
tfidf = TfidfVectorizer(
    analyzer='char_wb',   # character n-gram
    ngram_range=(2, 4),   # จับ pattern 2-4 ตัวอักษร เช่น "OR ", "' --"
    max_features=5000,    # จำกัด feature เพื่อประหยัด RAM
    sublinear_tf=True     # log scaling ลด noise
)
X_tfidf = tfidf.fit_transform(df_bal['user_inputs'].astype(str))
print(f"   TF-IDF shape: {X_tfidf.shape}")

# Encode query_template_id แล้วรวมกับ TF-IDF
le_tpl = LabelEncoder()
tpl_encoded = le_tpl.fit_transform(df_bal['query_template_id'].astype(str))
X_tpl = csr_matrix(tpl_encoded.reshape(-1, 1))

# รวม TF-IDF + template feature
X = hstack([X_tfidf, X_tpl])
print(f"   Final feature shape: {X.shape}")

# Labels
y_binary = df_bal['label'].values
le_tec   = LabelEncoder()
y_multi  = le_tec.fit_transform(df_bal['attack_technique'])
print(f"   Attack techniques: {list(le_tec.classes_)}")

# Train/Test Split
X_train, X_test, y_bin_tr, y_bin_te, y_mul_tr, y_mul_te = train_test_split(
    X, y_binary, y_multi,
    test_size=0.2, random_state=42, stratify=y_binary
)
print(f"   Train: {X_train.shape[0]:,} | Test: {X_test.shape[0]:,}")

# ─────────────────────────────────────────
# STEP 5: TRAIN MODELS
# ─────────────────────────────────────────
print("🤖 [5/6] Training models...")

# ── Layer 1: Isolation Forest ──
print("   Layer 1: Isolation Forest...")
iso = IsolationForest(
    n_estimators=100,
    contamination=0.1,
    random_state=42,
    n_jobs=-1
)
iso.fit(X_train)
iso_pred  = iso.predict(X_test)
iso_count = sum(iso_pred == -1)
print(f"   ✅ Anomalies: {iso_count:,}/{X_test.shape[0]:,}")

# ── Layer 2: Random Forest Binary ──
print("   Layer 2: Random Forest (Binary)...")
rf = RandomForestClassifier(
    n_estimators=100,
    max_depth=15,
    random_state=42,
    n_jobs=-1
)
rf.fit(X_train, y_bin_tr)
rf_pred = rf.predict(X_test)
rf_acc  = accuracy_score(y_bin_te, rf_pred)
print(f"   ✅ Binary Accuracy: {rf_acc*100:.2f}%")
print(classification_report(y_bin_te, rf_pred,
      target_names=['Normal', 'Attack']))

# ── Layer 3: XGBoost Multi-class ──
print("   Layer 3: XGBoost (Multi-class)...")
xgb = XGBClassifier(
    n_estimators=100,
    max_depth=6,
    learning_rate=0.1,
    eval_metric='mlogloss',
    tree_method='hist',    # เร็วขึ้นมากกับ sparse data
    random_state=42,
    n_jobs=-1
)
xgb.fit(X_train, y_mul_tr)
xgb_pred = xgb.predict(X_test)
xgb_acc  = accuracy_score(y_mul_te, xgb_pred)
print(f"   ✅ Multi Accuracy: {xgb_acc*100:.2f}%")
print(classification_report(y_mul_te, xgb_pred,
      target_names=le_tec.classes_))

# ─────────────────────────────────────────
# STEP 6: SAVE
# ─────────────────────────────────────────
print("💾 [6/6] Saving models...")
joblib.dump(tfidf,   'models/tfidf.pkl')
joblib.dump(le_tpl,  'models/le_template.pkl')
joblib.dump(le_tec,  'models/le_technique.pkl')
joblib.dump(iso,     'models/iso_forest.pkl')
joblib.dump(rf,      'models/rf_binary.pkl')
joblib.dump(xgb,     'models/xgb_multi.pkl')

print("\n🎉 Training Complete!")
print(f"   Binary Accuracy : {rf_acc*100:.2f}%")
print(f"   Multi  Accuracy : {xgb_acc*100:.2f}%")
print("   Models saved → /models/")