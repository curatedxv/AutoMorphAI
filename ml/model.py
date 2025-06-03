import torch,torch.nn as nn, numpy as np, pandas as pd, os
from sklearn.preprocessing import StandardScaler

class AE(nn.Module):
    def __init__(self, dim):
        super(AE, self).__init__()
        self.e = nn.Sequential(
            nn.Linear(dim, 8),
            nn.ReLU(),
            nn.Linear(8, 4)
        )
        self.d = nn.Sequential(
            nn.Linear(4, 8),
            nn.ReLU(),
            nn.Linear(8, dim)
        )
    def forward(self, x):
        return self.d(self.e(x))

sc = StandardScaler()
ae = AE(1)

def train_ae(df, epochs=50):
    arr = df[["cpu"]].values.astype(np.float32)
    s = sc.fit_transform(arr)
    t = torch.tensor(s, dtype=torch.float32)
    opt = torch.optim.Adam(ae.parameters(), lr=0.01)
    loss_fn = nn.MSELoss()
    ae.train()
    for _ in range(epochs):
        opt.zero_grad()
        r = ae(t)
        l = loss_fn(r, t)
        l.backward()
        opt.step()

def up_ae(df, epochs=3):
    arr = df[["cpu"]].values.astype(np.float32)
    s = sc.transform(arr)
    t = torch.tensor(s, dtype=torch.float32)
    opt = torch.optim.Adam(ae.parameters(), lr=0.001)
    loss_fn = nn.MSELoss()
    ae.train()
    for _ in range(epochs):
        opt.zero_grad()
        r = ae(t)
        l = loss_fn(r, t)
        l.backward()
        opt.step()

if os.path.exists("data/metrics_normal.csv"):
    df0 = pd.read_csv("data/metrics_normal.csv")
    train_ae(df0, epochs=150)
else:
    print("WARNING: data/metrics_normal.csv not found")

def detect(df):
    x = torch.FloatTensor(sc.transform(df[['cpu']]))
    ae.eval()
    with torch.no_grad():
        r = ae(x)
        err = torch.mean((x - r) ** 2, dim=1)
    thresh = err.mean() + err.std()
    d = df.copy()
    d["anomaly"] = (err > thresh).int().numpy()
    return d
