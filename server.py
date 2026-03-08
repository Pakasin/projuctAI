import joblib
import numpy as np
from fastapi import FastAPI
from pydantic import BaseModel
from scipy.sparse import hstack, csr_matrix

app = FastAPI(title="SQLi Hybrid Detection API v3")

# โหลด Models
tfidf    = joblib.load('models/tfidf.pkl')
le_tpl   = joblib.load('models/le_template.pkl')
le_tec   = joblib.load('models/le_technique.pkl')
iso      = joblib.load('models/iso_forest.pkl')
rf       = joblib.load('models/rf_binary.pkl')
xgb      = joblib.load('models/xgb_multi.pkl')

class SQLiInput(BaseModel):
    user_inputs:       str
    query_template_id: str

@app.post("/predict")
def predict(data: SQLiInput):
    # TF-IDF transform
    X_tfidf = tfidf.transform([data.user_inputs])

    # Template encode
    try:
        tpl = le_tpl.transform([data.query_template_id])[0]
    except:
        tpl = 0
    X_tpl   = csr_matrix([[tpl]])
    X_input = hstack([X_tfidf, X_tpl])

    # Layer 1: Isolation Forest
    iso_score  = float(iso.decision_function(X_input)[0])
    is_anomaly = bool(iso.predict(X_input)[0] == -1)

    # Layer 2: Random Forest
    binary_pred = int(rf.predict(X_input)[0])
    binary_prob = float(rf.predict_proba(X_input)[0][1])

    # Layer 3: XGBoost
    tec_idx  = xgb.predict(X_input)[0]
    tec_pred = le_tec.inverse_transform([tec_idx])[0]

    # Hybrid result
    is_threat = is_anomaly or binary_pred == 1

    return {
        "is_threat":        is_threat,
        "is_anomaly":       is_anomaly,
        "anomaly_score":    round(iso_score, 4),
        "binary_label":     binary_pred,
        "attack_prob":      round(binary_prob, 4),
        "attack_technique": tec_pred
    }

@app.get("/")
def health():
    return {"status": "SQLi Hybrid API v3 running"}