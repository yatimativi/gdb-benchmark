# GDB: When Empathy Misses the Goal

A Benchmark for Goal Displacement in LLM Advice. GDB measures the tendency of
conversational language models to substitute warmth, reassurance, or
validation for goal-advancing content when both are in tension.

> Anonymous submission for double-blind review.

## TL;DR

GDB evaluates how often an LLM abandons a user's stated decision-making
goal in favor of socially comforting content. The benchmark contains **230
scenarios** across **9 domains** and **4 family cells**, each scored on a
**3-dimensional ordinal rubric** (Goal Fidelity, Feasibility Acknowledgment,
Displacement Severity). Across **18 models** (4,140 generated responses; 4,134
scored — 6 failed generation and are retained as null rows), trap displacement
(`DS >= 2`, averaged-rater consensus, mean of F1 and F2 cells) ranges from
`0.0%` on the strongest frontier models to `37.7%` on the weakest open-weight
8B model, and anti-correlates with Chatbot Arena Elo at Spearman `rho = -0.839`
(`n = 15`).

## Repository contents

```
new_git/
  README.md                  this file
  LICENSE                    CC-BY-4.0 (data) + MIT (code)
  CITATION.cff               citation metadata
  requirements.txt           Python dependencies for code/
  scenarios/                 230 scenarios as JSON and per-family JSONL
  responses/                 4,134 model responses across 18 models
  annotations/               two author raters (full corpus) + external raters
  unified_dataset/           4,140-row joined CSV/JSONL (responses + scores; 6 null-response rows)
  rubric/                    rubric anchors and rater-facing guidelines
  probe1_post_training/      OLMo-2 / Qwen 2.5 / Mistral 7B probe of post-training stages
  discriminant_2x2/          factorial probe (complexity x social pressure)
  docs/                      Croissant 1.0 metadata, DATASHEET, and supporting docs
  code/                      analysis scripts (separate agent)
```

## Quick start

### Option A — Docker (recommended; fully isolated)

```bash
docker build -t gdb .
docker run --rm gdb          # runs all six analysis scripts
```

### Option B — Conda

```bash
conda env create -f environment.yml
conda activate gdb
python code/headline_table.py
```

### Option C — pip (standard)

```bash
# Exact pinned versions (strict reproducibility):
pip install -r requirements_locked.txt

# Or minimum versions (flexible):
pip install -r requirements.txt

python code/headline_table.py
```

**No GPU and no API keys are needed to reproduce the analysis results.**
All six scripts read only the checked-in CSV/JSONL files.

### Reproduce all paper results

Run each script from the repository root (the directory containing this README):

```bash
python code/headline_table.py      # Table 4: per-model displacement by family
python code/reliability.py         # Table 3: IRR statistics
python code/tier_test.py           # Section 7: tier χ² = 143.53 and GLMM LRT
python code/arena_correlation.py   # Figure 2: Arena Elo correlation (ρ = -0.839)
python code/discriminant_2x2.py    # Section 7.1 / Appendix O: 2×2 probe
python code/probe1_stages.py       # Section 7.2 / Appendix P: post-training stages
```

All scripts print to stdout only; no files are written. Expected run time:
under 5 minutes total on a standard laptop.

| Paper artifact | Script | Key output |
|---|---|---|
| Table 4: per-model displacement by family | `code/headline_table.py` | Trap range 0.0–37.7% |
| Table 3: reliability statistics | `code/reliability.py` | AC1 = 0.896 |
| Section 7: tier chi-squared and GLMM LRT | `code/tier_test.py` | χ² = 143.53 |
| Figure 2: Arena Elo correlation | `code/arena_correlation.py` | ρ ≈ −0.80 |
| Section 7.1: 2×2 dissociation probe | `code/discriminant_2x2.py` | 4-cell table |
| Section 7.2: post-training stage decomposition | `code/probe1_stages.py` | 7-checkpoint table |

See `code/README.md` for notes on which results reproduce exactly and which
are approximations (Arena Elo, GLMM).

### Evaluating a new model

To score a new model against all 230 GDB scenarios:

```bash
# Test the pipeline without any API key (mock mode):
python code/generate_responses.py --mock --model my-new-model

# Evaluate a real model (set the appropriate API key first):
export OPENAI_API_KEY=sk-...
python code/generate_responses.py --model gpt-4o-turbo --provider openai

# Then run the standard analysis:
python code/headline_table.py
```

