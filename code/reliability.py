"""Inter-rater reliability (reproduces Table 3).

Computes Cohen's quadratic-weighted kappa between A1 and A2 on the full
4134-response corpus for GF / FA / DS, and Gwet's AC1 for the binary
DS>=2 outcome. Then recomputes external validation kappas (R1 vs R2,
etc.) on the 191-item subset and prints the diff against the precomputed
values in kappa_results.json.

Note on binary agreement: we deliberately do not report Cohen's binary
kappa for the DS>=2 outcome. The two authors apply slightly different
thresholds on that boundary (A1 marginal 8.1%, A2 marginal 14.6%);
Cohen's binary kappa is depressed under that marginal asymmetry by a
known artifact even though percent agreement is high. Gwet's AC1 is the
prevalence-stable index used throughout the manuscript (AC1 = 0.896).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _paths import DATA, EXT  # noqa: E402


def quadratic_weighted_kappa(y1: np.ndarray, y2: np.ndarray) -> float:
    """Cohen's quadratic-weighted kappa from scratch."""
    y1 = np.asarray(y1)
    y2 = np.asarray(y2)
    cats = np.union1d(np.unique(y1), np.unique(y2))
    cat_idx = {c: i for i, c in enumerate(cats)}
    k = len(cats)
    if k == 1:
        return 1.0
    O = np.zeros((k, k), dtype=float)
    for a, b in zip(y1, y2):
        O[cat_idx[a], cat_idx[b]] += 1
    n = O.sum()
    row = O.sum(axis=1)
    col = O.sum(axis=0)
    E = np.outer(row, col) / n
    W = np.zeros((k, k), dtype=float)
    denom = (k - 1) ** 2
    for i in range(k):
        for j in range(k):
            W[i, j] = ((cats[i] - cats[j]) ** 2) / denom
    num = (W * O).sum()
    den = (W * E).sum()
    return 1.0 - num / den if den > 0 else 1.0


def gwet_ac1_binary(y1: np.ndarray, y2: np.ndarray) -> float:
    """Gwet's AC1 for two raters on binary labels."""
    y1 = np.asarray(y1).astype(int)
    y2 = np.asarray(y2).astype(int)
    po = (y1 == y2).mean()
    # Marginal proportions for category 1, averaged across raters.
    pi1 = ((y1.sum() + y2.sum()) / (2.0 * len(y1)))
    pe = 2.0 * pi1 * (1.0 - pi1)
    return (po - pe) / (1.0 - pe) if pe < 1 else 1.0


def _safe_pair(df: pd.DataFrame, c1: str, c2: str) -> pd.DataFrame:
    sub = df[[c1, c2]].dropna()
    return sub


def main() -> None:
    df = pd.read_csv(DATA)

    print("Author IRR (A1 vs A2) on full corpus")
    print("-" * 60)
    for dim in ["gf", "fa", "ds"]:
        if dim == "fa":
            # FA is coded as -1 (N/A) on F0 and F3 scenarios where no binding
            # constraint is present. Exclude those rows before computing kappa.
            sub = df[(df["fa_a1"] != -1) & (df["fa_a2"] != -1)][
                ["fa_a1", "fa_a2"]
            ].dropna()
        else:
            sub = _safe_pair(df, f"{dim}_a1", f"{dim}_a2")
        kw = quadratic_weighted_kappa(sub.iloc[:, 0].values, sub.iloc[:, 1].values)
        print(f"  {dim.upper():3s} quadratic-weighted kappa = {kw:.3f}  (n={len(sub)})")

    # Prevalence-stable agreement index on the binary headline outcome.
    sub = _safe_pair(df, "ds_a1", "ds_a2")
    b1 = (sub["ds_a1"] >= 2).astype(int).values
    b2 = (sub["ds_a2"] >= 2).astype(int).values
    print(f"  DS>=2 Gwet's AC1           = {gwet_ac1_binary(b1, b2):.3f}"
          f"  [paper reports 0.896]")

    print()
    print("External validation (191-item subset)")
    print("-" * 60)
    ext = pd.read_csv(EXT / "all_raters_scores.csv")

    pairs = {
        "A1 vs A2 (author IRR)": [("gf_a1", "gf_a2"), ("fa_a1", "fa_a2"),
                                  ("ds_a1", "ds_a2")],
        "R1 vs R2": [("gf_r1", "gf_r2"), ("fa_r1", "fa_r2"),
                     ("ds_r1", "ds_r2")],
        "R1 vs Author": [("gf_r1", "gf_author"), ("fa_r1", "fa_author"),
                         ("ds_r1", "ds_author")],
        "R2 vs Author": [("gf_r2", "gf_author"), ("fa_r2", "fa_author"),
                         ("ds_r2", "ds_author")],
    }

    recomputed: dict[str, dict[str, dict[str, float | int]]] = {}
    for label, dims in pairs.items():
        recomputed[label] = {}
        print(f"\n  {label}")
        for c1, c2 in dims:
            dim = c1.split("_")[0]
            sub = _safe_pair(ext, c1, c2)
            sub = sub[(sub[c1] != -1) & (sub[c2] != -1)]
            if len(sub) == 0:
                recomputed[label][dim] = {"kappa": None, "n": 0}
                print(f"    {dim.upper():3s}  (no overlap)")
                continue
            kw = quadratic_weighted_kappa(sub[c1].values, sub[c2].values)
            recomputed[label][dim] = {"kappa": round(kw, 3), "n": len(sub)}
            print(f"    {dim.upper():3s} kappa = {kw:.3f}  (n={len(sub)})")

    # Verify against the stored kappa_results.json TOTAL block.
    stored_path = EXT / "kappa_results.json"
    if stored_path.exists():
        stored = json.loads(stored_path.read_text())
        total = stored.get("TOTAL", {})
        print()
        print("Diff vs kappa_results.json (TOTAL block):")
        print("-" * 60)
        any_diff = False
        for label, dims in recomputed.items():
            for dim, val in dims.items():
                if val["kappa"] is None:
                    continue
                expected = total.get(label, {}).get(dim, {}).get("kappa")
                if expected is None:
                    continue
                delta = abs(val["kappa"] - expected)
                if delta > 0.005:
                    any_diff = True
                    print(f"  {label:<25s} {dim.upper():3s} "
                          f"recomputed={val['kappa']:.3f} stored={expected:.3f} "
                          f"diff={delta:.3f}")
        if not any_diff:
            print("  All recomputed kappas match stored values within 0.005.")


if __name__ == "__main__":
    main()
