"""Per-model trap displacement table (reproduces Table 4).

Loads the unified dataset and prints a markdown table of per-model
displacement rates broken down by trap family (F1, F2, F3, F0), with
the headline Trap column defined as the mean of F1 and F2 cell rates,
plus an All column over every scored response. Sorted by Trap column.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _paths import DATA  # noqa: E402

# Tier mapping. Keys cover the model identifiers as they appear in
# unified_dataset.csv (some use ':' / '.', others use '-').
TIER = {
    "gemini-2.5-pro": "Frontier",
    "gemini-3.1-pro-preview": "Frontier",
    "gpt-5.4": "Frontier",
    "claude-sonnet-4-6": "Frontier",
    "deepseek-chat": "Frontier",
    "deepseek-reasoner": "Frontier",
    "gpt-4o": "Frontier",
    "gemini-2.5-flash": "Mid-tier",
    "gpt-5.4-mini-2026-03-17": "Mid-tier",
    "claude-haiku-4-5-20251001": "Mid-tier",
    "gpt-4o-mini": "Mid-tier",
    "ollama:mistral": "OW-small",
    "ollama:llama3": "OW-small",
    "ollama:llama3.1:8b": "OW-small",
    "ollama:llama3.1:70b": "OW-large",
    "ollama:qwen2.5:32b": "OW-large",
    "ollama:qwen2.5:72b": "OW-large",
    "ollama:nemotron": "OW-large",
}

# Pretty display names for the table.
DISPLAY = {
    "gemini-2.5-pro": "Gemini 2.5 Pro",
    "gemini-3.1-pro-preview": "Gemini 3.1 Pro Prev",
    "gpt-5.4": "GPT-5.4",
    "claude-sonnet-4-6": "Sonnet 4.6",
    "deepseek-chat": "DeepSeek Chat",
    "deepseek-reasoner": "DeepSeek Reasoner",
    "gpt-4o": "GPT-4o",
    "gemini-2.5-flash": "Gemini 2.5 Flash",
    "gpt-5.4-mini-2026-03-17": "GPT-5.4 mini",
    "claude-haiku-4-5-20251001": "Haiku 4.5",
    "gpt-4o-mini": "GPT-4o-mini",
    "ollama:mistral": "Mistral 7B",
    "ollama:llama3": "Llama 3 8B",
    "ollama:llama3.1:8b": "Llama 3.1 8B",
    "ollama:llama3.1:70b": "Llama 3.1 70B",
    "ollama:qwen2.5:32b": "Qwen2.5 32B",
    "ollama:qwen2.5:72b": "Qwen2.5 72B",
    "ollama:nemotron": "Nemotron",
}

FAMILY_LABEL = {0: "F0", 1: "F1", 2: "F2", 3: "F3"}


def avg_rater_displaced(df: pd.DataFrame) -> pd.Series:
    """Binary outcome: averaged-rater DS consensus, thresholded at >= 2."""
    return ((df["ds_a1"] + df["ds_a2"]) / 2.0 >= 2).astype(float)


def main() -> None:
    df = pd.read_csv(DATA)
    df = df.dropna(subset=["ds_a1", "ds_a2"]).copy()
    df["disp"] = avg_rater_displaced(df)

    # Sanity check: compare to precomputed `displaced` column if present.
    if "displaced" in df.columns:
        diff = (df["disp"].astype(int) - df["displaced"].astype(int)).abs().sum()
        print(f"check: recomputed displaced agrees with stored column on "
              f"{len(df) - int(diff)}/{len(df)} rows")
        print()

    rows = []
    for model, sub in df.groupby("model"):
        per_fam = {}
        for fam_int, fam_label in FAMILY_LABEL.items():
            fsub = sub[sub["trap_family"] == fam_int]
            per_fam[fam_label] = fsub["disp"].mean() if len(fsub) else float("nan")
        trap_rate = (per_fam["F1"] + per_fam["F2"]) / 2.0
        all_rate = sub["disp"].mean()
        rows.append({
            "model": model,
            "tier": TIER.get(model, "?"),
            "F1": per_fam["F1"], "F2": per_fam["F2"],
            "F3": per_fam["F3"], "F0": per_fam["F0"],
            "Trap": trap_rate, "All": all_rate,
        })

    out = pd.DataFrame(rows).sort_values("Trap")

    name_w = max(len(DISPLAY.get(m, m)) for m in out["model"])
    header = (f"{'Model'.ljust(name_w)}  {'Tier':<10} "
              f"{'F1':>6} {'F2':>6} {'F3':>6} {'F0':>6} {'Trap':>6} {'All':>6}")
    print(header)
    print("-" * len(header))
    for _, r in out.iterrows():
        name = DISPLAY.get(r["model"], r["model"])
        print(f"{name.ljust(name_w)}  {r['tier']:<10} "
              f"{r['F1'] * 100:5.1f}% {r['F2'] * 100:5.1f}% "
              f"{r['F3'] * 100:5.1f}% {r['F0'] * 100:5.1f}% "
              f"{r['Trap'] * 100:5.1f}% {r['All'] * 100:5.1f}%")

    print()
    print("Tier rollup (response-pooled, F1+F2 cells only):")
    trap_only = df[df["trap_family"].isin([1, 2])].copy()
    trap_only["tier"] = trap_only["model"].map(TIER)
    rollup = trap_only.groupby("tier")["disp"].agg(["mean", "count"])
    for tier, row in rollup.iterrows():
        print(f"  {tier:<10} {row['mean'] * 100:5.1f}%  (n={int(row['count'])})")


if __name__ == "__main__":
    main()
