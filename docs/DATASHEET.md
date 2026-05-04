# Datasheet for GDB

> *When Empathy Misses the Goal: A Benchmark for Goal Displacement in LLM Advice.*

Datasheet following Gebru et al. (2021), "Datasheets for Datasets."
Anonymous submission for double-blind review; identifying details about the
research team, institutions, and IRB protocol numbers have been redacted.

---

## 1. Motivation

**1.1 For what purpose was the dataset created?**
GDB was created to measure goal displacement in conversational language
models: the substitution of warm, reassuring, or validating content for
goal-advancing content in scenarios where both are in tension. Existing
sycophancy and helpfulness benchmarks conflate epistemic deference with
functional goal abandonment; GDB was built to dissociate the two.

**1.2 Who created the dataset?**
The research team (anonymized for review). Two of the team members
(referred to here as A1 and A2) annotated the full corpus.

**1.3 Who funded the creation of the dataset?**
Anonymized for review. Funding sources will be disclosed at camera-ready.

**1.4 Any other comments?**
No.

---

## 2. Composition

**2.1 What do the instances represent?**
Three populations of instances:
1. **Scenarios** (n=230): single-turn user prompts paired with a goal
   declaration, optional hard constraints, and a taxonomy cell label.
2. **Responses** (n=4,140 rows; 4,134 non-null): one row per (scenario, model)
   pair for 18 models. The expected total is `230 * 18 = 4,140`. Six pairs
   failed generation (API quota errors) and are retained in the unified
   dataset as null-response rows with NaN scores; they are excluded from all
   analyses. All six null rows are in the F0 empathy cell (scenarios
   F0-CAR-001, F0-CLI-001, F0-FIN-001, F0-REL-001 for `ollama:mistral`;
   F0-CLI-001 and F0-REL-001 for `gpt-4o`).
3. **Annotations** (n=8,268): two raters (A1, A2) scored every non-null
   response on three ordinal dimensions, yielding `4,134 * 2` rater-response
   rows.

**2.2 How many instances are there in total?**
230 scenarios; 4,140 response rows (4,134 non-null, 6 null-response due to
generation failures); 8,268 author annotations on the 4,134 non-null
responses; an additional 191-row stratified subset rated by two external
Prolific raters (R1, R2).

**2.3 Does the dataset contain all possible instances or is it a sample?**
The 230 scenarios are an author-constructed sample, not a population. They
were drafted across 9 principal domains (clinical, financial, career, legal,
relationship, education, technology, housing, parenting), plus a small
"Other" catch-all of 4 scenarios outside these categories, and four family
cells (F1, F2, F3, F0). No claim of statistical representativeness over
real-world conversations is made.

**2.4 What data does each instance consist of?**
- Scenario fields: `id`, `trap_family` (0..3), `domain`, `difficulty`,
  `user_prompt` (the user-facing text), `user_goal` (a one-line goal
  declaration), `hard_constraints` (free text or empty), and short
  justification fields for trap-family and difficulty assignment.
- Response fields: `scenario_id`, `model`, `temperature`, `response`.
- Annotation fields: `scenario_id`, `model`, `rater_id` (A1 or A2),
  `goal_fidelity` (0..3), `feasibility_ack` (0..3 on F1/F2; -1 on F0/F3),
  `displacement_severity` (0..3), and free-text rationale where the rater
  flagged the case for re-discussion.

**2.5 Is there a label or target associated with each instance?**
Yes. The headline binary outcome is `displaced = 1` iff the average of
the two raters' DS scores is `>= 2`. Per-dimension averages are also
released. The unified dataset (`unified_dataset/unified_dataset.csv`)
joins scenario, response, and both rater scores into a single flat file.

**2.6 Is any information missing from individual instances?**
Six (scenario, model) pairs failed generation (API quota errors). These rows
are retained in `unified_dataset.csv` with null response text and NaN score
fields; they are excluded from all displacement analyses. `feasibility_ack`
is intentionally coded as `-1` (N/A) on F0 and F3 because no binding
constraint is present.

**2.7 Are relationships between individual instances made explicit?**
Yes, via `scenario_id` and `model`, which are stable join keys across all
files.

**2.8 Are there recommended data splits?**
The benchmark is evaluation-only; no train/val/test split is provided.
Models should be queried fresh on the full 230-scenario corpus.

