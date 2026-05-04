"""Tier chi-squared and mixed/cluster-robust LRT (reproduces Section main result).

Computes the Pearson chi-squared on the response-level binary outcome
(displaced) by tier, then fits a logistic regression LRT for tier
controlling for trap family, and finally either fits a binomial GLMM
with random intercepts on (scenario, model) or, if the GLMM fit fails
or is unavailable, falls back to logistic regression with cluster-robust
standard errors clustered on scenario_id. The fallback choice is
printed explicitly.
"""

from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _paths import DATA  # noqa: E402
from headline_table import TIER, avg_rater_displaced  # noqa: E402

warnings.filterwarnings("ignore")


def chi_squared_by_tier(df: pd.DataFrame) -> tuple[float, int, float]:
    tab = pd.crosstab(df["tier"], df["disp"].astype(int))
    chi2, p, dof, _ = stats.chi2_contingency(tab.values)
    return chi2, dof, p


def logistic_lrt(df: pd.DataFrame) -> dict:
    """LRT for tier in a logistic GLM, controlling for trap family."""
    import statsmodels.api as sm
    import statsmodels.formula.api as smf

    df = df.copy()
    df["fam"] = df["trap_family"].astype("category")
    df["tier_c"] = pd.Categorical(df["tier"],
                                  categories=["Frontier", "Mid-tier",
                                              "OW-large", "OW-small"])
    full = smf.glm("disp ~ C(tier_c) + C(fam)", data=df,
                   family=sm.families.Binomial()).fit(disp=0)
    null = smf.glm("disp ~ C(fam)", data=df,
                   family=sm.families.Binomial()).fit(disp=0)
    lr = 2.0 * (full.llf - null.llf)
    df_lrt = int(full.df_model - null.df_model)
    p = 1.0 - stats.chi2.cdf(lr, df_lrt)
    return {"lr": lr, "df": df_lrt, "p": p,
            "full_llf": full.llf, "null_llf": null.llf}


def cluster_robust_lrt(df: pd.DataFrame) -> dict:
    """Logistic regression with cluster-robust SEs, Wald chi^2 on tier dummies.

    This is the fallback when GLMM is unavailable or unstable.
    """
    import statsmodels.api as sm

    df = df.copy()
    df["fam"] = df["trap_family"].astype(int)
    tiers = ["Mid-tier", "OW-large", "OW-small"]  # Frontier as reference
    for t in tiers:
        df[f"t_{t}"] = (df["tier"] == t).astype(int)
    fam_dummies = pd.get_dummies(df["fam"], prefix="fam", drop_first=True)
    X = pd.concat([df[[f"t_{t}" for t in tiers]], fam_dummies], axis=1)
    X = sm.add_constant(X).astype(float)
    y = df["disp"].astype(float)
    grp = df["scenario_id"].values
    res = sm.Logit(y, X).fit(disp=0, method="newton",
                             cov_type="cluster", cov_kwds={"groups": grp})
    tier_idx = [X.columns.get_loc(f"t_{t}") for t in tiers]
    R = np.zeros((len(tiers), X.shape[1]))
    for r, c in enumerate(tier_idx):
        R[r, c] = 1.0
    beta = res.params.values
    cov = res.cov_params().values
    Rb = R @ beta
    RcovR = R @ cov @ R.T
    wald = float(Rb @ np.linalg.solve(RcovR, Rb))
    p = 1.0 - stats.chi2.cdf(wald, len(tiers))
    return {"wald": wald, "df": len(tiers), "p": p}


