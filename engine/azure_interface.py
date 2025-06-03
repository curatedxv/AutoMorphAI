import os, pandas as pd
from datetime import datetime, timedelta
from dateutil import tz
from azure.identity import DefaultAzureCredential
from azure.monitor.query import MetricsQueryClient
from azure.mgmt.compute import ComputeManagementClient

def get_vm_metrics(minutes=5):
    sid = os.getenv("AZURE_SUBSCRIPTION_ID")
    rg = os.getenv("AZURE_RESOURCE_GROUP")
    vm = os.getenv("AZURE_VM_NAME")
    print("SUB:", sid, "RG:", rg, "VM:", vm)
    if not (sid and rg and vm):
        print("Missing env vars")
        return pd.DataFrame()
    cred = DefaultAzureCredential()
    mc = MetricsQueryClient(cred)
    uri = f"/subscriptions/{sid}/resourceGroups/{rg}/providers/Microsoft.Compute/virtualMachines/{vm}"
    et = datetime.utcnow().replace(tzinfo=tz.tzutc())
    st = et - timedelta(minutes=mins)
    try:
        data = mc.query_resource(uri,
                                 metric_names=["Percentage CPU"],
                                 timespan=(st, et),
                                 granularity=timedelta(minutes=1),
                                 aggregations=["Average"])
    except Exception as e:
        print("Azure API error:", e)
        return pd.DataFrame()
    if not data.metrics:
        print("No metrics")
        return pd.DataFrame()
    rows = []
    for m in data.metrics:
        for ts in m.timeseries:
            for d in ts.data:
                if d.timestamp and d.average is not None:
                    rows.append({
                        "timestamp": pd.to_datetime(d.timestamp),
                        "cpu": d.average
                    })
    if not rows:
        print("No data")
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    print("Collected:", df)
    return df

def scale_up_vmss():
    sid = os.getenv("AZURE_SUBSCRIPTION_ID")
    rg = os.getenv("AZURE_RESOURCE_GROUP")
    ss = os.getenv("AZURE_VMSS_NAME")
    if not (sid and rg and ss):
        print("Missing VMSS vars")
        return
    cred = DefaultAzureCredential()
    cc = ComputeManagementClient(cred, sid)
    print(f"[Azure] VMSS: {ss}")
    vmss = cc.virtual_machine_scale_sets.get(rg, ss)
    cap = vmss.sku.capacity
    print(f"[Azure] Curr cap: {cap}")
    vmss.sku.capacity = cap + 1
    poller = cc.virtual_machine_scale_sets.begin_create_or_update(rg, ss, vmss)
    poller.result()
    print(f"[Azure] Scaled to {cap + 1}")

def start_vm():
    sid = os.getenv("AZURE_SUBSCRIPTION_ID")
    rg = os.getenv("AZURE_RESOURCE_GROUP")
    vm = os.getenv("AZURE_VM_NAME")
    if not (sid and rg and vm):
        print("Missing VM vars")
        return
    cred = DefaultAzureCredential()
    cc = ComputeManagementClient(cred, sid)
    print(f"[Azure] Starting: {vm}")
    poller = cc.virtual_machines.begin_start(rg, vm)
    poller.result()
    print(f"[Azure] Started {vm}")

def stop_vm():
    sid = os.getenv("AZURE_SUBSCRIPTION_ID")
    rg = os.getenv("AZURE_RESOURCE_GROUP")
    vm = os.getenv("AZURE_VM_NAME")
    if not (sid and rg and vm):
        print("Missing VM vars")
        return
    cred = DefaultAzureCredential()
    cc = ComputeManagementClient(cred, sid)
    print(f"[Azure] Stopping: {vm}")
    poller = cc.virtual_machines.begin_power_off(rg, vm)
    poller.result()
    print(f"[Azure] Stopped {vm}")

def apply_action(act):
    print("Action:", act)
    if act == "scale_up":
        if os.getenv("AZURE_VMSS_NAME"):
            scale_up_vmss()
        elif os.getenv("AZURE_VM_NAME"):
            start_vm()
        else:
            print("[Azure] No target")
    elif act == "start_vm":
        start_vm()
    elif act == "stop_vm":
        stop_vm()
    elif act == "notify":
        print("[Azure] Notification")
    else:
        print("[Azure] No action")