Supported providers: `openai`, `anthropic`, `google`, `deepseek`, `ollama`
(local). See `code/generate_responses.py --help` for all options.

## The taxonomy

Three trap families plus a control cell, factored from `{constraint, distress}`:

| Cell | Constraint | Distress | Role        | n  | What it tests                                                          |
|------|------------|----------|-------------|----|------------------------------------------------------------------------|
| F1   | yes        | no       | trap        | 65 | Feasibility override: model validates an infeasible goal              |
| F2   | yes        | yes      | trap        | 65 | Mixed trap: model addresses only the emotional layer                   |
| F3   | no         | no       | reference   | 65 | Specificity check: no triggers, near-zero displacement expected        |
| F0   | no         | yes      | empathy     | 35 | Empathy condition: empathy IS the goal; reverse displacement scored    |

`Trap displacement` is the mean of F1 and F2 rates (n=130). F3 is the
reference cell (a specificity check). F0 inverts the rubric: unsolicited
problem-solving where empathy was the goal counts as reverse displacement.

## The 3-dimensional rubric

Each response is scored on three ordinal dimensions, 0 to 3:

- **GF (Goal Fidelity)**: how completely the response advances the user's
  stated goal.
- **FA (Feasibility Acknowledgment)**: whether the response acknowledges the
  binding constraint (scored only on F1 and F2; coded as N/A elsewhere).
- **DS (Displacement Severity)**: how much warmth/validation displaces
  goal-advancing content.

The headline binary outcome is `DS >= 2` after averaging the two author
scores. Full anchors are in `rubric/rubric.md`.

## Models evaluated

All 18 models were queried at `temperature = 0.7`, single-turn, with no system
prompt beyond a brief task framing. Grouped by tier:

**Frontier (7)**
- `gemini-2.5-pro`
- `gemini-3.1-pro-preview`
- `gpt-5.4`
- `claude-sonnet-4.6`
- `deepseek-chat` (V3)
- `deepseek-reasoner` (R1)
- `gpt-4o`

**Mid-tier (4)**
- `gemini-2.5-flash`
- `gpt-5.4-mini-2026-03-17`
- `claude-haiku-4.5`
- `gpt-4o-mini`

**Open-weight, large (4)**
- `ollama_llama3-1_70b`
- `ollama_qwen2-5_32b`
- `ollama_qwen2-5_72b`
- `ollama_nemotron`

**Open-weight, small (3)**
- `ollama_mistral`
- `ollama_llama3`
- `ollama_llama3-1_8b`

## Reproducibility

All headline numbers in the manuscript reproduce from this repository alone;
no external API calls are required for the analysis pipeline (response
generation is upstream and its outputs are checked in). See `code/README.md`
for the script-level mapping between manuscript tables/figures and the
scripts that produce them.

## Key companion documents

| Document | Path |
|---|---|
| Datasheet for Datasets (Gebru et al.) | [`docs/DATASHEET.md`](docs/DATASHEET.md) |
| Croissant 1.0 metadata (incl. Responsible AI fields) | [`docs/croissant.json`](docs/croissant.json) |
| Rubric anchors | [`rubric/rubric.md`](rubric/rubric.md) |
| Rater guidelines | [`rubric/annotation_guidelines.md`](rubric/annotation_guidelines.md) |
| Reproducibility scripts | [`code/README.md`](code/README.md) |

## Intended and out-of-scope uses

GDB is intended for:

- Benchmarking and comparing LLMs on goal fidelity in advisory contexts.
- Studying the relationship between RLHF / post-training stages and goal
  displacement (the post-training probe in `probe1_post_training/`
  decomposes Base → SFT → DPO checkpoints).
- Methods research on rubric-based ordinal evaluation of generative model
  output, and on dissociating displacement from social sycophancy
  (the 2x2 probe in `discriminant_2x2/`).

GDB is **not** intended for:

- Clinical, legal, financial, or diagnostic decision support. Scenarios
  referencing medical, legal, or financial procedures are illustrative
  fictional vignettes, not authoritative ground truth.
- Training models on GDB scenarios or responses without disclosure.
  Including GDB in pre-training or fine-tuning data would invalidate
  future benchmark scores.
- Generalizing performance estimates to non-English or non-Western
  settings without re-annotation. All scenarios are English-language and
  reference US institutional contexts.

## Limitations

- **Language and geography**: All 230 scenarios are in English and
  reference US institutional contexts. Cross-lingual and cross-cultural
  validity is untested.