**2.9 Are there any errors, sources of noise, or redundancies?**
Inter-rater reliability is reported in `annotations/external_raters/
kappa_results.json`. Quadratic-weighted Cohen's kappa between A1 and A2
on the full 4,134-response corpus: GF=0.908, FA=0.909, DS=0.756.
Binary `DS >= 2` Gwet's AC1 = 0.896. We report AC1 rather than Cohen's
binary kappa for the binary outcome because the two annotators apply
slightly different DS>=2 thresholds (A1 marginal 8.1%, A2 marginal 14.6%);
under that prevalence asymmetry Cohen's binary kappa is depressed by a
known marginal-correction artifact even though percent agreement is high,
and Gwet's AC1 is the recommended prevalence-stable index. Residual
disagreement on the ordinal DS scale reflects the boundary between scores
1 and 2 on borderline cases.

**2.10 Does the dataset rely on external resources?**
The model responses depend on the underlying LLM APIs and weights at the
time of generation. We provide the raw responses so that downstream
analysis is independent of API drift. The benchmark itself is fully
self-contained.

**2.11 Does the dataset contain confidential data?**
No. All scenarios are author-constructed fictional vignettes. None
describe real, identifiable individuals.

**2.12 Could the dataset cause harm if misused?**
A subset of scenarios reference real institutional contexts (e.g., FAA
medical reinstatement standards, US immigration timelines) and contain
plausible-sounding domain content. The dataset is for research use only
and must not be deployed as ground truth for diagnostic, legal, financial,
or clinical decision support. See section 5.

---

## 3. Collection process

**3.1 How was the data acquired?**
- **Scenarios** were author-constructed. Each scenario was drafted by one
  team member and reviewed by at least one other. Scenarios that did not
  pass three pre-collection criteria were rejected: (i) constraint
  verifiability (the binding constraint must be checkable against an
  external source), (ii) displacement-invitingness (the scenario must
  elicit a non-trivial displacement rate from at least one frontier
  model in pilot generation), and (iii) rater-distinguishability (two
  pilot raters had to agree on the intended cell within one ordinal step).
- **Responses** were generated by querying each model's public API at
  `temperature = 0.7`, single-turn, with a fixed task framing and no
  system prompt. Open-weight models were served via Ollama on local
  hardware.
- **Annotations** were produced by A1 and A2 working independently in a
  shared schema, blind to model identity. Calibration was performed on
  10 shared responses prior to the main pass; disagreements were resolved
  by re-annotation against a written rubric, not by adjudication.

**3.2 What mechanisms were used to collect the data?**
Model response generation: Python scripts using the official SDKs for
each provider. Annotation: a custom rater interface that hid model
identity and shuffled response order within each scenario.

**3.3 Over what timeframe was the data collected?**
Scenario authoring: late 2025. Response generation: 2025-2026. Author
annotation: 2026. External rater collection: 2026.

**3.4 Were any ethical review processes conducted?**
The external rater study (191-item subset) was conducted under an
ethics protocol approved by the host institution's research ethics
board (protocol number anonymized for review). Raters were recruited
via Prolific, gave informed consent, and were paid GBP 9 per hour
(above the Prolific minimum at the time). No personally identifying
information was collected beyond the Prolific worker ID, which is not
released.

**3.5 Did individuals consent to use of their data?**
The external raters gave informed consent. The model responses are
generated content from commercial APIs and open-weight checkpoints;
their use is governed by the respective providers' terms of service,
which were reviewed for compatibility with academic redistribution.

---

## 4. Preprocessing, cleaning, labeling

**4.1 Was any preprocessing of the raw data done?**
Minimal. Model responses are released as the raw API outputs, with the
exception of stripping leading/trailing whitespace. The unified dataset
joins scenarios, responses, and both raters' scores; the join is
deterministic on `(scenario_id, model)` and `(scenario_id, model,
rater_id)`.

**4.2 Was the raw data saved in addition to the preprocessed data?**
Yes. Per-rater CSVs in `annotations/per_model_authors/` carry the raw
scores; the unified dataset is a downstream join over those files.

**4.3 Is the software used to preprocess the data available?**
Yes, in `code/`.

---

## 5. Uses

**5.1 Has the dataset been used for any tasks already?**
Yes: for the manuscript that this submission accompanies. Two probes
(`probe1_post_training/`, `discriminant_2x2/`) extend the main benchmark
to study post-training-stage effects and to dissociate displacement from
sycophancy under a complexity x social-pressure factorial.

**5.2 Is there a repository that links to all uses of the dataset?**
Not yet; this is the initial release.

