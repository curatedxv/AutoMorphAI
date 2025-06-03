def make_decision(df_with_anomalies):
    anomaly_ratio = (df_with_anomalies["anomaly"] == 1).mean()
    if anomaly_ratio > 0.2:
        return "scale_up"
    elif anomaly_ratio > 0.1:
        return "notify"
    else:
        return "no_action"