- **Single-turn**: Scenarios are evaluated single-turn. Multi-turn
  displacement dynamics are not captured.
- **No train/val split**: GDB is an evaluation-only benchmark. The corpus
  is small enough that contamination from pre-training is a real risk for
  closed-weight models; users should treat scores on potentially
  contaminated systems as upper bounds.
- **Judge dependence in probes**: The headline 18-model rates rely on
  human annotation, but the post-training and 2x2 probes use GPT-4.1 and
  Kimi-K2 as LLM judges. Judge drift may affect those probes' numerical
  reproducibility if the judge models are updated.
- **Rater pool**: Headline scores come from two trained author
  annotators. External rater portability (`annotations/external_raters/`)
  is reported on a 191-item subset, not the full corpus.

### Known benchmark failure modes

- **Ceiling effects on frontier models**: Gemini 2.5 Pro, GPT-5.4, and
  DeepSeek Chat all score 0.0% trap displacement. The benchmark cannot
  discriminate among the top tier; F1 and F2 cells saturate at the
  current frontier.
- **Floor confounds on small open-weight models**: For 7B–8B open-weight
  models, `DS >= 2` on F3 (specificity-check, no triggers) sometimes
  reflects general instruction-following failure rather than the
  warmth-for-substance substitution GDB targets. Manual inspection of
  F3 hits on small models is recommended before drawing displacement
  conclusions.
- **Single-seed point estimates**: Each (scenario, model) pair was
  generated once at temperature 0.7. We did not measure across-seed
  variance; reported per-model rates are point estimates.
- **Prompt-template sensitivity**: All scenarios use a uniform single-turn
  framing. Robustness to system-prompt or persona variation is untested.

## Bias and mitigation

NeurIPS 2026 D&B requires explicit treatment of demographic, linguistic,
and structural biases in the benchmark. We document the known biases of
GDB below and the mitigations (or honest acknowledgements where mitigation
is not possible).

**Linguistic bias.** All 230 scenarios are English-language. Performance
estimates do not generalize to non-English models, multilingual reasoning,
or code-switching contexts. *Mitigation*: We report this prominently in
the README, DATASHEET (§2.5.4), and Croissant `cr:dataBiases` field.
Translation extensions are out of scope for v1 and would require
re-annotation rather than machine translation.

**Cultural / institutional bias.** Scenarios reference US institutions
and procedures (FAA timelines, US immigration, US healthcare and legal
practice, US college admissions). What counts as "feasibility-blocking"
is partially culturally indexed. *Mitigation*: We do not claim
generalization beyond US-context English advice. Future work could
construct parallel scenarios for other locales.

**Demographic representation in scenarios.** Scenarios deliberately
omit named demographic characteristics: no character names, ages,
genders, races, or socioeconomic markers appear in any scenario prompt.
This was a design choice to minimize demographic confounds in
displacement scoring. *Consequence*: GDB cannot be used to measure
**differential displacement** across user-demographic groups, which is
a meaningful gap. *Conversely*, no demographic group is disproportionately
embedded in adversarial, stigmatizing, or low-status framings.

**Domain bias.** The 9 domains (clinical, financial, career, legal,
parenting, relationships, technical, housing, transportation) were
selected for being displacement-prone advice contexts, not for being
representative of all advice scenarios. F1/F2 trap construction
intentionally over-samples high-stakes constraint conflicts.
*Mitigation*: We report per-domain breakdowns in `code/headline_table.py`
output and document domain selection rationale in `docs/SCENARIO_DESIGN.md`.

**Rater bias.** A1 and A2 are two trained author annotators. On the
binary `DS >= 2` outcome, A1's marginal positive rate (8.1%) is lower
than A2's (14.6%) — a 6.5-pp gap reflecting genuine disagreement on the
1-vs-2 threshold for borderline cases. *Mitigation*: Headline rates use
the averaged-rater consensus (`avg(ds_a1, ds_a2) >= 2`), reducing
single-rater drift. We report Gwet's AC1 (0.896) rather than Cohen's
binary kappa as the prevalence-stable headline statistic, and external
rater portability (κ = 0.766–0.824 vs authors) is reported on a 191-item
stratified subset to bound author-pair idiosyncrasy.

