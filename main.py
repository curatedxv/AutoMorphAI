from ml.model import detect, train_ae
from engine.decision import make_decision
from engine.azure_interface import apply_action, get_vm_metrics
import pandas as pd
import time, os

MF = "metrics_log.csv"
hist = pd.DataFrame()

def append_metrics(df,fn,keep=20):
    if 'timestamp' in df:
        df=df.copy()
        df['timestamp']=pd.to_datetime(df['timestamp']).dt.tz_localize(None)
    if os.path.exists(fn):
        old=pd.read_csv(fn)
        if not old.empty and 'timestamp' in old:
            old['timestamp']=pd.to_datetime(old['timestamp']).dt.tz_localize(None)
    else:
        old=pd.DataFrame()
    if not df.empty:
        if not old.empty:
            allm=pd.concat([old,df])
        else:
            allm=df
        allm=allm.drop_duplicates(subset="timestamp").sort_values("timestamp")
        allm=allm.tail(keep)
        allm.to_csv(fn,index=False)

print("[AutoMorphAI] Continuous monitoring started! Press Ctrl+C to stop.")

try:
    while True:
        nm = get_vm_metrics(minutes=60)
        if nm.empty:
            print("No real metrics found, using demo data for training!")
            nm = pd.DataFrame({
                "cpu":[0.3,0.32,0.28,0.92,0.3],
                "memory":[0.4,0.41,0.39,0.95,0.4],
                "response_time":[120,121,123,500,122],
                "timestamp":pd.date_range("2023-01-01",periods=5,freq='min')
            })
        hist=pd.concat([hist,nm]).drop_duplicates(subset="timestamp")
        train_ae(hist.tail(100),epochs=20)

        cm = get_vm_metrics(minutes=5)
        if cm.empty:
            print("No real current metrics, using demo data for detection!")
            cm = nm.tail(5)
        anomalies = detect(cm)
        act = make_decision(anomalies)

        apply_action(act)
        append_metrics(cm,MF,keep=20)
        print(f"[AutoMorphAI] Cycle finished. Action applied: {act}")
        print(f"[AutoMorphAI] Detected anomalies: {anomalies}")
        time.sleep(60)
except KeyboardInterrupt:
    print("\n[AutoMorphAI] Monitoring stopped by user.")