**5.3 What other tasks could the dataset be used for?**
Studying RLHF reward dynamics, calibrating "helpfulness" benchmarks,
auditing fine-tuning interventions, or as a held-out evaluation for
alignment-tuning research.

**5.4 Is there anything about the composition of the dataset that might
impact future uses?**
The benchmark is in English only and US-centric (some scenarios
reference US-specific institutional contexts). Performance estimates
should not be generalized to non-English or non-Western settings without
re-annotation.

**5.5 Are there tasks for which the dataset should not be used?**
- The dataset is **not** a clinical or legal decision-support resource.
  Scenarios that reference medical or legal procedures are
  illustrative, not authoritative.
- Models should **not** be trained on the scenarios or responses without
  disclosing that GDB was in the training mix; doing so will inflate
  apparent benchmark scores.
- The dataset is not designed for measuring general dialogue quality,
  factual accuracy, or open-ended creativity.

---

## 6. Distribution

**6.1 Will the dataset be distributed to third parties?**
Yes. The dataset is released under CC-BY-4.0 (data) and MIT (code).

**6.2 How will the dataset be distributed?**
Via a public mirror at camera-ready (URL withheld for double-blind
review). The present anonymous bundle is the version-1.0.0 snapshot.

**6.3 When will the dataset be distributed?**
At camera-ready, contingent on acceptance. The reviewer-facing version
is this anonymous bundle.

**6.4 Will the dataset be distributed under a copyright or other
intellectual property license?**
CC-BY-4.0 for data, MIT for code. See `LICENSE`.

**6.5 Have any third parties imposed IP-based or other restrictions?**
No. Model responses are derived from commercial-API and open-weight
outputs; their redistribution as evaluation artifacts under CC-BY-4.0
was reviewed against each provider's terms. Specifically:
- **OpenAI** (GPT-4o, GPT-4o-mini, GPT-5.4, GPT-5.4-mini): Usage Policies
  permit publication of API outputs in academic research; outputs are
  not classed as OpenAI IP under the current Terms.
- **Anthropic** (Claude Sonnet 4.6, Claude Haiku 4.5): Usage Policy
  permits redistribution of model outputs for research and evaluation.
- **Google** (Gemini 2.5 Pro, Gemini 2.5 Flash, Gemini 3.1 Pro Preview):
  Gemini API ToS permits use of generated content in research
  publications; outputs are user-owned.
- **DeepSeek** (DeepSeek Chat / V3, DeepSeek Reasoner / R1): API ToS
  reviewed and compatible with academic redistribution.
- **Meta** (Llama 3, Llama 3.1 8B/70B): Llama Community License permits
  research redistribution of outputs with attribution.
- **Alibaba** (Qwen 2.5 32B/72B): Tongyi Qianwen License permits
  research use and output redistribution.
- **Mistral AI** (Mistral 7B): Apache-2.0 / Mistral Research License
  permits research redistribution.
- **NVIDIA** (Nemotron): Open Model License permits research use.

All listed terms are as of access date (early 2026); citation of the
specific policy versions is in the maintenance log of the public mirror.

**6.6 Do any export controls or other regulatory restrictions apply?**
No.

---

## 7. Maintenance

**7.1 Who will be supporting/hosting/maintaining the dataset?**
The research team (anonymized for review). Maintenance contact details
will be added at camera-ready.

**7.2 How can the owner be contacted?**
Via the issue tracker on the public mirror (URL withheld for review).

**7.3 Is there an erratum?**
None at v1.0.0-anonymous. Errata will be tracked in the public mirror's
issue tracker.

**7.4 Will the dataset be updated?**
Yes. Patch versions for scenario errata and additional rater data;
minor versions for additional model evaluations; major versions for
schema changes. The authors commit to a two-year maintenance window
from the date of publication.

**7.5 If the dataset relates to people, are there applicable retention
limits?**
The only person-derived data are the external rater annotations, which
are stored under pseudonymous worker IDs that are not released. The
underlying Prolific worker IDs are retained internally for the duration
of the IRB-mandated retention window and then deleted.

**7.6 Will older versions continue to be supported?**
Yes. Each released version is tagged on the public mirror and remains
downloadable. Headline manuscript numbers correspond to v1.0.0.

**7.7 Is there a mechanism for others to extend the dataset?**
Yes. Pull requests adding new scenarios (with full taxonomy cell
justification) or new model evaluations (with documented generation
parameters) are welcome via the public mirror.
