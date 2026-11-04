import itertools
import json
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

from utils import train_val_split

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
DTYPE = torch.float64


class InputNorm(nn.Module):
    def __init__(self, mean, std):
        super().__init__()
        self.register_buffer("mean", mean)
        self.register_buffer("std", std)

    def forward(self, x):
        return (x - self.mean) / self.std


class ResBlock(nn.Module):
    def __init__(self, dim, act_cls):
        super().__init__()
        self.block = nn.Sequential(nn.Linear(dim, dim), nn.LayerNorm(dim), act_cls())

    def forward(self, x):
        return x + self.block(x)


class TorchModel(nn.Module):

    def __init__(self):
        super().__init__()
        self.register_buffer("y_mean", torch.tensor(0.0, dtype=DTYPE))
        self.register_buffer("y_std", torch.tensor(1.0, dtype=DTYPE))

    def denorm(self, z):
        return z * self.y_std + self.y_mean

    def set_target_scale(self, y_mean, y_std):
        self.y_mean.fill_(y_mean)
        self.y_std.fill_(y_std)
        return self

    def predict(self, X):
        self.eval()
        self.to(DEVICE, DTYPE)
        with torch.no_grad():
            return self(torch.tensor(X, dtype=DTYPE, device=DEVICE)).cpu().numpy()


def normalize_targets(y_tr, y_val):
    y_mean, y_std = float(np.mean(y_tr)), max(float(np.std(y_tr)), 1e-8)
    return y_mean, y_std, (y_tr - y_mean) / y_std, (y_val - y_mean) / y_std


def input_stats(X):
    X = torch.tensor(X, dtype=DTYPE)
    return X.mean(dim=0), torch.clamp(X.std(dim=0), min=1e-8)


def settings(config, **keys):
    """Every combination of the named config grids: settings(cfg, lr="lrs", ...) -> [{"lr": ...}, ...]."""
    return [dict(zip(keys, values)) for values in itertools.product(*(config[k] for k in keys.values()))]


def train_single(model, X_tr, y_tr, X_val, y_val, max_epochs, patience, lr, weight_decay, extra=None,
                 lr_min=1e-7, eval_every=100):
    """Full-batch AdamW, learning rate cut tenfold on a validation plateau, stopped once it falls below lr_min."""
    model = model.to(DEVICE, DTYPE)
    X_tr, y_tr, X_val, y_val = (torch.tensor(a, dtype=DTYPE, device=DEVICE) for a in (X_tr, y_tr, X_val, y_val))
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=weight_decay)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode="min", factor=0.1, patience=patience)
    best_val, best_state = float("inf"), None
    for epoch in range(max_epochs):
        model.train()
        optimizer.zero_grad()
        loss = F.mse_loss(model(X_tr), y_tr)
        if extra is not None:
            loss = loss + extra(model)
        loss.backward()
        optimizer.step()
        if (epoch + 1) % eval_every == 0:
            model.eval()
            with torch.no_grad():
                val_loss = F.mse_loss(model(X_val), y_val).item()
            scheduler.step(val_loss)
            if val_loss < best_val:
                best_val = val_loss
                best_state = {k: v.cpu().clone() for k, v in model.state_dict().items()}
            if optimizer.param_groups[0]["lr"] < lr_min:
                break
    model.load_state_dict(best_state)
    model.eval()
    with torch.no_grad():
        final_train = F.mse_loss(model(X_tr), y_tr).item()
    return best_state, best_val, final_train, epoch + 1


def train_neural(build, grid, X, y, config, physics=None):
    X_tr, y_tr, X_val, y_val = train_val_split(X, y)
    input_mean, input_std = input_stats(X_tr)
    y_mean, y_std, y_tr_n, y_val_n = normalize_targets(y_tr, y_val)
    best = None
    for setting in grid:
        print(f"\n{setting}")
        extra = physics(setting, y_mean, y_std) if physics else None
        vals, states = [], []
        for seed in range(config["n_seeds"]):
            torch.manual_seed(seed)
            state, val_n, train_n, epochs = train_single(
                build(setting, input_mean, input_std), X_tr, y_tr_n, X_val, y_val_n, config["max_epochs"],
                config["patience"], setting["lr"], setting["weight_decay"], extra)
            vals.append(val_n * y_std ** 2)
            states.append(state)
            print(f"  seed {seed}: train={train_n * y_std ** 2:.2e}, val={vals[-1]:.2e} ({epochs} ep)")
        k = int(np.argmin(vals))
        if best is None or np.mean(vals) < best["mean_val_mse"]:
            best = {**setting, "mean_val_mse": float(np.mean(vals)), "val_mse": vals[k]}
            model = build(best, input_mean, input_std).to(DTYPE)
            model.load_state_dict(states[k])
            model.set_target_scale(y_mean, y_std).eval()
    return model, best


def save_checkpoint(model, params, results_dir, config):
    results_dir = Path(results_dir)
    results_dir.mkdir(parents=True, exist_ok=True)
    torch.save({"state_dict": model.state_dict(), "config": config}, results_dir / "model_best.pt")
    with open(results_dir / "params.json", "w") as fp:
        json.dump(params, fp, indent=2)


def load_checkpoint(path, build):
    ckpt = torch.load(Path(path) / "model_best.pt", map_location=DEVICE, weights_only=False)
    model = build(ckpt["config"]).to(DEVICE, DTYPE)
    model.load_state_dict(ckpt["state_dict"])
    model.eval()
    return model
