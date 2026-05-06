"""Tier chi-squared and GLMM-LRT (reproduces Section 6 / Discussion result).

Reproduces the three statistics reported in the main paper:

  (1) Pearson chi-squared by tier on the per-response binary outcome
      (F1+F2 trap subset).
  (2) Logistic GLMM with a scenario random intercept, fit by Laplace
      approximation; LRT for tier controlling for trap family.
      (Paper Eq. N.6.)
  (3) Cluster-robust logistic-regression Wald test as a cross-check
      (sandwich variance, clustered on scenario_id).

The GLMM is implemented directly here (penalized IRLS for the random
effect, L-BFGS-B over the fixed effects + log-variance) because
statsmodels' BinomialBayesMixedGLM is variational and does not yield a
proper LRT, and pymer4/lme4 are not assumed to be installed.
"""

from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from scipy.optimize import minimize
from scipy.special import expit

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _paths import DATA  # noqa: E402
from headline_table import TIER, avg_rater_displaced  # noqa: E402

warnings.filterwarnings("ignore")


# ---------------------------------------------------------------------------
# (1) Pearson chi-squared
# ---------------------------------------------------------------------------

def chi_squared_by_tier(df: pd.DataFrame) -> tuple[float, int, float]:
    tab = pd.crosstab(df["tier"], df["disp"].astype(int))
    chi2, p, dof, _ = stats.chi2_contingency(tab.values)
    return chi2, dof, p


# ---------------------------------------------------------------------------
# (2) Binomial GLMM with scenario random intercept, Laplace LRT
# ---------------------------------------------------------------------------

def _laplace_marglik(theta, X, y, scen_codes, S):
    """Laplace-approximate marginal log-likelihood of a binomial GLMM
    with a single scalar random intercept per scenario.

    theta = [beta..., log_sigma].
    """
    p = X.shape[1]
    beta = theta[:p]
    sig2 = np.exp(2.0 * theta[p])

    Xb = X @ beta
    u = np.zeros(S)

    # Penalized IRLS for u given beta, sigma
    for _ in range(80):
        eta = Xb + u[scen_codes]
        pp = expit(eta)
        g = np.bincount(scen_codes, weights=(y - pp), minlength=S) - u / sig2
        H = np.bincount(scen_codes, weights=pp * (1.0 - pp), minlength=S) + 1.0 / sig2
        du = g / H
        u = u + du
        if np.max(np.abs(du)) < 1e-9:
            break

    eta = Xb + u[scen_codes]
    log_p = -np.logaddexp(0.0, -eta)
    log_1mp = -np.logaddexp(0.0, eta)
    ll = float(np.sum(y * log_p + (1.0 - y) * log_1mp))

    log_pri = -0.5 * float(np.sum(u * u)) / sig2 - 0.5 * S * np.log(2.0 * np.pi * sig2)
    pp = expit(eta)
    H = np.bincount(scen_codes, weights=pp * (1.0 - pp), minlength=S) + 1.0 / sig2
    laplace_corr = -0.5 * float(np.sum(np.log(H))) + 0.5 * S * np.log(2.0 * np.pi)
    return ll + log_pri + laplace_corr


def _fit_glmm(X, y, scen_codes, S):
    """Fit binomial GLMM with scenario RE; return (loglik, sigma, success)."""
    import statsmodels.api as sm

    glm = sm.GLM(y, X, family=sm.families.Binomial()).fit(disp=0)
    theta0 = np.concatenate([np.asarray(glm.params), [0.0]])
    res = minimize(
        lambda th: -_laplace_marglik(th, X, y, scen_codes, S),
        theta0, method="L-BFGS-B", options={"maxiter": 2000},
    )
    sigma = float(np.exp(res.x[-1]))
    return -float(res.fun), sigma, bool(res.success)


