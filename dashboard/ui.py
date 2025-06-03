from fastapi import FastAPI
import pandas as pd
from ml.model import detect_anomalies
from engine.decision import make_decision

print("UI.PY LOADED!")

app = FastAPI()

@app.get("/")
def read_root():
    return {"AutoMorphAI": "Running"}

@app.get("/analyze")
def analyze():
    df = pd.read_csv("data/metrics_sample.csv")
    df_with_anomalies = detect_anomalies(df)
    action = make_decision(df_with_anomalies)
    return {
        "action": action,
        "anomalies": df_with_anomalies["anomaly"].tolist()
    }
