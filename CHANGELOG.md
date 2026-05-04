# Changelog

All notable changes to GDB are recorded here. Versioning follows
SemVer-with-an-anonymous-suffix during the review phase; numeric
versions will be assigned at camera-ready.

## [1.0.0-anonymous] — 2026-05-03

Initial submission bundle for NeurIPS 2026 Datasets & Benchmarks Track.

### Included
- 230 author-constructed scenarios across 9 domains and 4 taxonomy
  cells (F0=35, F1=65, F2=65, F3=65).
- 4,140 model response rows across 18 models at temperature 0.7
  (single-turn, no system prompt); 4,134 are non-null (6 failed
  generation and are retained as null rows — see Known Issues).
- 8,268 author annotations (A1, A2) on the 3-dimensional ordinal rubric
  (Goal Fidelity, Feasibility Acknowledgment, Displacement Severity).
- 191-item external rater subset (R1, R2) for rubric portability.
- Post-training stage probe (`probe1_post_training/`): 7 checkpoints
  spanning OLMo-2 / Qwen-2.5 / Mistral 7B base / SFT / DPO / instruct
  variants, dual-judged by GPT-4.1 and Kimi-K2.
- 2x2 discriminant probe (`discriminant_2x2/`): 8 models on a 40-scenario
  factorial of task complexity × social pressure.
- Six reproducibility scripts (`code/`) that recompute every headline
  number from the checked-in data.
- Datasheet (Gebru et al. 2021 schema), Croissant 1.0 metadata with
  Responsible AI fields, rubric anchors, and rater guidelines.

### Documentation
- README with intended uses, out-of-scope uses, limitations, known
  failure modes, bias and mitigation, compute disclosure, and author
  responsibility statement.
- DATASHEET with full motivation, composition, collection, processing,
  uses, distribution, and maintenance sections.

### Known issues
- 6 of 4,140 (scenario, model) pairs have no response (refusals or API
  errors), all in the F0 empathy cell for `gpt-4o` and `ollama:mistral`.
  These rows are present in `unified_dataset.csv` with NaN scores.
- Three frontier models (`deepseek-reasoner`, `claude-haiku-4.5`,
  `gpt-5.4-mini-2026-03-17`) lack public Chatbot Arena Elo at submission
  time; they are excluded from the Arena correlation analysis (n=15).
- The post-training probe omits a Mistral 7B v0.1 base checkpoint that
  was tried during pilot but excluded from the final analysis.
