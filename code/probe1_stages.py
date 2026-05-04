"""Post-training stage probe (reproduces Section 7.2 / Appendix P).

Loads the GPT-4.1 and Kimi-K2 judge CSVs in
``probe1_post_training/judges/``, averages the two judges' DS>=2 binary
outcomes per response, and prints per-checkpoint per-family rates plus
a Trap column (mean of F1+F2). Checkpoints span base / SFT / DPO / RLHF
variants for OLMo, Qwen, and Mistral families.
"""

from __future__ import annotations

import glob
import re
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _paths import PROBE1  # noqa: E402

CHECKPOINT_LABEL = {
    "probe1_local_olmo2-7b-base": "olmo2-7b-base",
    "probe1_local_olmo2-7b-sft": "olmo2-7b-sft",
    "probe1_local_olmo2-7b-dpo": "olmo2-7b-dpo",
    "probe1_local_qwen25-7b-base": "qwen25-7b-base",
    "probe1_qwen25_7b_instruct": "qwen25-7b-instruct",
    "probe1_mistral7b_v02_instruct": "mistral7b-v02-instruct",
    "probe1_mistral7b_v03_instruct": "mistral7b-v03-instruct",
}

# Display order matches the manuscript table.
ORDER = [
    "olmo2-7b-base", "olmo2-7b-sft", "olmo2-7b-dpo",
    "qwen25-7b-base", "qwen25-7b-instruct",
    "mistral7b-v02-instruct", "mistral7b-v03-instruct",
]


def _family_from_id(scenario_id: str) -> int:
    m = re.match(r"^F(\d)-", scenario_id)
    return int(m.group(1)) if m else -1


def main() -> None:
    files = sorted(glob.glob(str(PROBE1 / "judges" / "*.csv")))
    if not files:
        print("No probe1 judge CSVs found.")
        return

    frames = []
    for f in files:
        df = pd.read_csv(f)
        frames.append(df)
    cat = pd.concat(frames, ignore_index=True)

    cat["fam"] = cat["scenario_id"].apply(_family_from_id)

    # Average the raw DS scores (0..3) across the two judges per response,
    # then apply the same >= 2 threshold used for the main 18-model analysis
    # (averaged-rater consensus). This matches the paper's §7.2 method.
    per_resp = (cat.groupby(["response_type", "scenario_id", "fam"])
                ["displacement_severity"].mean().reset_index())
    per_resp["disp_bin"] = (per_resp["displacement_severity"] >= 2.0).astype(int)

    name_w = max(len(v) for v in ORDER)
    header = (f"{'Checkpoint'.ljust(name_w)}  "
              f"{'F1':>6} {'F2':>6} {'F3':>6} {'F0':>6} {'Trap':>6}")
    print(header)
    print("-" * len(header))

    for ckpt in ORDER:
        rt = next((k for k, v in CHECKPOINT_LABEL.items() if v == ckpt), None)
        if rt is None:
            continue
        sub = per_resp[per_resp["response_type"] == rt]
        if len(sub) == 0:
            continue
        rates = {}
        for fam in [1, 2, 3, 0]:
            cell = sub[sub["fam"] == fam]
            rates[fam] = cell["disp_bin"].mean() if len(cell) else float("nan")
        trap = (rates[1] + rates[2]) / 2.0
        print(f"{ckpt.ljust(name_w)}  "
              f"{rates[1] * 100:5.1f}% {rates[2] * 100:5.1f}% "
              f"{rates[3] * 100:5.1f}% {rates[0] * 100:5.1f}% "
              f"{trap * 100:5.1f}%")


if __name__ == "__main__":
    main()