**Model selection bias.** The 18 models reflect availability and access
at submission time (early 2026). Newer or non-English-aligned systems
are not represented; the open-weight tier skews toward Llama, Qwen, and
Mistral families served via Ollama. *Mitigation*: We document the
selection in the Models section of this README and in DATASHEET §2.4;
the evaluation pipeline accepts new models via the standard JSONL
response format (see `code/README.md`).

**LLM-as-judge bias (probe studies only).** The post-training and 2x2
probe analyses use GPT-4.1 and Kimi-K2 as judges. Both models may favor
their own training distribution or share systematic blind spots.
*Mitigation*: We use two judges from different providers (OpenAI and
Moonshot) and average their scores; we report inter-judge agreement
(pooled AC1 = 0.718). The headline 18-model rates do **not** depend on
LLM judges — they use human annotation only.

**Construct-validity caveat.** "Goal displacement" as defined here
operationalizes one specific failure mode (warmth/validation crowding
out substance). It is not a measure of overall helpfulness, factual
accuracy, harm-avoidance, or sycophancy. The 2x2 discriminant probe
(Appendix O) provides empirical evidence that displacement dissociates
from sycophancy in the L-pressure cells, but the construct should not
be over-extended.

## Compute and resource use

Generating the 4,134 model responses required approximately 4,140 API or
local-inference calls across 18 models at temperature 0.7. Closed-weight
generation (OpenAI, Anthropic, Google, DeepSeek APIs) was the dominant
cost; open-weight models (Llama, Qwen, Mistral, Nemotron) ran locally on
a single workstation via Ollama. We did not instrument inference energy
use. The LLM-judge passes for the probe studies (GPT-4.1 + Kimi-K2 over
the OLMo / Qwen / Mistral checkpoints and the 2x2 cells) added
approximately 3,800 API calls.

**Reproducing the analysis pipeline from the checked-in data requires no
API calls and no GPU.** All six scripts in `code/` complete in under five
minutes total on a standard laptop and depend only on `pandas`, `numpy`,
`scipy`, `scikit-learn`, `statsmodels`, and `matplotlib`.

## Author responsibility statement

The authors confirm that:

- All model API outputs were generated under provider terms of service
  that permit redistribution as evaluation artifacts for academic
  research (OpenAI, Anthropic, Google, DeepSeek, and Meta Llama
  licenses were each reviewed for compatibility with CC-BY-4.0
  redistribution; see `docs/DATASHEET.md` §6.5).
- No personally identifying information is released. Pseudonymous
  Prolific worker identifiers used for the external rater study are
  retained internally for compensation auditing only and are not
  included in the public release.
- The external rater study was conducted under an approved
  institutional ethics protocol with informed consent and above-minimum
  compensation.
- The CC-BY-4.0 license applies to the original dataset content
  (scenarios, rubric, annotations, derived analyses). The dataset does
  not incorporate copyrighted third-party text.

## Ethics and responsible use

Scenarios are author-constructed fictional vignettes; no real individuals
are described. The external rater study (n=191) was conducted under an
institutional ethics protocol; raters gave informed consent and were
compensated above Prolific's recommended minimum rate. No personally
identifying information is released with the dataset; Prolific worker
identifiers are not included. Full collection, annotation, and consent
details are in [`docs/DATASHEET.md`](docs/DATASHEET.md) §3.

The benchmark surfaces displacement behavior that may correlate with
post-training pipelines (RLHF, DPO). Results should be reported in the
spirit of constructive evaluation, not vendor comparison; tier-level
patterns are more robust than per-model deltas, especially for models
without published Elo or with small open-weight sample sizes.

## License

- **Data** (scenarios, responses, annotations): Creative Commons Attribution
  4.0 International (CC-BY-4.0). You may share and adapt with attribution.
- **Code** (`code/` and any scripts shipped in this repo): MIT.

Full text in `LICENSE`.

## How to cite

```bibtex
@article{anonymous2026gdb,
  title   = {When Empathy Misses the Goal: A Benchmark for Goal Displacement in LLM Advice},
  author  = {[anonymous]},
  journal = {[anonymous; under review]},
  year    = {2026},
  note    = {Anonymous submission; bibtex will be populated at camera-ready}
}
```

## Maintenance

The dataset is versioned via the public mirror; the present anonymous bundle
corresponds to version `1.0.0-anonymous`. The authors commit to a two-year
maintenance window from the date of publication: bug fixes, scenario
errata, and additional rater data will be released as patch versions.
Issues, errata, and pull requests are welcome via the issue tracker on the
public mirror (URL withheld for double-blind review and populated at
camera-ready).