def glmm_lrt_tier(df: pd.DataFrame) -> dict:
    """LRT for tier in a binomial GLMM with scenario RE, controlling for fam."""
    from patsy import dmatrices

    df = df.copy()
    df["fam"] = df["trap_family"].astype("category")
    df["tier_c"] = pd.Categorical(
        df["tier"], categories=["Frontier", "Mid-tier", "OW-large", "OW-small"]
    )

    scen_codes, scen_uniq = pd.factorize(df["scenario_id"])
    S = len(scen_uniq)
    y = df["disp"].astype(float).values

    X_full = dmatrices("disp ~ C(tier_c) + C(fam)", data=df, return_type="dataframe")[1].values
    X_null = dmatrices("disp ~ C(fam)", data=df, return_type="dataframe")[1].values

    ll_f, sig_f, ok_f = _fit_glmm(X_full, y, scen_codes, S)
    ll_n, sig_n, ok_n = _fit_glmm(X_null, y, scen_codes, S)
    lr = 2.0 * (ll_f - ll_n)
    df_lrt = X_full.shape[1] - X_null.shape[1]
    p = 1.0 - stats.chi2.cdf(lr, df_lrt)
    return {"lr": lr, "df": df_lrt, "p": p,
            "sigma_full": sig_f, "sigma_null": sig_n,
            "converged": ok_f and ok_n}


def glmm_lrt_modelfam(df: pd.DataFrame) -> dict:
    """LRT for model x family interaction in a binomial GLMM with scenario RE.

    Run on F0+F1+F2 (excludes F3 specificity check).
    """
    from patsy import dmatrices

    df = df.copy()
    df["fam"] = df["trap_family"].astype("category")
    df["mod"] = df["model"].astype("category")

    scen_codes, scen_uniq = pd.factorize(df["scenario_id"])
    S = len(scen_uniq)
    y = df["disp"].astype(float).values

    X_full = dmatrices("disp ~ C(mod) * C(fam)", data=df, return_type="dataframe")[1].values
    X_null = dmatrices("disp ~ C(mod) + C(fam)", data=df, return_type="dataframe")[1].values

    ll_f, sig_f, ok_f = _fit_glmm(X_full, y, scen_codes, S)
    ll_n, sig_n, ok_n = _fit_glmm(X_null, y, scen_codes, S)
    lr = 2.0 * (ll_f - ll_n)
    df_lrt = X_full.shape[1] - X_null.shape[1]
    p = 1.0 - stats.chi2.cdf(lr, df_lrt)
    return {"lr": lr, "df": df_lrt, "p": p, "converged": ok_f and ok_n}


# ---------------------------------------------------------------------------
# (3) Cluster-robust Wald (cross-check)
# ---------------------------------------------------------------------------

def cluster_robust_wald(df: pd.DataFrame) -> dict:
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


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------

def main() -> None:
    df = pd.read_csv(DATA)
    df = df.dropna(subset=["ds_a1", "ds_a2"]).copy()
    df["disp"] = avg_rater_displaced(df)
    df["tier"] = df["model"].map(TIER)

    # Trap subset (F1+F2): used for the headline tier statistics.
    df_trap = df[df["trap_family"].isin([1, 2])].copy()

    chi2, dof, p = chi_squared_by_tier(df_trap)
    print("Tier chi-squared on per-response binary outcome (F1+F2, excl. F3/F0):")
    print(f"  chi^2 = {chi2:.2f}, df = {dof}, p = {p:.3e}")
    print(f"  (paper reports chi^2 = 143.53, p < 1e-30)")

    print()
    print("GLMM LRT for tier (binomial, scenario random intercept, controlling for fam):")
    g = glmm_lrt_tier(df_trap)
    print(f"  LR chi^2 = {g['lr']:.2f}, df = {g['df']}, p = {g['p']:.3e}")
    print(f"  fitted sigma_S = {g['sigma_full']:.3f} (full), {g['sigma_null']:.3f} (null)")
    print(f"  converged: {g['converged']}")
    print(f"  (paper reports chi^2 = 154.29, p < 1e-32)")

    print()
    print("Cluster-robust Wald (cross-check, sandwich on scenario_id):")
    cr = cluster_robust_wald(df_trap)
    print(f"  Wald chi^2 = {cr['wald']:.2f}, df = {cr['df']}, p = {cr['p']:.3e}")

    print()
    df_mfx = df[df["trap_family"].isin([0, 1, 2])].copy()
    print(f"GLMM LRT for model x family interaction (F0+F1+F2, n={len(df_mfx)}):")
    gi = glmm_lrt_modelfam(df_mfx)
    print(f"  LR chi^2 = {gi['lr']:.2f}, df = {gi['df']}, p = {gi['p']:.3e}")
    print(f"  converged: {gi['converged']}")
    print(f"  (paper reports chi^2 = 230.60, df = 34, p < 1e-30)")


if __name__ == "__main__":
    main()