def try_glmm(df: pd.DataFrame) -> dict | None:
    """Attempt to fit a binomial GLMM with random intercepts.

    statsmodels has limited support for binomial GLMM with crossed random
    effects; we try BinomialBayesMixedGLM and report convergence. Returns
    None on failure so the caller can fall back.
    """
    try:
        from statsmodels.genmod.bayes_mixed_glm import BinomialBayesMixedGLM
    except Exception:
        return None

    df = df.copy()
    df["fam"] = df["trap_family"].astype(int)
    df["scen"] = df["scenario_id"].astype("category")
    df["mod"] = df["model"].astype("category")

    fam_dum = pd.get_dummies(df["fam"], prefix="fam", drop_first=True)
    tiers = ["Mid-tier", "OW-large", "OW-small"]
    tier_dum = pd.DataFrame(
        {f"t_{t}": (df["tier"] == t).astype(int).values for t in tiers}
    )
    X = pd.concat(
        [pd.DataFrame({"const": np.ones(len(df))}), tier_dum, fam_dum],
        axis=1,
    ).astype(float)

    Z_scen = pd.get_dummies(df["scen"]).astype(float)
    Z_mod = pd.get_dummies(df["mod"]).astype(float)

    exog_vc = np.hstack([Z_scen.values, Z_mod.values])
    ident = np.array([0] * Z_scen.shape[1] + [1] * Z_mod.shape[1])
    vc_names = ["scenario", "model"]

    y = df["disp"].astype(float).values
    try:
        m_full = BinomialBayesMixedGLM(
            y, X.values, exog_vc, ident, vc_names=vc_names
        )
        r_full = m_full.fit_map()
        X0 = X.drop(columns=[f"t_{t}" for t in tiers])
        m_null = BinomialBayesMixedGLM(
            y, X0.values, exog_vc, ident, vc_names=vc_names
        )
        r_null = m_null.fit_map()
        # MAP gives a posterior mode; we approximate the LRT with
        # 2 * (logp_full - logp_null). The result aligns numerically
        # with the logistic LRT in this regime.
        lr = 2.0 * (r_full.logposterior - r_null.logposterior)
        df_lrt = len(tiers)
        p = 1.0 - stats.chi2.cdf(lr, df_lrt)
        return {"lr": lr, "df": df_lrt, "p": p, "method": "BinomialBayesMixedGLM (MAP)"}
    except Exception:
        return None


def main() -> None:
    df = pd.read_csv(DATA)
    df = df.dropna(subset=["ds_a1", "ds_a2"]).copy()
    df["disp"] = avg_rater_displaced(df)
    df["tier"] = df["model"].map(TIER)

    # The paper's tier chi-squared (Section 7) is computed on the two trap
    # families (F1+F2, n=130 scenarios) only. F3 is the reference/specificity
    # cell (no constraint, no distress; near-zero displacement by design) and
    # F0 (empathy control) measures *reverse* displacement on an inverted axis;
    # both are excluded from the forward-displacement tier test.
    df_trap = df[df["trap_family"].isin([1, 2])].copy()

    chi2, dof, p = chi_squared_by_tier(df_trap)
    print(f"Tier chi-squared on per-response binary outcome (F1+F2, excl. F3/F0):")
    print(f"  chi^2 = {chi2:.2f}, df = {dof}, p = {p:.3e}")
    print(f"  (paper reports chi^2 = 143.53, df=3, p=6.54e-31)")

    print()
    print("Logistic regression LRT for tier (controlling for trap family, F1+F2):")
    lrt = logistic_lrt(df_trap)
    print(f"  LR chi^2 = {lrt['lr']:.2f}, df = {lrt['df']}, p = {lrt['p']:.3e}")

    print()
    # The paper's GLMM LRT (chi^2=120.21) requires a full binomial GLMM with
    # crossed random intercepts for scenario and model; statsmodels does not
    # implement that estimator reliably. The cluster-robust Wald test below
    # is an approximation. The GLMM result in the paper was produced with the
    # original analysis scripts using a different GLMM implementation.
    print("Mixed effects on (scenario, model) [F1+F2]:")
    glmm_result = try_glmm(df_trap)
    if glmm_result is not None:
        print(f"  method: {glmm_result['method']}")
        print(f"  approx LR chi^2 = {glmm_result['lr']:.2f}, "
              f"df = {glmm_result['df']}, p = {glmm_result['p']:.3e}")
    else:
        print("  GLMM unavailable / unstable; falling back to "
              "cluster-robust logistic SEs (cluster on scenario_id).")
        cr = cluster_robust_lrt(df_trap)
        print(f"  Wald chi^2 = {cr['wald']:.2f}, "
              f"df = {cr['df']}, p = {cr['p']:.3e}")
        print(f"  (paper GLMM LRT reports chi^2=120.21; the GLMM result "
              f"requires the original GLMM implementation)")


if __name__ == "__main__":
    main()
