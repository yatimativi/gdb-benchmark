# Reproducibility scripts

Six small scripts that reproduce the headline numbers in the paper from
the data in this repository. All paths are resolved relative to the
repo root via `_paths.py`; no absolute paths are hardcoded.

## Requirements

```
pip install -r ../requirements.txt
```

The scripts depend only on `pandas`, `numpy`, `scipy`, `scikit-learn`,
`statsmodels`, and `matplotlib`. No vendor SDKs or network access are
needed; the scripts only analyze the CSV / JSONL data shipped in the
repository.

## What each script reproduces

| Script | Reproduces |
|---|---|
| `headline_table.py`   | Table 4 (per-model F0 / F1 / F2 / F3 / Trap / All), plus the tier rollup of response-pooled trap rates. |
| `reliability.py`      | Table 3 (author IRR + external rater kappas, with a diff against the precomputed `kappa_results.json`). |
| `tier_test.py`        | Tier chi-squared on the per-response binary outcome and the LRT for tier in a logistic GLM controlling for trap family; falls back to cluster-robust SEs (cluster on `scenario_id`) when the binomial GLMM is unavailable. |
| `arena_correlation.py`| Figure 2 numbers (Spearman / Pearson between trap displacement and Chatbot Arena Elo, plus leave-one-out range). |
| `probe1_stages.py`    | Section 7.2 / Appendix P (per-checkpoint F0 / F1 / F2 / F3 / Trap rates from the post-training probe, averaged across the GPT-4.1 and Kimi-K2 judges). |
| `discriminant_2x2.py` | Section 7.1 / Appendix O (per-cell DS>=2, sycophancy-positive, and within-cell Spearman rho between DS and max-sycophancy). |

## Usage

Run from the **repository root** (the directory containing `README.md`):

```bash
python code/headline_table.py
python code/reliability.py
python code/tier_test.py
python code/arena_correlation.py
python code/probe1_stages.py
python code/discriminant_2x2.py
```

Each script prints to stdout only; no files are written. Scripts share
utilities via `headline_table.py` and `_paths.py` (all paths repo-relative).

### Evaluating a new model

`generate_responses.py` generates responses for any new model and writes
a JSONL file compatible with the standard analysis pipeline:

```bash
# No API key needed — mock mode for pipeline verification:
python code/generate_responses.py --mock --model test-model

# Real evaluation (set API key env var first):
python code/generate_responses.py --model gpt-4o --provider openai

# See all options:
python code/generate_responses.py --help
```

## Notes on numerical reproducibility

### Exact reproductions
`headline_table.py`, `reliability.py`, and `discriminant_2x2.py` reproduce
paper values exactly (within floating-point rounding) from the checked-in
data. The tier chi-squared in `tier_test.py` (χ² = 143.53) also reproduces
exactly.

### Approximate reproductions

**Arena Elo (`arena_correlation.py`)**: The Elo scores hardcoded in the
script are paper-time snapshots from early 2026. Chatbot Arena Elo values
drift as new battles are collected; current values will differ. The paper
reports ρ = -0.839 (n=15). Running the script today may produce a slightly
different ρ because the underlying Elo inputs have changed. To reproduce
the paper exactly, use the Elo values stored in the script as-is (do not
update them). The script prints a reminder to this effect.

**GLMM LRT (`tier_test.py`)**: The paper's GLMM result (likelihood-ratio
test for tier in a mixed-effects logistic model with random intercepts per
`scenario_id`) was computed with `statsmodels 0.14`. The script uses
`BinomialBayesMixedGLM` when available and reports the same LRT statistic.
If the GLMM fails to converge (can happen with older statsmodels), the
script falls back to a logistic regression with cluster-robust standard
errors and prints a **FALLBACK** notice. The fallback test statistic will
differ from the paper; the tier effect and its significance will not.

**Probe studies (`probe1_stages.py`)**: The LLM-judge calls that produced
the probe scores are pre-computed and checked in; the script reads those
files rather than calling GPT-4.1 or Kimi-K2. Numeric values reproduce
exactly. If judge models are updated externally, re-running generation
would produce different judge scores.
